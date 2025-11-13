#!/usr/bin/env python3
"""
Dual Pipeline Event Processing
Process events from AEDAT4 file through two pipelines:
1. Time-based: Generate frames at fixed FPS intervals
2. Event-based: Generate frames after accumulating N events
Save frames as JPEG images in separate folders
"""

import argparse
import cv2
import os
import numpy as np
import time

# Try to import dv library for reading AEDAT4
try:
    import dv as dv_old
    DV_OLD_AVAILABLE = True
except ImportError:
    DV_OLD_AVAILABLE = False

from utils.frame_generator import FrameGenerator
from utils.event_based_generator import EventBasedFrameGenerator


# Configuration
FILE_PATH = './data/dvSave-2025_11_12_20_21_55.aedat4'
FPS = 30
EVENTS_PER_FRAME = 10000
OUTPUT_DIR = './output/'
JPEG_QUALITY = 85
SHUTTER_TYPE = 'boxcar'
BOXCAR_PERIOD = 0.1
BOXCAR_DUTY = 0.25
BRIGHTNESS = 3.0
DECAY_RATE = 0.0


def save_frame_jpeg(frame, output_path, quality=85):
    """
    Save frame as JPEG image
    
    Args:
        frame: Frame as numpy array (H, W, 3) uint8
        output_path: Path to save JPEG file
        quality: JPEG quality (1-100)
    
    Returns:
        True if successful, False otherwise
    """
    if frame is None:
        return False
    
    # Ensure frame is uint8
    if frame.dtype != np.uint8:
        frame = frame.astype(np.uint8)
    
    # Create output directory if needed
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save as JPEG with quality parameter
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    success = cv2.imwrite(output_path, frame, encode_params)
    
    return success


def format_frame_number(frame_num, padding=4):
    """Format frame number with zero-padding"""
    return f"frame_{frame_num:0{padding}d}.jpg"


def process_dual_pipeline(file_path, output_dir, fps=30, events_per_frame=10000,
                          shutter_type='boxcar', period=0.1, duty=0.25,
                          brightness=3.0, decay_rate=0.5, jpeg_quality=85):
    """
    Process events through both time-based and event-based pipelines
    
    Args:
        file_path: Path to input AEDAT4 file
        output_dir: Base output directory
        fps: Frames per second for time-based pipeline
        events_per_frame: Events per frame for event-based pipeline
        shutter_type: Shutter function type
        period: Period for boxcar shutter
        duty: Duty cycle for boxcar shutter
        brightness: Brightness multiplier
        decay_rate: Frame persistence decay
        jpeg_quality: JPEG compression quality (1-100)
    """
    if not DV_OLD_AVAILABLE:
        print("Error: dv library not available. Install it with: pip install dv")
        return False
    
    # Create output directories
    time_based_dir = os.path.join(output_dir, 'time_based')
    event_based_dir = os.path.join(output_dir, 'event_based')
    
    os.makedirs(time_based_dir, exist_ok=True)
    os.makedirs(event_based_dir, exist_ok=True)
    
    print(f"Reading events from: {file_path}")
    
    try:
        with dv_old.AedatFile(file_path) as f:
            events = np.hstack([packet for packet in f['events'].numpy()])
            
            print(f"Total events in file: {len(events)}")
            
            if len(events) == 0:
                print("No events found in file")
                return False
            
            # Get resolution from events
            x_max = events['x'].max()
            y_max = events['y'].max()
            width = int(x_max) + 1
            height = int(y_max) + 1
            
            print(f"Detected resolution: {width}x{height}")
            
            # Extract event arrays
            timestamps = events['timestamp']
            x_coords = events['x']
            y_coords = events['y']
            polarities = events['polarity']
            
            # Initialize frame generators
            frame_gen_time = FrameGenerator(
                width=width,
                height=height,
                fps=fps,
                shutter_type=shutter_type,
                period=period,
                duty=duty,
                brightness=brightness,
                decay_rate=decay_rate
            )
            
            frame_gen_event = EventBasedFrameGenerator(
                width=width,
                height=height,
                events_per_frame=events_per_frame,
                shutter_type=shutter_type,
                period=period,
                duty=duty,
                brightness=brightness,
                decay_rate=decay_rate
            )
            
            # Processing state
            frame_interval = 1.0 / fps
            t0 = timestamps[0]
            last_frame_time_s = 0.0
            
            time_frame_counter = 0
            event_frame_counter = 0
            
            total_events = len(events)
            
            print("\nProcessing events through dual pipelines...")
            print("=" * 60)
            
            start_time = time.time()
            
            # Process events in batches
            batch_size = 1000  # Process events in batches for efficiency
            i = 0
            
            while i < total_events:
                # Determine batch end
                batch_end = min(i + batch_size, total_events)
                
                # Get batch of events
                batch_ts = timestamps[i:batch_end]
                batch_x = x_coords[i:batch_end]
                batch_y = y_coords[i:batch_end]
                batch_pol = polarities[i:batch_end]
                
                # Convert timestamps to seconds
                batch_ts_s = (batch_ts - t0) * 1e-6
                
                # Add events to time-based generator
                frame_gen_time.add_events(batch_ts, batch_x, batch_y, batch_pol)
                
                # Check if it's time to generate a time-based frame
                current_time_s = batch_ts_s[-1] if len(batch_ts_s) > 0 else last_frame_time_s
                time_frame_end_s = last_frame_time_s + frame_interval
                
                if current_time_s >= time_frame_end_s:
                    frame = frame_gen_time.get_frame()
                    time_frame_counter += 1
                    frame_path = os.path.join(time_based_dir, format_frame_number(time_frame_counter))
                    save_frame_jpeg(frame, frame_path, jpeg_quality)
                    
                    frame_gen_time.reset_frame()
                    last_frame_time_s = time_frame_end_s
                
                # Add events to event-based generator
                events_added, should_generate = frame_gen_event.add_events(
                    batch_ts, batch_x, batch_y, batch_pol
                )
                
                # Check if we should generate an event-based frame
                if should_generate:
                    frame = frame_gen_event.get_frame()
                    event_frame_counter += 1
                    frame_path = os.path.join(event_based_dir, format_frame_number(event_frame_counter))
                    save_frame_jpeg(frame, frame_path, jpeg_quality)
                    
                    frame_gen_event.reset_frame()
                
                # Advance to next batch
                i = batch_end
                
                # Progress report
                if i % 100000 == 0 or i == total_events:
                    progress = (i / total_events) * 100
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    print(f"Progress: {progress:.1f}% ({i}/{total_events} events, {rate:.0f} events/sec) | "
                          f"Time-based: {time_frame_counter} frames, Event-based: {event_frame_counter} frames")
            
            # Generate final frames if there are remaining events
            if frame_gen_time.get_event_count() > 0:
                frame = frame_gen_time.get_frame()
                time_frame_counter += 1
                frame_path = os.path.join(time_based_dir, format_frame_number(time_frame_counter))
                save_frame_jpeg(frame, frame_path, jpeg_quality)
            
            if frame_gen_event.get_event_count() > 0:
                frame = frame_gen_event.get_frame()
                event_frame_counter += 1
                frame_path = os.path.join(event_based_dir, format_frame_number(event_frame_counter))
                save_frame_jpeg(frame, frame_path, jpeg_quality)
            
            elapsed = time.time() - start_time
            
            print("\n" + "=" * 60)
            print("Processing complete!")
            print(f"Time-based frames: {time_frame_counter}")
            print(f"Event-based frames: {event_frame_counter}")
            print(f"Total events processed: {total_events}")
            print(f"Processing time: {elapsed:.2f} seconds")
            print(f"Output directories:")
            print(f"  - Time-based: {time_based_dir}")
            print(f"  - Event-based: {event_based_dir}")
            print("=" * 60)
            
            return True
            
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    global FILE_PATH, FPS, EVENTS_PER_FRAME, OUTPUT_DIR, JPEG_QUALITY
    global SHUTTER_TYPE, BOXCAR_PERIOD, BOXCAR_DUTY, BRIGHTNESS, DECAY_RATE
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process events through dual pipelines')
    parser.add_argument('--file', type=str, default=FILE_PATH,
                       help='Path to input AEDAT4 file')
    parser.add_argument('--fps', type=int, default=FPS,
                       help='FPS for time-based pipeline')
    parser.add_argument('--events-per-frame', type=int, default=EVENTS_PER_FRAME,
                       help='Number of events per frame for event-based pipeline')
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR,
                       help='Base output directory')
    parser.add_argument('--jpeg-quality', type=int, default=JPEG_QUALITY,
                       help='JPEG compression quality (1-100)')
    parser.add_argument('--shutter', type=str, choices=['boxcar', 'morlet', 'no_shutter'],
                       default=SHUTTER_TYPE, help='Shutter function type')
    parser.add_argument('--period', type=float, default=BOXCAR_PERIOD,
                       help='Period for boxcar shutter (seconds)')
    parser.add_argument('--duty', type=float, default=BOXCAR_DUTY,
                       help='Duty cycle for boxcar shutter (0-1)')
    parser.add_argument('--brightness', type=float, default=BRIGHTNESS,
                       help='Brightness multiplier (1.0 = normal, >1.0 = brighter)')
    parser.add_argument('--decay-rate', type=float, default=DECAY_RATE,
                       help='Frame persistence decay (1.0 = no decay, 0.95 = 5%% fade per frame)')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("Dual Pipeline Event Processing")
    print("=" * 60)
    print(f"Input file: {args.file}")
    print(f"Time-based FPS: {args.fps}")
    print(f"Event-based events per frame: {args.events_per_frame}")
    print(f"Output directory: {args.output_dir}")
    print(f"JPEG quality: {args.jpeg_quality}")
    print(f"Shutter: {args.shutter}")
    if args.shutter == 'boxcar':
        print(f"  Period: {args.period}s, Duty: {args.duty}")
    print(f"Brightness: {args.brightness}x")
    print(f"Decay rate: {args.decay_rate}")
    print("=" * 60 + "\n")
    
    success = process_dual_pipeline(
        file_path=args.file,
        output_dir=args.output_dir,
        fps=args.fps,
        events_per_frame=args.events_per_frame,
        shutter_type=args.shutter,
        period=args.period,
        duty=args.duty,
        brightness=args.brightness,
        decay_rate=args.decay_rate,
        jpeg_quality=args.jpeg_quality
    )
    
    if success:
        print("\n✓ Processing completed successfully")
    else:
        print("\n✗ Processing failed")
    
    return success


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user")


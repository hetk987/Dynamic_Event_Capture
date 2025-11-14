#!/usr/bin/env python3
"""
AEDAT to MP4 Converter
Convert AEDAT4 event camera files to MP4 video files
Supports time-based and event-based frame generation
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
from utils.video_writer import VideoWriter


# Configuration
FILE_PATH = './data/dvSave-2025_11_12_20_21_55.aedat4'
OUTPUT_PATH = './output/stop.mp4'
PIPELINE_TYPE = 'time_based'  # 'time_based' or 'event_based'
FPS = 30
EVENTS_PER_FRAME = 10000
BRIGHTNESS = 3.0
DECAY_RATE = 0.0
VIDEO_CODEC = 'mp4v'


def convert_aedat_to_mp4(file_path, output_path, pipeline_type='time_based',
                         fps=30, events_per_frame=10000,
                         brightness=3.0, decay_rate=0.5, codec='mp4v'):
    """
    Convert AEDAT4 file to MP4 video
    
    Args:
        file_path: Path to input AEDAT4 file
        output_path: Path to output MP4 file
        pipeline_type: 'time_based' or 'event_based'
        fps: Frames per second for time-based pipeline
        events_per_frame: Events per frame for event-based pipeline
        brightness: Brightness multiplier
        decay_rate: Frame persistence decay
        codec: Video codec (mp4v, avc1, etc.)
    
    Returns:
        True if successful, False otherwise
    """
    if not DV_OLD_AVAILABLE:
        print("Error: dv library not available. Install it with: pip install dv")
        return False
    
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
            
            # Initialize frame generator based on pipeline type
            # Use 'no_shutter' for simple conversion (all events weighted equally)
            if pipeline_type == 'time_based':
                frame_gen = FrameGenerator(
                    width=width,
                    height=height,
                    fps=fps,
                    shutter_type='no_shutter',
                    brightness=brightness,
                    decay_rate=decay_rate
                )
                print(f"Using time-based pipeline: {fps} FPS")
            else:  # event_based
                frame_gen = EventBasedFrameGenerator(
                    width=width,
                    height=height,
                    events_per_frame=events_per_frame,
                    shutter_type='no_shutter',
                    brightness=brightness,
                    decay_rate=decay_rate
                )
                print(f"Using event-based pipeline: {events_per_frame} events per frame")
            
            # Initialize video writer
            video_writer = VideoWriter(output_path, width, height, fps=fps, codec=codec)
            
            # Processing state
            t0 = timestamps[0]
            frame_interval = 1.0 / fps if pipeline_type == 'time_based' else None
            last_frame_time_s = 0.0
            
            frame_counter = 0
            total_events = len(events)
            
            print("\nProcessing events and generating video...")
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
                
                if pipeline_type == 'time_based':
                    # Add events to time-based generator
                    frame_gen.add_events(batch_ts, batch_x, batch_y, batch_pol)
                    
                    # Check if it's time to generate frame(s)
                    # Handle case where batch spans multiple frame intervals
                    current_time_s = batch_ts_s[-1] if len(batch_ts_s) > 0 else last_frame_time_s
                    
                    # Generate all frames that should have been created in this batch
                    while current_time_s >= last_frame_time_s + frame_interval:
                        frame = frame_gen.get_frame()
                        video_writer.write_frame(frame)
                        frame_counter += 1
                        
                        frame_gen.reset_frame()
                        last_frame_time_s += frame_interval
                
                else:  # event_based
                    # Add events to event-based generator
                    events_added, should_generate = frame_gen.add_events(
                        batch_ts, batch_x, batch_y, batch_pol
                    )
                    
                    # Check if we should generate a frame
                    if should_generate:
                        frame = frame_gen.get_frame()
                        video_writer.write_frame(frame)
                        frame_counter += 1
                        
                        frame_gen.reset_frame()
                
                # Advance to next batch
                i = batch_end
                
                # Progress report
                if i % 100000 == 0 or i == total_events:
                    progress = (i / total_events) * 100
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    print(f"Progress: {progress:.1f}% ({i}/{total_events} events, {rate:.0f} events/sec) | "
                          f"Frames: {frame_counter}")
            
            # Generate final frame if there are remaining events
            if pipeline_type == 'time_based':
                if frame_gen.get_event_count() > 0:
                    frame = frame_gen.get_frame()
                    video_writer.write_frame(frame)
                    frame_counter += 1
            else:  # event_based
                if frame_gen.get_event_count() > 0:
                    frame = frame_gen.get_frame()
                    video_writer.write_frame(frame)
                    frame_counter += 1
            
            # Release video writer
            video_writer.release()
            
            elapsed = time.time() - start_time
            
            print("\n" + "=" * 60)
            print("Conversion complete!")
            print(f"Total frames: {frame_counter}")
            print(f"Total events processed: {total_events}")
            print(f"Processing time: {elapsed:.2f} seconds")
            print(f"Output video: {output_path}")
            print("=" * 60)
            
            return True
            
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    global FILE_PATH, OUTPUT_PATH, PIPELINE_TYPE, FPS, EVENTS_PER_FRAME
    global BRIGHTNESS, DECAY_RATE, VIDEO_CODEC
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Convert AEDAT4 files to MP4 videos')
    parser.add_argument('--file', type=str, default=FILE_PATH,
                       help='Path to input AEDAT4 file')
    parser.add_argument('--output', type=str, default=OUTPUT_PATH,
                       help='Path to output MP4 file')
    parser.add_argument('--pipeline', type=str, choices=['time_based', 'event_based'],
                       default=PIPELINE_TYPE, help='Pipeline type: time_based or event_based')
    parser.add_argument('--fps', type=int, default=FPS,
                       help='FPS for time-based pipeline')
    parser.add_argument('--events-per-frame', type=int, default=EVENTS_PER_FRAME,
                       help='Number of events per frame for event-based pipeline')
    parser.add_argument('--brightness', type=float, default=BRIGHTNESS,
                       help='Brightness multiplier (1.0 = normal, >1.0 = brighter)')
    parser.add_argument('--decay-rate', type=float, default=DECAY_RATE,
                       help='Frame persistence decay (1.0 = no decay, 0.95 = 5%% fade per frame)')
    parser.add_argument('--codec', type=str, default=VIDEO_CODEC,
                       help='Video codec (mp4v, avc1, etc.)')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("AEDAT to MP4 Converter")
    print("=" * 60)
    print(f"Input file: {args.file}")
    print(f"Output file: {args.output}")
    print(f"Pipeline: {args.pipeline}")
    if args.pipeline == 'time_based':
        print(f"FPS: {args.fps}")
    else:
        print(f"Events per frame: {args.events_per_frame}")
    print(f"Brightness: {args.brightness}x")
    print(f"Decay rate: {args.decay_rate}")
    print(f"Codec: {args.codec}")
    print("=" * 60 + "\n")
    
    success = convert_aedat_to_mp4(
        file_path=args.file,
        output_path=args.output,
        pipeline_type=args.pipeline,
        fps=args.fps,
        events_per_frame=args.events_per_frame,
        brightness=args.brightness,
        decay_rate=args.decay_rate,
        codec=args.codec
    )
    
    if success:
        print("\n✓ Conversion completed successfully")
    else:
        print("\n✗ Conversion failed")
    
    return success


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user")


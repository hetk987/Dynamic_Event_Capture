#!/usr/bin/env python3
"""
Frame-based Event Camera Capture with DCE
Generate 30fps frames from event camera data (live or recorded)
"""

import argparse
import cv2
import threading
import time
import os
from collections import deque
import numpy as np

# Try to import both camera libraries
try:
    import dv_processing as dv
    DV_PROCESSING_AVAILABLE = True
except ImportError:
    DV_PROCESSING_AVAILABLE = False

try:
    import dv as dv_old
    DV_OLD_AVAILABLE = True
except ImportError:
    DV_OLD_AVAILABLE = False

from utils.frame_generator import FrameGenerator
from utils.video_writer import VideoWriter


# Configuration
INPUT_SOURCE = 'camera'  # 'camera' or 'file'
FILE_PATH = './data/dvSave-2025_10_22_18_42_06.aedat4'
FPS = 15
ENABLE_MP4_RECORDING = False
OUTPUT_PATH = './output/recording.mp4'
SHUTTER_TYPE = 'no_shutter' # 'boxcar', 'morlet', 'no_shutter'
BOXCAR_PERIOD = 0.1
BOXCAR_DUTY = 0.25

# Camera settings
DOWNSAMPLING = 50
BUFFER_SIZE = 50000

# Global data buffers and flags
event_buffer = deque(maxlen=BUFFER_SIZE)
data_lock = threading.Lock()
running = True
camera_resolution = None


def stream_camera_data():
    """Stream data from DVXplorer camera"""
    global event_buffer, running
    global camera_resolution
    
    if not DV_PROCESSING_AVAILABLE:
        print("Error: dv-processing not available. Install it with: pip install dv-processing")
        return
    
    try:
        print("Opening camera...")
        capture = dv.io.camera.open()
        
        print(f"Connected to camera: {capture.getCameraName()}")
        
        if capture.isEventStreamAvailable():
            resolution = capture.getEventResolution()
            print(f"Event resolution: {resolution[0]}x{resolution[1]}")
            camera_resolution = (resolution[0], resolution[1])
        else:
            camera_resolution = (640, 480)
        
        print("Starting real-time data streaming...")
        print("Move something in front of the camera to generate events!")
        
        event_count = 0
        batch_count = 0
        
        while running:
            events = capture.getNextEventBatch()
            
            if events is not None and len(events) > 0:
                batch_count += 1
                event_count += len(events)
                
                # if batch_count % 10 == 0:
                #     print(f"Received batch {batch_count}: {len(events)} events (total: {event_count})")
                
                events_np = events.numpy()
                
                # Downsample for performance
                if len(events_np) > DOWNSAMPLING:
                    events_np = events_np[::DOWNSAMPLING]
                
                timestamps = events_np['timestamp']
                x_coords = events_np['x']
                y_coords = events_np['y']
                polarities = events_np['polarity']
                
                with data_lock:
                    for i in range(len(timestamps)):
                        event_buffer.append({
                            'timestamp': timestamps[i],
                            'x': x_coords[i],
                            'y': y_coords[i],
                            'polarity': polarities[i]
                        })
            
            time.sleep(0.001)
                        
    except Exception as e:
        print(f"Error connecting to camera: {e}")
        print("Make sure your DVXplorer camera is connected via USB")
        running = False


def get_comparison_paths(output_path):
    """Generate suffixed paths for comparison videos"""
    base, ext = os.path.splitext(output_path)
    path_with_dce = f"{base}_with_dce{ext}"
    path_no_dce = f"{base}_no_dce{ext}"
    return path_with_dce, path_no_dce


def read_file_data(file_path):
    """Read events from AEDAT4 file"""
    global event_buffer, running
    
    if not DV_OLD_AVAILABLE:
        print("Error: dv library not available. Install it with: pip install dv")
        return
    
    try:
        print(f"Reading events from: {file_path}")
        
        with dv_old.AedatFile(file_path) as f:
            events = np.hstack([packet for packet in f['events'].numpy()])
            
            print(f"Total events in file: {len(events)}")
            
            # Add events to buffer in chunks
            chunk_size = 10000
            for i in range(0, len(events), chunk_size):
                if not running:
                    break
                
                chunk = events[i:i+chunk_size]
                
                with data_lock:
                    for event in chunk:
                        event_buffer.append({
                            'timestamp': event['timestamp'],
                            'x': event['x'],
                            'y': event['y'],
                            'polarity': event['polarity']
                        })
                
                time.sleep(0.01)  # Small delay to simulate real-time
        
        print("Finished reading file")
        
    except Exception as e:
        print(f"Error reading file: {e}")
        running = False


def main():
    """Main function"""
    global INPUT_SOURCE, FILE_PATH, FPS, ENABLE_MP4_RECORDING, OUTPUT_PATH
    global SHUTTER_TYPE, BOXCAR_PERIOD, BOXCAR_DUTY, event_buffer, running
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Frame-based Event Camera Capture with DCE')
    parser.add_argument('--source', type=str, choices=['camera', 'file'], 
                       default=INPUT_SOURCE, help='Input source: camera or file')
    parser.add_argument('--file', type=str, default=FILE_PATH, 
                       help='Path to AEDAT4 file (if using file source)')
    parser.add_argument('--fps', type=int, default=FPS, 
                       help='Target frames per second')
    parser.add_argument('--record', action='store_true', 
                       help='Enable MP4 recording')
    parser.add_argument('--record-comparison', action='store_true',
                       help='Record two videos: one with DCE and one without for comparison')
    parser.add_argument('--output', type=str, default=OUTPUT_PATH, 
                       help='Output path for MP4 file')
    parser.add_argument('--shutter', type=str, choices=['boxcar', 'morlet', 'no_shutter'], 
                       default=SHUTTER_TYPE, help='Shutter function type')
    parser.add_argument('--period', type=float, default=BOXCAR_PERIOD, 
                       help='Period for boxcar shutter (seconds)')
    parser.add_argument('--duty', type=float, default=BOXCAR_DUTY, 
                       help='Duty cycle for boxcar shutter (0-1)')
    
    args = parser.parse_args()
    
    INPUT_SOURCE = args.source
    FILE_PATH = args.file
    FPS = args.fps
    ENABLE_MP4_RECORDING = args.record
    ENABLE_COMPARISON = args.record_comparison
    OUTPUT_PATH = args.output
    SHUTTER_TYPE = args.shutter
    BOXCAR_PERIOD = args.period
    BOXCAR_DUTY = args.duty
    
    # Start data streaming thread
    if INPUT_SOURCE == 'camera':
        print("Starting camera thread...")
        data_thread = threading.Thread(target=stream_camera_data, daemon=True)
        data_thread.start()
        
        # Wait a moment for camera to initialize
        time.sleep(2)
        
        # Get camera resolution
        if camera_resolution is not None:
            width, height = camera_resolution
        elif len(event_buffer) > 0:
            with data_lock:
                # Estimate resolution from events
                x_max = max(e['x'] for e in list(event_buffer)[:1000]) if len(event_buffer) > 0 else 640
                y_max = max(e['y'] for e in list(event_buffer)[:1000]) if len(event_buffer) > 0 else 480
                width = int(x_max) + 1
                height = int(y_max) + 1
        else:
            width, height = 640, 480
    else:
        print("Starting file reading thread...")
        data_thread = threading.Thread(target=read_file_data, args=(FILE_PATH,), daemon=True)
        data_thread.start()
        
        # Wait for some data to be loaded
        while len(event_buffer) < 1000 and running:
            time.sleep(0.1)
        
        # Get resolution from file
        with data_lock:
            if len(event_buffer) > 0:
                x_max = max(e['x'] for e in list(event_buffer))
                y_max = max(e['y'] for e in list(event_buffer))
                width = int(x_max) + 1
                height = int(y_max) + 1
            else:
                width, height = 640, 480
    
    print(f"Detected resolution: {width}x{height}")
    
    # Determine mode
    comparison_mode = ENABLE_COMPARISON
    
    # Initialize frame generator(s)
    if comparison_mode:
        # Dual frame generators for comparison mode
        frame_gen_dce = FrameGenerator(
            width=width,
            height=height,
            fps=FPS,
            shutter_type=SHUTTER_TYPE,
            period=BOXCAR_PERIOD,
            duty=BOXCAR_DUTY
        )
        frame_gen_no_dce = FrameGenerator(
            width=width,
            height=height,
            fps=FPS,
            shutter_type='no_shutter',
            period=BOXCAR_PERIOD,
            duty=BOXCAR_DUTY
        )
        video_writer = None
        video_writer_dce = None
        video_writer_no_dce = None
        
        # Initialize dual video writers
        path_with_dce, path_no_dce = get_comparison_paths(OUTPUT_PATH)
        video_writer_dce = VideoWriter(path_with_dce, width, height, fps=FPS)
        video_writer_no_dce = VideoWriter(path_no_dce, width, height, fps=FPS)
    else:
        # Single frame generator for normal mode
        frame_gen = FrameGenerator(
            width=width,
            height=height,
            fps=FPS,
            shutter_type=SHUTTER_TYPE,
            period=BOXCAR_PERIOD,
            duty=BOXCAR_DUTY
        )
        
        # Initialize video writer if enabled
        video_writer = None
        if ENABLE_MP4_RECORDING:
            video_writer = VideoWriter(OUTPUT_PATH, width, height, fps=FPS)
        
        # Create OpenCV window
        window_name = 'Event Camera - Frame View'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    # Print status
    print("\n" + "=" * 60)
    if comparison_mode:
        print("Frame-based Event Camera with DCE - COMPARISON MODE")
    else:
        print("Frame-based Event Camera with DCE")
    print("=" * 60)
    print(f"Source: {INPUT_SOURCE}")
    if INPUT_SOURCE == 'file':
        print(f"File: {FILE_PATH}")
    print(f"Resolution: {width}x{height}")
    print(f"FPS: {FPS}")
    print(f"Shutter: {SHUTTER_TYPE}")
    if SHUTTER_TYPE == 'boxcar':
        print(f"Period: {BOXCAR_PERIOD}s, Duty: {BOXCAR_DUTY}")
    
    if comparison_mode:
        print("Recording comparison videos:")
        path_with_dce, path_no_dce = get_comparison_paths(OUTPUT_PATH)
        print(f"  - With DCE: {path_with_dce}")
        print(f"  - No DCE:   {path_no_dce}")
        print("Display: OFF (comparison mode)")
        print("Press Ctrl+C to stop")
    else:
        print(f"Recording: {'ON' if ENABLE_MP4_RECORDING else 'OFF'}")
        if ENABLE_MP4_RECORDING:
            print(f"Output: {OUTPUT_PATH}")
        print("Press 'q' to quit")
    print("=" * 60 + "\n")
    
    frame_interval = 1.0 / FPS
    last_frame_time = time.time()
    frame_counter = 0
    
    # Main loop
    while running:
        current_time = time.time()
        
        # Check if it's time to generate a new frame
        if current_time - last_frame_time >= frame_interval:
            # Get events from buffer
            with data_lock:
                if len(event_buffer) > 0:
                    # Extract events that fit within a time window
                    events_list = list(event_buffer)
                    
                    # Get timestamp range
                    if len(events_list) > 1:
                        timestamps = np.array([e['timestamp'] for e in events_list])
                        x_coords = np.array([e['x'] for e in events_list])
                        y_coords = np.array([e['y'] for e in events_list])
                        polarities = np.array([e['polarity'] for e in events_list])
                        
                        # Get events within one frame interval
                        t0 = timestamps[0]
                        t_end = t0 + (frame_interval * 1e6)  # Convert to microseconds
                        
                        mask = timestamps < t_end
                        
                        if np.any(mask):
                            if comparison_mode:
                                # Comparison mode: process events twice for dual video
                                num_added_dce = frame_gen_dce.add_events(
                                    timestamps[mask],
                                    x_coords[mask],
                                    y_coords[mask],
                                    polarities[mask]
                                )
                                num_added_no_dce = frame_gen_no_dce.add_events(
                                    timestamps[mask],
                                    x_coords[mask],
                                    y_coords[mask],
                                    polarities[mask]
                                )
                                
                                if num_added_dce > 0 or num_added_no_dce > 0:
                                    # Generate both frames
                                    frame_dce = frame_gen_dce.get_frame()
                                    frame_no_dce = frame_gen_no_dce.get_frame()
                                    
                                    # Write to both video files
                                    video_writer_dce.write_frame(frame_dce)
                                    video_writer_no_dce.write_frame(frame_no_dce)
                                    
                                    frame_counter += 1
                                    
                                    if frame_counter % 30 == 0:
                                        buffer_size = len(event_buffer)
                                        print(f"Frame {frame_counter}: Events in buffer: {buffer_size}")
                                
                                # Remove processed events
                                num_to_remove = np.sum(mask)
                                for _ in range(num_to_remove):
                                    event_buffer.popleft()
                                
                                # Reset both frame buffers
                                frame_gen_dce.reset_frame()
                                frame_gen_no_dce.reset_frame()
                            else:
                                # Normal mode: single video with optional display
                                num_added = frame_gen.add_events(
                                    timestamps[mask],
                                    x_coords[mask],
                                    y_coords[mask],
                                    polarities[mask]
                                )
                                
                                if num_added > 0:
                                    # Generate and display frame
                                    frame = frame_gen.get_frame()
                                    
                                    # Write to video if enabled
                                    if video_writer:
                                        video_writer.write_frame(frame)
                                    
                                    # Display frame
                                    cv2.imshow(window_name, frame)
                                    
                                    frame_counter += 1
                                    
                                    if frame_counter % 30 == 0:
                                        buffer_size = len(event_buffer)
                                        print(f"Frame {frame_counter}: Events in buffer: {buffer_size}")
                                
                                # Remove processed events
                                num_to_remove = np.sum(mask)
                                for _ in range(num_to_remove):
                                    event_buffer.popleft()
                                
                                # Reset frame buffer
                                frame_gen.reset_frame()
            
            last_frame_time = current_time
        
        # Check for quit (only in normal mode)
        if not comparison_mode:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("Quit requested")
                running = False
        else:
            # In comparison mode, just check for keyboard interrupt
            time.sleep(0.001)
        
        # Small sleep to prevent busy waiting
        if not comparison_mode:
            time.sleep(0.001)
    
    # Cleanup
    print("\nShutting down...")
    if comparison_mode:
        if video_writer_dce:
            video_writer_dce.release()
        if video_writer_no_dce:
            video_writer_no_dce.release()
    else:
        if video_writer:
            video_writer.release()
        cv2.destroyAllWindows()
    print("Done!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        running = False


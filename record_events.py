#!/usr/bin/env python3
"""
Event Recording Script
Record events from camera or file to AEDAT4 format
"""

import argparse
import cv2
import threading
import time
import os
from datetime import datetime
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


# Configuration
INPUT_SOURCE = 'camera'  # 'camera' or 'file'
FILE_PATH = './data/dvSave-2025_10_22_18_42_06.aedat4'
OUTPUT_DIR = './data/'
ENABLE_PREVIEW = True
PREVIEW_SCALE = 0.5  # Scale factor for preview window

# Camera settings
DOWNSAMPLING = 10
BUFFER_SIZE = 50000

# Global flags
running = True
camera_resolution = None
preview_frame = None
preview_lock = threading.Lock()


def create_preview_frame(events_list, width, height):
    """Create a simple preview frame from recent events"""
    if len(events_list) == 0:
        return None
    
    # Take last N events for preview
    preview_events = list(events_list)[-10000:] if len(events_list) > 10000 else events_list
    
    # Create frame
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    for event in preview_events:
        x = int(event['x'])
        y = int(event['y'])
        polarity = event['polarity']
        
        if 0 <= x < width and 0 <= y < height:
            if polarity > 0:
                frame[y, x, 1] = 255  # Green
            else:
                frame[y, x, 2] = 255  # Red
    
    return frame


def update_preview(events_list, width, height):
    """Update preview frame in separate thread"""
    global preview_frame
    
    while running:
        if len(events_list) > 0:
            frame = create_preview_frame(events_list, width, height)
            if frame is not None:
                with preview_lock:
                    preview_frame = frame
        time.sleep(0.033)  # ~30fps preview update


def record_from_camera(output_path):
    """Record events from camera to AEDAT4 file"""
    global running, camera_resolution
    
    if not DV_PROCESSING_AVAILABLE:
        print("Error: dv-processing not available. Install it with: pip install dv-processing")
        return False
    
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
        
        width, height = camera_resolution
        
        print(f"Starting recording to: {output_path}")
        print("Press 'q' to stop recording")
        
        # Create recorder
        recorder = dv.io.MonoCameraWriter(output_path, capture.getCameraName())
        
        # Initialize preview if enabled
        preview_thread = None
        if ENABLE_PREVIEW:
            preview_events = []
            preview_thread = threading.Thread(target=update_preview, args=(preview_events, width, height), daemon=True)
            preview_thread.start()
            
            window_name = 'Recording Preview (Press q to stop)'
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, int(width * PREVIEW_SCALE), int(height * PREVIEW_SCALE))
        
        event_count = 0
        start_time = time.time()
        
        while running:
            events = capture.getNextEventBatch()
            
            if events is not None and len(events) > 0:
                # Write events to recorder
                recorder.writeEvents(events)
                
                event_count += len(events)
                
                # Update preview
                if ENABLE_PREVIEW and preview_thread:
                    events_np = events.numpy()
                    if len(events_np) > DOWNSAMPLING:
                        events_np = events_np[::DOWNSAMPLING]
                    
                    for event in events_np:
                        preview_events.append({
                            'timestamp': event['timestamp'],
                            'x': event['x'],
                            'y': event['y'],
                            'polarity': event['polarity']
                        })
                    
                    # Keep preview buffer size manageable
                    if len(preview_events) > 50000:
                        preview_events = preview_events[-50000:]
                
                # Display preview
                if ENABLE_PREVIEW:
                    with preview_lock:
                        if preview_frame is not None:
                            preview_scaled = cv2.resize(preview_frame, 
                                                       (int(width * PREVIEW_SCALE), 
                                                        int(height * PREVIEW_SCALE)))
                            cv2.imshow(window_name, preview_scaled)
                    
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("Stop requested")
                        running = False
                
                # Progress report
                elapsed = time.time() - start_time
                if event_count % 100000 == 0:
                    rate = event_count / elapsed if elapsed > 0 else 0
                    print(f"Recorded {event_count} events ({rate:.0f} events/sec)")
            
            time.sleep(0.001)
        
        # Close recorder
        recorder.close()
        
        if ENABLE_PREVIEW:
            cv2.destroyAllWindows()
        
        elapsed = time.time() - start_time
        print(f"\nRecording complete!")
        print(f"Total events: {event_count}")
        print(f"Duration: {elapsed:.2f} seconds")
        print(f"Average rate: {event_count/elapsed:.0f} events/sec")
        print(f"Saved to: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"Error recording from camera: {e}")
        return False


def copy_file_to_output(input_path, output_path):
    """Copy existing AEDAT4 file to output path"""
    import shutil
    
    try:
        print(f"Copying file from: {input_path}")
        print(f"To: {output_path}")
        
        shutil.copy2(input_path, output_path)
        
        # Verify file was copied
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"File copied successfully ({file_size / (1024*1024):.2f} MB)")
            return True
        else:
            print("Error: File copy failed")
            return False
            
    except Exception as e:
        print(f"Error copying file: {e}")
        return False


def main():
    """Main function"""
    global INPUT_SOURCE, FILE_PATH, OUTPUT_DIR, ENABLE_PREVIEW, running
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Record events to AEDAT4 file')
    parser.add_argument('--source', type=str, choices=['camera', 'file'], 
                       default=INPUT_SOURCE, help='Input source: camera or file')
    parser.add_argument('--file', type=str, default=FILE_PATH, 
                       help='Path to input AEDAT4 file (if using file source)')
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR,
                       help='Output directory for recorded files')
    parser.add_argument('--no-preview', action='store_true',
                       help='Disable preview window')
    
    args = parser.parse_args()
    
    INPUT_SOURCE = args.source
    FILE_PATH = args.file
    OUTPUT_DIR = args.output_dir
    ENABLE_PREVIEW = not args.no_preview
    
    # Create output directory if needed
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    output_filename = f"dvSave-{timestamp}.aedat4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    print("\n" + "=" * 60)
    print("Event Recording to AEDAT4")
    print("=" * 60)
    print(f"Source: {INPUT_SOURCE}")
    if INPUT_SOURCE == 'file':
        print(f"Input file: {FILE_PATH}")
    print(f"Output: {output_path}")
    print(f"Preview: {'ON' if ENABLE_PREVIEW else 'OFF'}")
    print("=" * 60 + "\n")
    
    success = False
    
    if INPUT_SOURCE == 'camera':
        success = record_from_camera(output_path)
    else:
        # For file source, just copy the file
        success = copy_file_to_output(FILE_PATH, output_path)
    
    if success:
        print(f"\n✓ Recording saved to: {output_path}")
    else:
        print("\n✗ Recording failed")
    
    return success


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        running = False


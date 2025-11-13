#!/usr/bin/env python3
"""
Event Recording Script
Record events from camera or file to AEDAT4 format
"""

import argparse
import cv2
import time
import os
from datetime import datetime, timedelta
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
FILE_PATH = './data/test.aedat4'
OUTPUT_DIR = './data/'
ENABLE_PREVIEW = True
PREVIEW_SCALE = 0.5  # Scale factor for preview window
PREVIEW_DECAY = 0.50  # Decay rate per frame (0.98 = 2% fade per frame)
PREVIEW_BRIGHTNESS = 10.0  # Brightness multiplier

# Noise filtering configuration
ENABLE_NOISE_FILTER = True  # Enable background activity noise filter (default: enabled)
NOISE_FILTER_ACTIVITY_PERIOD_MS = 1.0  # Noise filter activity period in milliseconds (default: 1.0ms)

# Camera settings
DOWNSAMPLING = 100  # Only used for preview visualization, NOT for recording
BUFFER_SIZE = 50000

# Global flags
running = True
camera_resolution = None


def record_from_camera(output_path):
    """
    Record events from camera to AEDAT4 file with optional noise filtering.
    
    Args:
        output_path: Path to output AEDAT4 file
        
    Returns:
        bool: True if recording successful, False otherwise
    """
    global running, camera_resolution, ENABLE_NOISE_FILTER, NOISE_FILTER_ACTIVITY_PERIOD_MS
    
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
        
        # Initialize noise filter if enabled
        noise_filter = None
        if ENABLE_NOISE_FILTER:
            try:
                activity_period = timedelta(milliseconds=NOISE_FILTER_ACTIVITY_PERIOD_MS)
                noise_filter = dv.noise.BackgroundActivityNoiseFilter((width, height), activity_period)
                print(f"Noise filter enabled (activity period: {NOISE_FILTER_ACTIVITY_PERIOD_MS}ms)")
            except (AttributeError, ImportError, Exception) as e:
                print(f"Warning: Noise filter not available ({e}). Recording without noise filtering.")
                noise_filter = None
                ENABLE_NOISE_FILTER = False
        else:
            print("Noise filter disabled")
        
        print(f"Starting recording to: {output_path}")
        print("Press 'q' to stop recording")
        
        # Create recorder - pass the capture object, not the camera name
        recorder = dv.io.MonoCameraWriter(output_path, capture)
        
        # Initialize preview frame accumulator (float for decay)
        preview_frame = None
        if ENABLE_PREVIEW:
            preview_frame = np.zeros((height, width, 3), dtype=np.float32)
            window_name = 'Recording Preview (Press q to stop)'
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, int(width * PREVIEW_SCALE), int(height * PREVIEW_SCALE))
        
        # Statistics tracking
        raw_event_count = 0
        filtered_event_count = 0
        start_time = time.time()
        last_decay_time = time.time()
        last_display_time = time.time()
        decay_interval = 0.016  # Apply decay every ~16ms (60Hz decay)
        display_interval = 0.033  # Update display every ~33ms (30fps)
        
        while running:
            events = capture.getNextEventBatch()
            current_time = time.time()
            
            if events is not None and len(events) > 0:
                # Track raw events
                raw_event_count += len(events)
                
                # Filter events if noise filter is enabled
                if noise_filter is not None:
                    try:
                        # Pass events to filter
                        noise_filter.accept(events)
                        # Get filtered events (may return empty if filter is still processing)
                        filtered_events = noise_filter.generateEvents()
                        # Record filtered events (even if empty - filter may buffer internally)
                        if len(filtered_events) > 0:
                            recorder.writeEvents(filtered_events)
                            filtered_event_count += len(filtered_events)
                        # Note: Filter may buffer some events internally for analysis.
                        # Remaining events will be flushed at the end of recording.
                    except Exception as e:
                        # If filtering fails, record raw events
                        print(f"Warning: Noise filter error ({e}), recording raw events")
                        recorder.writeEvents(events)
                        filtered_event_count += len(events)
                else:
                    # Record raw events (no filtering) - ALL events are written directly
                    recorder.writeEvents(events)
                    filtered_event_count += len(events)
                
                # Use filtered_event_count for progress reporting
                event_count = filtered_event_count
                
                # Add new events to preview frame
                if ENABLE_PREVIEW:
                    events_np = events.numpy()
                    
                    # Clip coordinates to valid range
                    x_coords = np.clip(events_np['x'], 0, width - 1).astype(int)
                    y_coords = np.clip(events_np['y'], 0, height - 1).astype(int)
                    polarities = events_np['polarity']
                    
                    # Add events directly to frame (positive = green, negative = red)
                    for i in range(len(x_coords)):
                        x, y = x_coords[i], y_coords[i]
                        if polarities[i] > 0:
                            preview_frame[y, x, 1] = min(preview_frame[y, x, 1] + PREVIEW_BRIGHTNESS * 50, 255.0)
                        else:
                            preview_frame[y, x, 2] = min(preview_frame[y, x, 2] + PREVIEW_BRIGHTNESS * 50, 255.0)
                
                # Progress report with statistics
                elapsed = time.time() - start_time
                if filtered_event_count % 100000 == 0:
                    rate = filtered_event_count / elapsed if elapsed > 0 else 0
                    if noise_filter is not None and raw_event_count > 0:
                        reduction_factor = filtered_event_count / raw_event_count
                        percentage_filtered = (1.0 - reduction_factor) * 100.0
                        print(f"Recorded {filtered_event_count:,} events ({rate:.0f} events/sec) | "
                              f"Raw: {raw_event_count:,} | "
                              f"({percentage_filtered:.1f}% noise removed)")
                    else:
                        print(f"Recorded {filtered_event_count:,} events ({rate:.0f} events/sec)")
            
            # Apply decay and update display periodically
            if ENABLE_PREVIEW:
                # Apply decay based on time elapsed
                time_since_decay = current_time - last_decay_time
                if time_since_decay >= decay_interval:
                    # Calculate decay factor based on actual time elapsed
                    decay_factor = PREVIEW_DECAY ** (time_since_decay / decay_interval)
                    preview_frame *= decay_factor
                    last_decay_time = current_time
                
                # Update display periodically
                time_since_display = current_time - last_display_time
                if time_since_display >= display_interval:
                    # Convert to uint8
                    display_frame = np.clip(preview_frame, 0, 255).astype(np.uint8)
                    
                    # Resize for display
                    preview_scaled = cv2.resize(display_frame, 
                                               (int(width * PREVIEW_SCALE), 
                                                int(height * PREVIEW_SCALE)))
                    cv2.imshow(window_name, preview_scaled)
                    last_display_time = current_time
                
                # Always check for key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("Stop requested")
                    running = False
            
            time.sleep(0.001)
        
        # Flush any remaining filtered events from the noise filter
        # The filter may buffer events internally for analysis - ensure all are written
        if noise_filter is not None:
            try:
                # Call generateEvents() multiple times to ensure all buffered events are retrieved
                # Some filters may return events in chunks, so we keep calling until empty
                total_flushed = 0
                max_flush_attempts = 10  # Prevent infinite loop
                for attempt in range(max_flush_attempts):
                    remaining_events = noise_filter.generateEvents()
                    if len(remaining_events) > 0:
                        recorder.writeEvents(remaining_events)
                        filtered_event_count += len(remaining_events)
                        total_flushed += len(remaining_events)
                    else:
                        break  # No more events to flush
                
                if total_flushed > 0:
                    print(f"Flushed {total_flushed:,} remaining filtered events from buffer")
            except Exception as e:
                print(f"Warning: Error flushing noise filter ({e})")
        
        # Cleanup - MonoCameraWriter uses RAII and will finalize the file when destroyed
        # Ensure all events are written by explicitly deleting the recorder
        # The AEDAT4 file will contain all events written up to this point
        del recorder
        
        if ENABLE_PREVIEW:
            cv2.destroyAllWindows()
        
        elapsed = time.time() - start_time
        print(f"\nRecording complete!")
        print(f"Duration: {elapsed:.2f} seconds")
        
        # Display statistics
        if noise_filter is not None and raw_event_count > 0:
            reduction_factor = filtered_event_count / raw_event_count
            percentage_filtered = (1.0 - reduction_factor) * 100.0
            events_removed = raw_event_count - filtered_event_count
            print(f"Raw events received: {raw_event_count:,}")
            print(f"Filtered events recorded: {filtered_event_count:,}")
            print(f"Events removed (noise): {events_removed:,} ({percentage_filtered:.1f}%)")
            print(f"Reduction factor: {reduction_factor:.3f}")
            if hasattr(noise_filter, 'getReductionFactor'):
                try:
                    filter_reduction = noise_filter.getReductionFactor()
                    print(f"Filter reduction factor: {filter_reduction:.3f}")
                except:
                    pass
            print(f"Average rate: {filtered_event_count/elapsed:.0f} events/sec (filtered)")
        else:
            print(f"Total events: {filtered_event_count:,}")
            print(f"Average rate: {filtered_event_count/elapsed:.0f} events/sec")
        
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
    global ENABLE_NOISE_FILTER, NOISE_FILTER_ACTIVITY_PERIOD_MS
    
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
    parser.add_argument('--no-noise-filter', action='store_true',
                       help='Disable background activity noise filter (default: enabled)')
    parser.add_argument('--noise-filter-period', type=float, default=NOISE_FILTER_ACTIVITY_PERIOD_MS,
                       help=f'Noise filter activity period in milliseconds (default: {NOISE_FILTER_ACTIVITY_PERIOD_MS})')
    
    args = parser.parse_args()
    
    INPUT_SOURCE = args.source
    FILE_PATH = args.file
    OUTPUT_DIR = args.output_dir
    ENABLE_PREVIEW = not args.no_preview
    ENABLE_NOISE_FILTER = not args.no_noise_filter
    NOISE_FILTER_ACTIVITY_PERIOD_MS = args.noise_filter_period
    
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
    print(f"Noise filter: {'ON' if ENABLE_NOISE_FILTER else 'OFF'}", end='')
    if ENABLE_NOISE_FILTER:
        print(f" (activity period: {NOISE_FILTER_ACTIVITY_PERIOD_MS}ms)")
    else:
        print()
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


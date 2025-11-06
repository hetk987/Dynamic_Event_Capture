#!/usr/bin/env python3
"""
Simple test to debug visualization issues
"""

import dv_processing as dv
import numpy as np
import time

print("Starting camera test with event capture...")

try:
    # Open camera
    print("Opening camera...")
    capture = dv.io.camera.open()
    
    print(f"Connected to camera: {capture.getCameraName()}")
    
    if capture.isEventStreamAvailable():
        resolution = capture.getEventResolution()
        print(f"Event resolution: {resolution[0]}x{resolution[1]}")
    
    print("\n** WAVE YOUR HAND IN FRONT OF THE CAMERA **\n")
    print("Collecting events for 10 seconds...")
    
    all_events = []
    start_time = time.time()
    
    while time.time() - start_time < 10:
        events = capture.getNextEventBatch()
        
        if events is not None and len(events) > 0:
            print(f"Received {len(events)} events")
            print(f"Event type: {type(events)}")
            print(f"Available methods: {[m for m in dir(events) if not m.startswith('_')]}")
            
            # Store event data - try to access the numpy array directly
            events_np = events.numpy()
            print(f"Numpy array shape: {events_np.shape}")
            print(f"Numpy array dtype: {events_np.dtype}")
            
            timestamps = events_np['timestamp']
            x_coords = events_np['x']
            y_coords = events_np['y']
            polarities = events_np['polarity']
            
            for i in range(len(timestamps)):
                all_events.append({
                    'timestamp': timestamps[i],
                    'x': x_coords[i],
                    'y': y_coords[i],
                    'polarity': polarities[i]
                })
        
        time.sleep(0.01)
    
    print(f"\nCollected {len(all_events)} total events")
    
    if len(all_events) > 0:
        print("\nSample events:")
        for i in range(min(10, len(all_events))):
            e = all_events[i]
            print(f"  Event {i}: t={e['timestamp']}, x={e['x']}, y={e['y']}, p={e['polarity']}")
        
        print("\n✓ Camera is working and generating events!")
        print("The visualization should work now.")
    else:
        print("\n⚠ No events captured")
        print("Make sure to wave your hand or move objects in front of the camera")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()


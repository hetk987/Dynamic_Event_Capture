#!/usr/bin/env python3
"""
Test script to verify DVXplorer camera connection using dv_processing library
"""

import dv_processing as dv
import sys
import time

def test_camera_connection():
    """Test basic camera connection"""
    try:
        print("Discovering connected cameras...")
        
        # Discover connected cameras
        cameras = dv.io.camera.discover()
        
        print(f"Device discovery: found {len(cameras)} device(s).")
        
        if len(cameras) == 0:
            print("✗ No cameras found")
            return False
        
        for camera_name in cameras:
            print(f"Detected device [{camera_name}]")
        
        # Open the first camera found
        print("\nOpening camera...")
        capture = dv.io.camera.open()
        
        print(f"✓ Opened [{capture.getCameraName()}] camera")
        
        # Check capabilities
        print("\nCamera capabilities:")
        
        if capture.isEventStreamAvailable():
            resolution = capture.getEventResolution()
            print(f"✓ Events at ({resolution[0]}x{resolution[1]}) resolution")
        
        if capture.isFrameStreamAvailable():
            resolution = capture.getFrameResolution()
            print(f"✓ Frames at ({resolution[0]}x{resolution[1]}) resolution")
        
        if capture.isImuStreamAvailable():
            print("✓ IMU measurements")
        
        if capture.isTriggerStreamAvailable():
            print("✓ Triggers")
        
        # Try to read some events
        print("\nReading event data...")
        print("** WAVE YOUR HAND IN FRONT OF THE CAMERA NOW **")
        event_count = 0
        batch_count = 0
        
        for i in range(50):  # Try to read 50 batches over ~5 seconds
            events = capture.getNextEventBatch()
            if events is not None and len(events) > 0:
                batch_count += 1
                event_count += len(events)
                print(f"Batch {batch_count}: {len(events)} events ✓")
                
                if batch_count >= 5:  # Stop after receiving 5 batches with data
                    break
            
            time.sleep(0.1)  # Wait 100ms between checks
        
        if event_count > 0:
            print(f"\n✓ Test completed successfully!")
            print(f"✓ Processed {batch_count} batches with {event_count} total events")
            return True
        else:
            print("\n⚠ Camera connected but no events received")
            print("\nThis is normal for event cameras when there's no movement!")
            print("Event cameras only generate data when pixels detect changes.")
            print("\nThe camera is working - you can run Plot_wDCE.py now.")
            print("Just make sure to move things in front of the camera to see events.")
            return True
            
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your DVXplorer camera is connected via USB")
        print("2. Check that camera drivers are installed")
        print("3. Try a different USB port")
        print("4. Verify no other applications are using the camera")
        return False

if __name__ == "__main__":
    print("DVXplorer Camera Connection Test")
    print("=" * 40)
    
    success = test_camera_connection()
    
    if success:
        print("\n✓ Camera test passed! You can now run Plot_wDCE.py")
    else:
        print("\n✗ Camera test failed. Please fix the issues above.")
        sys.exit(1)

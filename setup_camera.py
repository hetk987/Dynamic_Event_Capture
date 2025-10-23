#!/usr/bin/env python3
"""
DVXplorer Camera Setup Helper
This script helps you start your DVXplorer camera streaming
"""

import subprocess
import sys
import time

def check_dv_viewer():
    """Check if DV Viewer is available"""
    try:
        result = subprocess.run(['which', 'dv-viewer'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ DV Viewer found at: {result.stdout.strip()}")
            return True
        else:
            print("✗ DV Viewer not found in PATH")
            return False
    except Exception as e:
        print(f"✗ Error checking for DV Viewer: {e}")
        return False

def start_camera_streaming():
    """Try to start camera streaming using DV Viewer"""
    print("Attempting to start camera streaming...")
    
    try:
        # Try to start DV Viewer in background
        process = subprocess.Popen(['dv-viewer'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        print("✓ DV Viewer started")
        print("Please configure your camera in DV Viewer:")
        print("1. Select your DVXplorer camera")
        print("2. Start streaming")
        print("3. Leave DV Viewer running")
        print("4. Then run the test script in another terminal")
        
        return process
        
    except FileNotFoundError:
        print("✗ DV Viewer not found")
        print("Please install DV software from:")
        print("https://docs.inivation.com/software/current-products/dv-viewer.html")
        return None
    except Exception as e:
        print(f"✗ Error starting DV Viewer: {e}")
        return None

def main():
    print("DVXplorer Camera Setup Helper")
    print("=" * 40)
    
    print("\nStep 1: Check DV Viewer availability")
    if not check_dv_viewer():
        print("\nPlease install DV Viewer first:")
        print("1. Download from: https://docs.inivation.com/software/current-products/dv-viewer.html")
        print("2. Install the software")
        print("3. Run this script again")
        return False
    
    print("\nStep 2: Start camera streaming")
    process = start_camera_streaming()
    
    if process:
        print("\nStep 3: Test camera connection")
        print("In another terminal, run:")
        print("source .venv311/bin/activate")
        print("python test_camera.py")
        
        print("\nPress Ctrl+C to stop DV Viewer when done testing")
        
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\nStopping DV Viewer...")
            process.terminate()
            process.wait()
            print("✓ DV Viewer stopped")
    
    return True

if __name__ == "__main__":
    main()

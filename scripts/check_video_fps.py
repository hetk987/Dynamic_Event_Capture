#!/usr/bin/env python3
"""
Video FPS Diagnostic Tool
Check the actual FPS metadata of MP4 video files
"""
import argparse
import cv2
import os
import sys


def check_video_fps(video_path):
    """
    Check the FPS metadata of a video file
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Dictionary with video metadata or None if failed
    """
    if not os.path.exists(video_path):
        print(f"Error: File not found: {video_path}")
        return None
    
    # Open video file
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video file: {video_path}")
        return None
    
    # Get video metadata
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    codec = int(cap.get(cv2.CAP_PROP_FOURCC))
    
    # Convert codec to string
    codec_str = "".join([chr((codec >> 8 * i) & 0xFF) for i in range(4)])
    
    # Calculate duration
    duration = frame_count / fps if fps > 0 else 0
    
    cap.release()
    
    return {
        'fps': fps,
        'frame_count': frame_count,
        'width': width,
        'height': height,
        'codec': codec_str,
        'duration': duration
    }


def main():
    parser = argparse.ArgumentParser(description='Check FPS metadata of video files')
    parser.add_argument('video_path', type=str, help='Path to video file')
    parser.add_argument('--expected-fps', type=float, default=30.0,
                       help='Expected FPS (default: 30)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Video FPS Diagnostic Tool")
    print("=" * 60)
    print(f"File: {args.video_path}\n")
    
    metadata = check_video_fps(args.video_path)
    
    if metadata is None:
        sys.exit(1)
    
    # Display results
    print(f"Resolution:    {metadata['width']}x{metadata['height']}")
    print(f"Codec:         {metadata['codec']}")
    print(f"Frame Count:   {metadata['frame_count']}")
    print(f"FPS (actual):  {metadata['fps']:.2f}")
    print(f"Duration:      {metadata['duration']:.2f} seconds")
    
    # Compare with expected FPS
    if args.expected_fps:
        print(f"\nExpected FPS:  {args.expected_fps:.2f}")
        fps_diff = metadata['fps'] - args.expected_fps
        fps_diff_pct = (fps_diff / args.expected_fps) * 100 if args.expected_fps > 0 else 0
        
        print(f"Difference:    {fps_diff:+.2f} fps ({fps_diff_pct:+.1f}%)")
        
        if abs(fps_diff_pct) > 5:
            print("\n⚠️  WARNING: FPS difference exceeds 5%!")
            print("This could explain playback speed issues.")
            if metadata['fps'] < args.expected_fps:
                slowdown_pct = (args.expected_fps / metadata['fps'] - 1) * 100
                print(f"Video will play {slowdown_pct:.1f}% SLOWER than expected.")
            else:
                speedup_pct = (metadata['fps'] / args.expected_fps - 1) * 100
                print(f"Video will play {speedup_pct:.1f}% FASTER than expected.")
        else:
            print("\n✓ FPS is within acceptable range.")
    
    print("=" * 60)


if __name__ == '__main__':
    main()




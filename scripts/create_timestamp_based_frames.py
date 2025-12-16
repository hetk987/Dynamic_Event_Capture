#!/usr/bin/env python3
"""
Helper script to analyze event timestamp distribution in AEDAT4 files
This helps diagnose timing issues and gaps in recordings
"""
import argparse
import numpy as np

try:
    import dv as dv_old
    DV_OLD_AVAILABLE = True
except ImportError:
    DV_OLD_AVAILABLE = False


def analyze_timestamps(file_path, num_samples=100):
    """
    Analyze timestamp distribution in an AEDAT4 file
    
    Args:
        file_path: Path to AEDAT4 file
        num_samples: Number of sample points to check for gaps
    """
    if not DV_OLD_AVAILABLE:
        print("Error: dv library not available. Install it with: pip install dv")
        return
    
    print(f"Analyzing: {file_path}\n")
    
    with dv_old.AedatFile(file_path) as f:
        events = np.hstack([packet for packet in f['events'].numpy()])
        
        if len(events) == 0:
            print("No events found in file")
            return
        
        timestamps = events['timestamp']
        
        # Basic statistics
        t_start = timestamps[0]
        t_end = timestamps[-1]
        duration_us = t_end - t_start
        duration_s = duration_us * 1e-6
        
        print("=" * 60)
        print("TIMESTAMP ANALYSIS")
        print("=" * 60)
        print(f"Total events:        {len(events):,}")
        print(f"First timestamp:     {t_start:,} µs")
        print(f"Last timestamp:      {t_end:,} µs")
        print(f"Duration:            {duration_s:.2f} seconds ({duration_us:,} µs)")
        print(f"Event rate (avg):    {len(events) / duration_s:,.0f} events/sec")
        
        # Check for gaps
        print(f"\nChecking for timestamp gaps...")
        
        # Sample timestamps evenly throughout the file
        sample_indices = np.linspace(0, len(timestamps) - 1, num_samples, dtype=int)
        sample_timestamps = timestamps[sample_indices]
        
        # Calculate time differences between samples
        time_diffs = np.diff(sample_timestamps)
        expected_diff = duration_us / (num_samples - 1)
        
        # Find large gaps (>2x expected)
        large_gaps = time_diffs > (expected_diff * 2)
        
        if np.any(large_gaps):
            print(f"⚠️  Found {np.sum(large_gaps)} large timestamp gaps!")
            print("\nLargest gaps:")
            gap_indices = np.where(large_gaps)[0]
            gap_sizes = time_diffs[gap_indices]
            
            # Show top 5 largest gaps
            sorted_indices = np.argsort(gap_sizes)[::-1][:5]
            for i, idx in enumerate(sorted_indices):
                gap_idx = gap_indices[idx]
                gap_size_us = gap_sizes[idx]
                gap_size_s = gap_size_us * 1e-6
                event_idx = sample_indices[gap_idx]
                time_pos = (timestamps[event_idx] - t_start) * 1e-6
                
                print(f"  {i+1}. Gap of {gap_size_s:.2f}s at t={time_pos:.2f}s (event {event_idx:,})")
        else:
            print("✓ No significant timestamp gaps detected")
        
        # Calculate expected video duration at 30 fps
        expected_frames_30fps = int(duration_s * 30)
        expected_duration_30fps = expected_frames_30fps / 30
        
        print(f"\n" + "=" * 60)
        print("VIDEO EXPECTATIONS (30 FPS)")
        print("=" * 60)
        print(f"Expected frames:     {expected_frames_30fps}")
        print(f"Expected duration:   {expected_duration_30fps:.2f} seconds")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Analyze event timestamps in AEDAT4 files')
    parser.add_argument('file', type=str, help='Path to AEDAT4 file')
    parser.add_argument('--samples', type=int, default=100,
                       help='Number of sample points to check (default: 100)')
    
    args = parser.parse_args()
    
    analyze_timestamps(args.file, args.samples)


if __name__ == '__main__':
    main()




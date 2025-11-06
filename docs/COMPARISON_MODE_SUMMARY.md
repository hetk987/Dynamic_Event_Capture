# Comparison Mode Implementation Summary

## Overview

Successfully implemented dual video recording mode that generates two videos simultaneously from the same event stream: one with DCE applied and one without DCE. This allows for direct visual comparison of the effects of Digital Coded Exposure.

## Key Features

### Dual Recording Mode
- **Flag**: `--record-comparison`
- **Output**: Two videos with suffixed paths
  - `{output_path}_with_dce.mp4` - With DCE applied
  - `{output_path}_no_dce.mp4` - Without DCE (all events weighted 1.0)

### Performance Optimization
- **No display**: Skips OpenCV window creation and updates
- **Dual processing**: Events processed twice (once for each video) for accuracy
- **Optimized output**: Console messages only every 30 frames

### Smart Path Generation
- Automatically generates suffixed paths from base output path
- Example: `./output/test.mp4` becomes:
  - `./output/test_with_dce.mp4`
  - `./output/test_no_dce.mp4`

## Implementation Details

### Files Modified

#### `frame_based_capture.py`
- Added `--record-comparison` CLI argument
- Added `get_comparison_paths()` function for path suffixing
- Created dual `FrameGenerator` instances (one with DCE, one without)
- Created dual `VideoWriter` instances
- Modified main loop to handle both comparison and normal modes
- Conditional display disable in comparison mode
- Updated cleanup logic for dual writers

#### `QUICK_START.md`
- Added comparison recording example
- Updated configuration options table
- Added note about performance mode

#### `FRAME_BASED_README.md`
- Added comparison recording section
- Updated command line options
- Documented output file naming

### Code Changes Summary

```python
# New argument
parser.add_argument('--record-comparison', action='store_true',
                   help='Record two videos: one with DCE and one without')

# Path generation
def get_comparison_paths(output_path):
    base, ext = os.path.splitext(output_path)
    return f"{base}_with_dce{ext}", f"{base}_no_dce{ext}"

# Dual generators
if comparison_mode:
    frame_gen_dce = FrameGenerator(..., shutter_type=SHUTTER_TYPE)
    frame_gen_no_dce = FrameGenerator(..., shutter_type='no_shutter')
    
# Dual processing
frame_gen_dce.add_events(events)
frame_gen_no_dce.add_events(events)
    
# Dual output
video_writer_dce.write_frame(frame_dce)
video_writer_no_dce.write_frame(frame_no_dce)
```

## Usage Examples

### Basic Comparison Recording
```bash
python frame_based_capture.py \
    --source file \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --record-comparison \
    --output ./output/comparison_test.mp4 \
    --shutter boxcar \
    --period 0.1 \
    --duty 0.25
```

### With Morlet Shutter
```bash
python frame_based_capture.py \
    --source file \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --record-comparison \
    --output ./output/comparison_morlet.mp4 \
    --shutter morlet
```

### With Live Camera
```bash
python frame_based_capture.py \
    --source camera \
    --record-comparison \
    --output ./output/live_comparison.mp4 \
    --shutter boxcar
```

## Expected Output

### Console Output
```
Frame-based Event Camera with DCE - COMPARISON MODE
============================================================
Source: file
File: ./data/dvSave-2025_10_22_18_42_06.aedat4
Resolution: 640x480
FPS: 30
Shutter: boxcar
Period: 0.1s, Duty: 0.25
Recording comparison videos:
  - With DCE: ./output/comparison_test_with_dce.mp4
  - No DCE:   ./output/comparison_test_no_dce.mp4
Display: OFF (comparison mode)
Press Ctrl+C to stop
============================================================

Frame 30: Events in buffer: 12450
Frame 60: Events in buffer: 8320
...
```

### Generated Files
```
output/
├── comparison_test_with_dce.mp4  (DCE applied)
└── comparison_test_no_dce.mp4    (no DCE)
```

## Benefits

1. **Direct Comparison**: Side-by-side evaluation of DCE effects
2. **Performance**: No display overhead for faster processing
3. **Accuracy**: Events processed twice independently
4. **Convenience**: Automatic file naming and pairing
5. **Flexibility**: Works with all shutter types (boxcar, morlet, etc.)

## Testing Notes

- Test with small files first to verify both videos are created
- Compare file sizes (should be similar)
- Verify frame counts match in both videos
- Check visual differences between DCE and no-DCE versions
- Test with different shutter types

## Status

✅ Implementation complete
✅ Documentation updated
✅ No linter errors in Python code
✅ Ready for testing


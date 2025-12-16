# Troubleshooting Guide

Common issues, fixes, and diagnostic tools for the Event Camera Frame Capture system.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Camera Connection Issues](#camera-connection-issues)
3. [File Processing Issues](#file-processing-issues)
4. [Video Output Problems](#video-output-problems)
5. [Display/Visualization Issues](#displayvisualization-issues)
6. [Performance Issues](#performance-issues)
7. [Diagnostic Tools](#diagnostic-tools)

## Installation Issues

### Python Version Compatibility

**Problem**: Python 3.13 and higher are not supported by this project.

**Solution**: Use Python 3.8 to 3.12. Check your Python version:

```bash
python3 --version
```

If you have Python 3.13+, you need to install a compatible version:
- Download Python 3.12 from https://www.python.org/downloads/
- Use a version manager like `pyenv` to install and switch between Python versions
- Create your virtual environment with the correct Python version: `python3.12 -m venv .venv`

### "No module named 'dv_processing'"

**Solution**: Install the dv-processing package:

```bash
pip install dv-processing
```

### "No module named 'dv'"

**Solution**: Install the legacy dv package:

```bash
pip install dv
```

**Note**: The project uses both `dv-processing` (for camera capture) and `dv` (for file reading). Both are required for full functionality.

### "No module named 'cv2'"

**Solution**: Install OpenCV:

```bash
pip install opencv-python
```

### "pip: command not found"

**Solution**:
- On Linux/macOS: Use `pip3` instead of `pip`
- On Windows: Ensure Python is added to PATH during installation
- Install pip: `python -m ensurepip --upgrade`

### Virtual Environment Not Activating

**Solution**:
- Linux/macOS: Use `source .venv/bin/activate`
- Windows: Use `.venv\Scripts\activate`
- Ensure you're in the project directory

### Import Errors After Installation

**Solution**:
1. Ensure virtual environment is activated
2. Reinstall packages: `pip install --force-reinstall -r requirements.txt`
3. Verify Python version: `python3 --version` (should be 3.8+)

## Camera Connection Issues

### "Error: dv-processing not available"

**Solution**:
1. Install dv-processing: `pip install dv-processing`
2. Verify camera drivers are installed
3. Check USB connection
4. Try a different USB port

### "No cameras found"

**Solution**:
1. Verify camera is connected via USB
2. Check camera drivers are installed
3. Run `python tests/test_camera.py` to diagnose
4. On Linux, you may need to add udev rules (see camera documentation)
5. Ensure no other applications are using the camera

### Camera Detected But No Events

**Solution**:
- This is normal! Event cameras only generate events when there's movement
- Wave your hand or move objects in front of the camera
- Check camera settings in DV Viewer (if installed)

## File Processing Issues

### "File not found" or "No such file or directory"

**Solution**:
1. Verify the file path is correct
2. Use absolute paths if relative paths don't work
3. Check file permissions
4. Ensure the file is an AEDAT4 file (`.aedat4` extension)

### "No events found in file"

**Solution**:
1. Verify the file is not corrupted
2. Try a different AEDAT4 file
3. Check file size (should be > 0 bytes)

### "Error reading file"

**Solution**:
1. Ensure the `dv` package is installed: `pip install dv`
2. Verify file format is correct (AEDAT4)
3. Check file permissions

## Video Output Problems

### Video Duration is Too Long (CRITICAL FIX)

**Problem**: Videos are significantly longer than the actual recording duration. For example, a 26-second recording produces a 76-second video.

**Root Cause**: Frame generation was based on **wall-clock processing time** instead of **event timestamps**.

**Solution**: **Always use `--use-event-time` flag when processing files!**

```bash
python src/frame_based_capture.py \
    --source file \
    --file ./data/recording.aedat4 \
    --record-comparison \
    --output ./output/video.mp4 \
    --use-event-time \
    --no-pacing
```

**Why This Happens**:
- In camera mode, frames are generated in real-time based on wall-clock time (correct)
- In file mode, frames should be generated based on event timestamps (not processing time)
- Without `--use-event-time`, a 26-second recording that takes 142 seconds to process generates 4,260 frames (142 × 30fps) instead of 780 frames (26 × 30fps)

**Verification**: Check the timing diagnostics at the end of processing:

```
TIMING DIAGNOSTICS
Event time span:            28.18 seconds  ← Actual recording duration
Expected video duration:    28.17 seconds  ← Should match!
Frames generated:           845            ← Should be ~28 * 30
```

If "Event time span" ≈ "Expected video duration", it's fixed! ✅

### Video Plays Too Slowly

**Problem**: Video plays slower than expected, even though duration is correct.

**Possible Causes**:
1. **FPS metadata is incorrect**: The video file may have wrong FPS metadata
2. **Codec issues**: Some codecs don't reliably encode FPS metadata

**Solution**:
1. Check actual FPS metadata:
   ```bash
   python scripts/check_video_fps.py path/to/video.mp4 --expected-fps 30
   ```
2. If FPS is wrong, the video writer will try different codecs automatically (avc1, H264, X264, mp4v)
3. Re-encode the video if necessary

### Video FPS Metadata is Wrong

**Problem**: Video file has incorrect FPS metadata (e.g., shows 24 fps instead of 30 fps).

**Solution**:
- The video writer automatically tries multiple codecs: 'avc1', 'H264', 'X264', 'mp4v'
- Check which codec was used in the console output
- If issues persist, verify OpenCV installation and codec support

### Video File Not Created

**Solution**:
1. Check output directory exists and is writable
2. Verify output path is correct
3. Check disk space
4. Look for error messages in console output

## Display/Visualization Issues

### No Display Window Appears

**Solution**:
- **Linux (remote server)**: Enable X11 forwarding: `ssh -X user@server`
- **macOS**: Check that XQuartz is installed (if using X11)
- **Windows**: Ensure OpenCV can create windows (may need display server)
- Try running with `--record` flag to save to file instead

### "Cannot connect to X server"

**Solution**:
- Enable X11 forwarding: `ssh -X user@server`
- Install X server software (XQuartz on macOS, Xming on Windows)
- Use `--record` flag to save to file instead of displaying

### Window Opens But Shows Black Screen

**Solution**:
- Wait for events to accumulate (event cameras need movement)
- Check that events are being processed (look for console output)
- Verify input file has events
- Try increasing brightness: `--brightness 5.0`

## Performance Issues

### Processing is Very Slow

**Solution**:
1. Reduce FPS: `--fps 15`
2. Reduce events per frame: `--events-per-frame 5000` (for process_dual_pipeline.py)
3. Use smaller input files for testing
4. Close other applications to free up resources
5. Use `--no-pacing` flag to process files faster (file mode only)

### High Memory Usage

**Solution**:
1. Process files in smaller chunks
2. Reduce buffer sizes in code (advanced)
3. Use `--record-comparison` mode which is more memory efficient

### Comparison Mode is Slow

**Solution**:
- Comparison mode processes events twice (once for each video)
- This is expected behavior for accuracy
- Use `--no-pacing` with `--use-event-time` for faster file processing
- Consider processing smaller files or reducing FPS

## Diagnostic Tools

### Check Video FPS Metadata

Use the diagnostic tool to verify FPS metadata of output MP4 files:

```bash
python scripts/check_video_fps.py path/to/video.mp4 --expected-fps 30
```

**Example output:**

```
Video FPS Diagnostic Tool
File: output/scene2_with_dce.mp4

Resolution:    640x480
Codec:         avc1
Frame Count:   2196
FPS (actual):  30.00
Duration:      73.20 seconds

Expected FPS:  30.00
Difference:    +0.00 fps (+0.0%)

✓ FPS is within acceptable range.
```

### Analyze Event Timestamps

Check the actual event time span in your recording:

```bash
python scripts/create_timestamp_based_frames.py \
    "./Research_Videos/joel/scene 2/combined-1-2025_11_19_12_55_57.aedat4"
```

This shows you the expected video duration based on event timestamps.

### Test Camera Connection

Test camera connection and event stream:

```bash
python tests/test_camera.py
```

This will:
- Discover connected cameras
- Test camera connection
- Verify event stream availability
- Read sample events

### Timing Diagnostics

When processing files with `frame_based_capture.py`, timing diagnostics are printed at the end:

```
TIMING DIAGNOSTICS
Wall-clock time elapsed:    75.30 seconds
Event time span:            73.20 seconds
Frames generated:           2196
Expected video duration:    73.20 seconds
Total events processed:     12,875,651
Average FPS (wall-clock):   29.15
Event time / Wall-clock:    0.97x

⚠️  Video may be SLOWER than expected (event time < wall-clock)
```

**What to look for**:
- **Event time span** should match **Expected video duration**
- If they don't match, you may not be using `--use-event-time`
- **Event time / Wall-clock** ratio should be close to 1.0 for efficient processing

## Common Error Messages

### "Permission denied" Errors

**Solution**:
- Check file/directory permissions
- Use `chmod` to change permissions (Linux/macOS)
- Run with appropriate user permissions

### Scripts Not Found

**Solution**:
- Ensure you're in the project root directory
- Use full paths: `python /path/to/Code/src/frame_based_capture.py`
- Check that files exist: `ls src/frame_based_capture.py`

### "No events in buffer"

**Solution**:
- This is normal if there's no movement in front of the camera
- Wait for events to accumulate
- Check that the camera/file has events

## Best Practices

### For File Processing

**Always use these flags together:**

```bash
--use-event-time    # Generate frames based on event timestamps (CRITICAL!)
--no-pacing         # Process file as fast as possible (optimization)
```

### For Comparison Mode

```bash
python src/frame_based_capture.py \
    --record-comparison \
    --use-event-time \
    --no-pacing
```

### For Live Camera

No special flags needed - camera mode automatically uses wall-clock time correctly.

## Getting Help

If you encounter issues not covered here:

1. Check the console output for error messages
2. Verify all prerequisites are installed
3. Test with sample data files first
4. Review the documentation in `docs/` directory
5. Check GitHub issues (if repository has issue tracking)

## Quick Reference: Common Fixes

| Problem | Solution |
|---------|----------|
| Video too long | Use `--use-event-time` flag |
| Video plays slowly | Check FPS metadata with `check_video_fps.py` |
| No display window | Use `--record` flag or enable X11 forwarding |
| Camera not detected | Run `python tests/test_camera.py` |
| Import errors | Activate virtual environment and reinstall packages |
| File not found | Use absolute paths or verify file location |
| Processing slow | Use `--no-pacing` flag (file mode only) |


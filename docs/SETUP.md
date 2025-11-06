# Setup Guide

Complete setup instructions for the Event Camera Frame Capture with Digital Coded Exposure (DCE) project.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Git Clone](#git-clone)
3. [Python Environment Setup](#python-environment-setup)
4. [Package Installation](#package-installation)
5. [Verification](#verification)
6. [Usage Guide - frame_based_capture.py](#usage-guide---frame_based_capturepy)
7. [Usage Guide - process_dual_pipeline.py](#usage-guide---process_dual_pipelinepy)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

-   **Python 3.8 or higher**

    -   Check your version: `python3 --version` or `python --version`
    -   Download from: https://www.python.org/downloads/

-   **Git**

    -   Check if installed: `git --version`
    -   Download from: https://git-scm.com/downloads

-   **pip** (Python package manager)
    -   Usually comes with Python 3.4+
    -   Check: `pip3 --version` or `pip --version`

### Hardware Requirements (Optional)

-   **DVXplorer Event Camera** (for live camera capture)
    -   USB connection required
    -   Camera drivers must be installed
    -   See camera manufacturer documentation for driver installation

### Operating System Compatibility

-   **Linux**: Fully supported
-   **macOS**: Fully supported
-   **Windows**: Supported (may require additional setup for camera drivers)

## Git Clone

### Clone the Repository

```bash
# Clone the repository
git clone https://github.com/hetk987/Dynamic_Event_Capture.git

# Navigate to the project directory
cd Code
```

### Verify Repository Structure

After cloning, you should see the following structure:

```
Code/
├── README.md
├── requirements.txt
├── frame_based_capture.py
├── record_events.py
├── process_dual_pipeline.py
├── utils/
├── tests/
├── scripts/
├── docs/
├── data/
└── output/
```

## Python Environment Setup

### Create Virtual Environment

It's recommended to use a virtual environment to isolate project dependencies.

#### Linux/macOS

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate
```

#### Windows

```cmd
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate
```

### Verify Virtual Environment

After activation, you should see `(.venv)` in your terminal prompt:

```bash
(.venv) user@computer:~/Code$
```

### Deactivate Virtual Environment

When you're done working, deactivate the virtual environment:

```bash
deactivate
```

## Package Installation

### Install Dependencies

With your virtual environment activated, install all required packages:

```bash
# Upgrade pip (recommended)
pip install --upgrade pip

# Install all dependencies from requirements.txt
pip install -r requirements.txt
```

### Required Packages

The following packages will be installed:

-   **vispy**: Core visualization package
-   **numpy**: Numerical computing
-   **PyQt6**: GUI framework (required by vispy)
-   **dv-processing**: DVXplorer camera support (new library)
-   **opencv-python**: Video and image processing

### Additional Package: dv (Legacy)

The code also uses the legacy `dv` library for reading AEDAT4 files. Install it separately:

```bash
pip install dv
```

**Note**: The project uses both `dv-processing` (for camera capture) and `dv` (for file reading). Both are required for full functionality.

### Verify Installation

Check that all packages are installed correctly:

```bash
# Check installed packages
pip list

# Verify key packages
python3 -c "import dv_processing; print('dv-processing: OK')"
python3 -c "import dv; print('dv: OK')"
python3 -c "import cv2; print('opencv-python: OK')"
python3 -c "import numpy; print('numpy: OK')"
```

## Verification

### Test Camera Connection (Optional)

If you have a DVXplorer camera connected:

```bash
python tests/test_camera.py
```

This will:

-   Discover connected cameras
-   Test camera connection
-   Verify event stream availability
-   Read sample events

### Test File Processing

Test with a sample AEDAT4 file:

```bash
# Make sure you have a test file in the data/ directory
python frame_based_capture.py --source file --file ./data/dvSave-2025_10_22_18_39_29.aedat4
```

If everything is set up correctly, you should see a window displaying event camera frames.

## Usage Guide - frame_based_capture.py

Main script for frame-based event camera capture with DCE. Generates video frames from event camera data (live or recorded).

### Basic Usage

#### View Pre-Recorded Data

```bash
python frame_based_capture.py --source file --file ./data/dvSave-2025_10_22_18_39_29.aedat4
```

#### View Live Camera

```bash
python frame_based_capture.py --source camera
```

#### Record to MP4

```bash
python frame_based_capture.py --source file \
    --file ./data/dvSave-2025_10_22_18_39_29.aedat4 \
    --record \
    --output ./output/my_video.mp4
```

### Command-Line Options

| Option                    | Type                             | Default                                    | Description                                                        |
| ------------------------- | -------------------------------- | ------------------------------------------ | ------------------------------------------------------------------ |
| `--source`                | `camera`, `file`                 | `camera`                                   | Input source: camera or file                                       |
| `--file`                  | string                           | `./data/dvSave-2025_10_22_18_42_06.aedat4` | Path to AEDAT4 file (if using file source)                         |
| `--fps`                   | integer                          | `30`                                       | Target frames per second                                           |
| `--record`                | flag                             | `False`                                    | Enable MP4 recording                                               |
| `--record-comparison`     | flag                             | `False`                                    | Record two videos: one with DCE and one without                    |
| `--output`                | string                           | `./output/no_light_recording.mp4`          | Output path for MP4 file                                           |
| `--shutter`               | `boxcar`, `morlet`, `no_shutter` | `no_shutter`                               | Shutter function type                                              |
| `--period`                | float                            | `0.1`                                      | Period for boxcar shutter (seconds)                                |
| `--duty`                  | float                            | `0.25`                                     | Duty cycle for boxcar shutter (0-1)                                |
| `--brightness`            | float                            | `3.0`                                      | Brightness multiplier (1.0 = normal, >1.0 = brighter)              |
| `--decay-rate`            | float                            | `0.5`                                      | Frame persistence decay (1.0 = no decay, 0.95 = 5% fade per frame) |
| `--min-decay`             | float                            | `0.999999`                                 | Minimum decay rate for low activity/static scenes                  |
| `--max-decay`             | float                            | `0.25`                                     | Maximum decay rate for high activity/motion                        |
| `--low-activity`          | integer                          | `5000`                                     | Activity threshold below which decay is minimized                  |
| `--high-activity`         | integer                          | `40000`                                    | Activity threshold above which decay is maximized                  |
| `--decay-alpha`           | float                            | `0.2`                                      | Smoothing factor for decay transitions (0-1, lower = smoother)     |
| `--decay-hysteresis`      | float                            | `0.05`                                     | Minimum change required to update decay (prevents flicker)         |
| `--enable-adaptive-decay` | flag                             | `False`                                    | Enable adaptive decay based on scene activity                      |

### Usage Examples

#### Custom DCE Settings (Boxcar Shutter)

```bash
python frame_based_capture.py --source file \
    --file ./data/dvSave-2025_10_22_18_39_29.aedat4 \
    --shutter boxcar \
    --period 0.15 \
    --duty 0.3
```

#### Morlet Wavelet Shutter

```bash
python frame_based_capture.py --source file \
    --file ./data/dvSave-2025_10_22_18_39_29.aedat4 \
    --shutter morlet
```

#### Record Comparison Videos (DCE vs No-DCE)

Generate two videos simultaneously to compare the effect of DCE:

```bash
python frame_based_capture.py \
    --source file \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --record-comparison \
    --output ./output/my_test.mp4 \
    --shutter boxcar \
    --period 0.1 \
    --duty 0.25
```

This creates:

-   `./output/my_test_with_dce.mp4` (with DCE applied)
-   `./output/my_test_no_dce.mp4` (without DCE, all events weighted equally)

**Note**: Comparison mode disables the display window for maximum performance.

#### Adjust Brightness

Increase the brightness of event dots:

```bash
python frame_based_capture.py \
    --source file \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --record \
    --output ./output/bright.mp4 \
    --brightness 2.0
```

Brightness values:

-   `1.0` = normal brightness
-   `2.0` = twice as bright
-   `3.0` = three times as bright
-   Higher values make events more visible

#### Enable Adaptive Decay

Automatically adjust decay rate based on scene activity:

```bash
python frame_based_capture.py \
    --source file \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --record \
    --output ./output/adaptive.mp4 \
    --enable-adaptive-decay \
    --min-decay 0.99 \
    --max-decay 0.3 \
    --low-activity 5000 \
    --high-activity 40000
```

#### Custom Frame Rate

```bash
python frame_based_capture.py \
    --source file \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --fps 60 \
    --record \
    --output ./output/60fps.mp4
```

### Controls

-   **'q'**: Quit the application
-   **Close window**: Exit application
-   **Ctrl+C**: Stop recording (in comparison mode)

### Output

-   **Red pixels**: Polarity 0 events (OFF events)
-   **Green pixels**: Polarity 1 events (ON events)
-   **Frame rate**: Configurable (default 30 fps)
-   **DCE weighting**: Visual effect of Digital Coded Exposure applied

## Usage Guide - process_dual_pipeline.py

Process events from AEDAT4 file through two pipelines simultaneously:

1. **Time-based**: Generate frames at fixed FPS intervals
2. **Event-based**: Generate frames after accumulating N events

Outputs frames as JPEG images in separate directories.

### Basic Usage

```bash
python process_dual_pipeline.py \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --output-dir ./output/
```

### Command-Line Options

| Option               | Type                             | Default                                    | Description                                                        |
| -------------------- | -------------------------------- | ------------------------------------------ | ------------------------------------------------------------------ |
| `--file`             | string                           | `./data/dvSave-2025_10_22_18_42_06.aedat4` | Path to input AEDAT4 file                                          |
| `--fps`              | integer                          | `30`                                       | FPS for time-based pipeline                                        |
| `--events-per-frame` | integer                          | `10000`                                    | Number of events per frame for event-based pipeline                |
| `--output-dir`       | string                           | `./output/`                                | Base output directory                                              |
| `--jpeg-quality`     | integer                          | `85`                                       | JPEG compression quality (1-100)                                   |
| `--shutter`          | `boxcar`, `morlet`, `no_shutter` | `boxcar`                                   | Shutter function type                                              |
| `--period`           | float                            | `0.1`                                      | Period for boxcar shutter (seconds)                                |
| `--duty`             | float                            | `0.25`                                     | Duty cycle for boxcar shutter (0-1)                                |
| `--brightness`       | float                            | `3.0`                                      | Brightness multiplier (1.0 = normal, >1.0 = brighter)              |
| `--decay-rate`       | float                            | `0.5`                                      | Frame persistence decay (1.0 = no decay, 0.95 = 5% fade per frame) |

### Usage Examples

#### Basic Processing

```bash
python process_dual_pipeline.py \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --output-dir ./output/dual_pipeline/
```

This creates:

-   `./output/dual_pipeline/time_based/` - Time-based frames (frame_0001.jpg, frame_0002.jpg, ...)
-   `./output/dual_pipeline/event_based/` - Event-based frames (frame_0001.jpg, frame_0002.jpg, ...)

#### Custom FPS and Events Per Frame

```bash
python process_dual_pipeline.py \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --fps 60 \
    --events-per-frame 5000 \
    --output-dir ./output/custom/
```

#### Custom DCE Settings

```bash
python process_dual_pipeline.py \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --shutter boxcar \
    --period 0.15 \
    --duty 0.3 \
    --brightness 2.0 \
    --output-dir ./output/custom_dce/
```

#### High Quality JPEG Output

```bash
python process_dual_pipeline.py \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --jpeg-quality 95 \
    --output-dir ./output/high_quality/
```

#### Morlet Wavelet Shutter

```bash
python process_dual_pipeline.py \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --shutter morlet \
    --output-dir ./output/morlet/
```

### Output Structure

After processing, you'll find:

```
output/
└── [output-dir]/
    ├── time_based/
    │   ├── frame_0001.jpg
    │   ├── frame_0002.jpg
    │   └── ...
    └── event_based/
        ├── frame_0001.jpg
        ├── frame_0002.jpg
        └── ...
```

### Performance Notes

-   Processing speed depends on file size and number of events
-   Progress is reported every 100,000 events
-   Final statistics show total frames generated and processing time

## Troubleshooting

### Installation Issues

#### "No module named 'dv_processing'"

**Solution**: Install the dv-processing package:

```bash
pip install dv-processing
```

#### "No module named 'dv'"

**Solution**: Install the legacy dv package:

```bash
pip install dv
```

#### "No module named 'cv2'"

**Solution**: Install OpenCV:

```bash
pip install opencv-python
```

#### "pip: command not found"

**Solution**:

-   On Linux/macOS: Use `pip3` instead of `pip`
-   On Windows: Ensure Python is added to PATH during installation
-   Install pip: `python -m ensurepip --upgrade`

#### Virtual Environment Not Activating

**Solution**:

-   Linux/macOS: Use `source .venv/bin/activate`
-   Windows: Use `.venv\Scripts\activate`
-   Ensure you're in the project directory

### Camera Connection Issues

#### "Error: dv-processing not available"

**Solution**:

1. Install dv-processing: `pip install dv-processing`
2. Verify camera drivers are installed
3. Check USB connection
4. Try a different USB port

#### "No cameras found"

**Solution**:

1. Verify camera is connected via USB
2. Check camera drivers are installed
3. Run `python tests/test_camera.py` to diagnose
4. On Linux, you may need to add udev rules (see camera documentation)
5. Ensure no other applications are using the camera

#### Camera Detected But No Events

**Solution**:

-   This is normal! Event cameras only generate events when there's movement
-   Wave your hand or move objects in front of the camera
-   Check camera settings in DV Viewer (if installed)

### File Processing Issues

#### "File not found" or "No such file or directory"

**Solution**:

1. Verify the file path is correct
2. Use absolute paths if relative paths don't work
3. Check file permissions
4. Ensure the file is an AEDAT4 file (`.aedat4` extension)

#### "No events found in file"

**Solution**:

1. Verify the file is not corrupted
2. Try a different AEDAT4 file
3. Check file size (should be > 0 bytes)

#### "Error reading file"

**Solution**:

1. Ensure the `dv` package is installed: `pip install dv`
2. Verify file format is correct (AEDAT4)
3. Check file permissions

### Display/Visualization Issues

#### No Display Window Appears

**Solution**:

-   **Linux (remote server)**: Enable X11 forwarding: `ssh -X user@server`
-   **macOS**: Check that XQuartz is installed (if using X11)
-   **Windows**: Ensure OpenCV can create windows (may need display server)
-   Try running with `--record` flag to save to file instead

#### "Cannot connect to X server"

**Solution**:

-   Enable X11 forwarding: `ssh -X user@server`
-   Install X server software (XQuartz on macOS, Xming on Windows)
-   Use `--record` flag to save to file instead of displaying

#### Window Opens But Shows Black Screen

**Solution**:

-   Wait for events to accumulate (event cameras need movement)
-   Check that events are being processed (look for console output)
-   Verify input file has events
-   Try increasing brightness: `--brightness 5.0`

### Performance Issues

#### Processing is Very Slow

**Solution**:

1. Reduce FPS: `--fps 15`
2. Reduce events per frame: `--events-per-frame 5000`
3. Use smaller input files for testing
4. Close other applications to free up resources

#### High Memory Usage

**Solution**:

1. Process files in smaller chunks
2. Reduce buffer sizes in code (advanced)
3. Use `--record-comparison` mode which is more memory efficient

### Other Issues

#### "Permission denied" Errors

**Solution**:

-   Check file/directory permissions
-   Use `chmod` to change permissions (Linux/macOS)
-   Run with appropriate user permissions

#### Import Errors After Installation

**Solution**:

1. Ensure virtual environment is activated
2. Reinstall packages: `pip install --force-reinstall -r requirements.txt`
3. Verify Python version: `python3 --version` (should be 3.8+)

#### Scripts Not Found

**Solution**:

-   Ensure you're in the project root directory
-   Use full paths: `python /path/to/Code/frame_based_capture.py`
-   Check that files exist: `ls frame_based_capture.py`

### Getting Help

If you encounter issues not covered here:

1. Check the console output for error messages
2. Verify all prerequisites are installed
3. Test with sample data files first
4. Review the documentation in `docs/` directory
5. Check GitHub issues (if repository has issue tracking)

## Next Steps

After successful setup:

1. **Test with sample data**: Use the provided AEDAT4 files in `data/` directory
2. **Read documentation**: Check `docs/QUICK_START.md` for quick examples
3. **Explore options**: Try different DCE settings and parameters
4. **Record your own data**: Use `record_events.py` to capture new events
5. **Process your data**: Use `process_dual_pipeline.py` for batch processing

## Additional Resources

-   **Quick Start Guide**: `docs/QUICK_START.md`
-   **Frame-Based Capture Documentation**: `docs/FRAME_BASED_README.md`
-   **Comparison Mode Guide**: `docs/COMPARISON_MODE_SUMMARY.md`
-   **Implementation Details**: `docs/IMPLEMENTATION_SUMMARY.md`
-   **Main README**: `README.md`

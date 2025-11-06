# Quick Start Guide

## Installation

```bash
# Activate virtual environment
source .venv311/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Basic Usage

### View Pre-Recorded Data

```bash
python frame_based_capture.py --source file --file ./data/dvSave-2025_10_22_18_39_29.aedat4
```

### View Live Camera

```bash
python frame_based_capture.py --source camera
```

### Record to MP4

```bash
python frame_based_capture.py --source file \
    --file ./data/dvSave-2025_10_22_18_39_29.aedat4 \
    --record \
    --output ./output/my_video.mp4
```

### Custom DCE Settings

```bash
python frame_based_capture.py --source file \
    --file ./data/dvSave-2025_10_22_18_39_29.aedat4 \
    --shutter boxcar \
    --period 0.15 \
    --duty 0.3
```

### Record Comparison Videos (DCE vs No-DCE)

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

- `./output/my_test_with_dce.mp4` (with DCE applied)
- `./output/my_test_no_dce.mp4` (without DCE, all events weighted equally)

**Note**: Comparison mode disables the display window for maximum performance.

### Adjust Brightness

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
- `1.0` = normal brightness (default)
- `2.0` = twice as bright
- `3.0` = three times as bright
- etc.

## Controls

- **'q'**: Quit the application
- Close window: Exit application

## What You'll See

- **Red pixels**: Polarity 0 events (OFF events)
- **Green pixels**: Polarity 1 events (ON events)
- **Frame rate**: 30 fps (configurable)
- **DCE weighting**: Visual effect of Digital Coded Exposure applied

## Troubleshooting

**No display window appears:**

- Ensure you have X11 forwarding enabled (if on remote server)
- Check that OpenCV can create windows on your system

**"No module named 'cv2'":**

```bash
pip install opencv-python
```

**Camera not detected:**

- Check USB connection
- Run `python test_camera.py` to verify camera connection

**File not found:**

- Verify the path to your AEDAT4 file is correct
- Use absolute paths if relative paths don't work

## File Structure

```
.
├── frame_based_capture.py    # Main script
├── utils/                     # Utility classes
│   ├── event_processor.py    # DCE weighting
│   ├── frame_generator.py    # Frame creation
│   └── video_writer.py       # MP4 output
├── data/                      # Test data files
├── output/                    # Video output directory
└── requirements.txt           # Dependencies
```

## Configuration Options

| Option                | Values                           | Default                                    |
| --------------------- | -------------------------------- | ------------------------------------------ |
| `--source`            | `camera`, `file`                 | `camera`                                   |
| `--file`              | Path string                      | `./data/dvSave-2025_10_22_18_39_29.aedat4` |
| `--fps`               | Integer                          | `30`                                       |
| `--record`            | Flag                             | `False`                                    |
| `--record-comparison` | Flag                             | `False`                                    |
| `--output`            | Path string                      | `./output/recording.mp4`                   |
| `--shutter`           | `boxcar`, `morlet`, `no_shutter` | `boxcar`                                   |
| `--period`            | Float (seconds)                  | `0.1`                                      |
| `--duty`              | Float (0-1)                      | `0.25`                                     |
| `--brightness`        | Float                            | `1.0`                                      |

See `FRAME_BASED_README.md` for detailed documentation.

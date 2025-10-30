# Frame-Based Event Camera Capture with DCE

## Overview

This module implements a time-based frame generation system that converts event camera data into traditional 30fps frames using Digital Coded Exposure (DCE) weighting. It supports both live camera streaming and pre-recorded AEDAT4 files.

## Installation

1. Activate your virtual environment:

```bash
source .venv311/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

**From pre-recorded file:**

```bash
python frame_based_capture.py --source file --file ./data/dvSave-2025_10_22_18_39_29.aedat4
```

**From live camera:**

```bash
python frame_based_capture.py --source camera
```

### With MP4 Recording

```bash
python frame_based_capture.py --source file --file ./data/dvSave-2025_10_22_18_39_29.aedat4 --record --output ./output/my_recording.mp4
```

### With Custom DCE Parameters

**Boxcar shutter with custom period and duty cycle:**

```bash
python frame_based_capture.py --source file --file ./data/dvSave-2025_10_22_18_39_29.aedat4 --shutter boxcar --period 0.15 --duty 0.3
```

**Morlet wavelet shutter:**

```bash
python frame_based_capture.py --source file --file ./data/dvSave-2025_10_22_18_39_29.aedat4 --shutter morlet
```

### With Comparison Recording (DCE vs No-DCE)

Generate two videos simultaneously to compare the effects of DCE:

```bash
python frame_based_capture.py --source file --file ./data/dvSave-2025_10_22_18_42_06.aedat4 --record-comparison --output ./output/my_test.mp4 --shutter boxcar --period 0.1 --duty 0.25
```

This creates:

- `./output/my_test_with_dce.mp4` (with DCE applied)
- `./output/my_test_no_dce.mp4` (without DCE, all events weighted equally)

**Note**: Comparison mode disables the display window for maximum performance.

### Command Line Options

| Option                | Description                                                | Default                                  |
| --------------------- | ---------------------------------------------------------- | ---------------------------------------- |
| `--source`            | Input source: 'camera' or 'file'                           | camera                                   |
| `--file`              | Path to AEDAT4 file (if using file source)                 | ./data/dvSave-2025_10_22_18_39_29.aedat4 |
| `--fps`               | Target frames per second                                   | 30                                       |
| `--record`            | Enable MP4 recording                                       | False                                    |
| `--record-comparison` | Record two videos: one with DCE and one without            | False                                    |
| `--output`            | Output path for MP4 file                                   | ./output/recording.mp4                   |
| `--shutter`           | Shutter function type: 'boxcar', 'morlet', or 'no_shutter' | boxcar                                   |
| `--period`            | Period for boxcar shutter (seconds)                        | 0.1                                      |
| `--duty`              | Duty cycle for boxcar shutter (0-1)                        | 0.25                                     |

## Architecture

The system is organized into modular components:

### `utils/event_processor.py`

- **EventProcessor** class: Applies DCE weighting to events
- Implements boxcar and Morlet shutter functions
- Handles timestamp conversion (microseconds to seconds)

### `utils/frame_generator.py`

- **FrameGenerator** class: Creates 2D frames from events
- Time-based buffering (33.33ms windows for 30fps)
- Accumulates weighted events into pixel arrays
- Color mapping: polarity 0 → red, polarity 1 → green

### `utils/video_writer.py`

- **VideoWriter** class: Handles MP4 output
- Optional video recording using OpenCV
- Context manager support for safe resource cleanup

### `frame_based_capture.py`

- Main script that orchestrates the system
- Supports both live camera and file input
- Real-time OpenCV display
- Threading for data acquisition and frame generation
- Command-line interface

## How It Works

1. **Event Acquisition**: Events are read from camera or file and buffered
2. **Time-based Binning**: Events are grouped into 33.33ms windows (for 30fps)
3. **DCE Weighting**: Each event is weighted based on its timestamp using the configured shutter function
4. **Frame Accumulation**: Weighted events are accumulated into pixel arrays
5. **Normalization**: Frame values are normalized to 0-255 range
6. **Display/Record**: Frames are displayed in real-time and optionally written to MP4

## DCE Shutter Functions

### Boxcar Shutter

Periodic shutter that opens for a fraction of each period.

- **period**: Duration of one full cycle (seconds)
- **duty**: Fraction of time shutter is open (0-1)

### Morlet Wavelet Shutter

Continuous weighting function based on Morlet wavelet.

- **frequency**: Center frequency (Hz)
- **sigma**: Width parameter (seconds)

## Notes

- Frame resolution is automatically detected from camera or events
- Events are downsampled by default (50:1) for performance
- Press 'q' in the display window to quit
- MP4 recording is written frame-by-frame as events are processed

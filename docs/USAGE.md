# Usage Guide

Complete usage documentation for all scripts in the Event Camera Frame Capture system.

## Table of Contents

1. [Overview](#overview)
2. [frame_based_capture.py](#frame_based_capturepy)
3. [process_dual_pipeline.py](#process_dual_pipelinepy)
4. [record_events.py](#record_eventspy)
5. [Utility Scripts](#utility-scripts)
6. [Common Workflows](#common-workflows)

## Overview

This system provides three main scripts for processing event camera data:

- **frame_based_capture.py**: Real-time frame generation with DCE, supports live camera and file input
- **process_dual_pipeline.py**: Batch processing with dual pipelines (time-based and event-based)
- **record_events.py**: Record events from camera or file to AEDAT4 format

## frame_based_capture.py

Main script for frame-based event camera capture with Digital Coded Exposure (DCE). Generates video frames from event camera data (live or recorded) and supports real-time display and MP4 recording.

### Basic Usage

#### View Pre-Recorded Data

```bash
python src/frame_based_capture.py --source file --file ./data/dvSave-2025_10_22_18_39_29.aedat4
```

#### View Live Camera

```bash
python src/frame_based_capture.py --source camera
```

#### Record to MP4

```bash
python src/frame_based_capture.py --source file \
    --file ./data/dvSave-2025_10_22_18_39_29.aedat4 \
    --record \
    --output ./output/videos/my_video.mp4
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
| `--use-event-time`        | flag                             | `False`                                    | **CRITICAL**: Generate frames based on event timestamps (use for file processing) |
| `--no-pacing`              | flag                             | `False`                                    | Process file as fast as possible (optimization)                    |

### Usage Examples

#### Custom DCE Settings (Boxcar Shutter)

```bash
python src/frame_based_capture.py --source file \
    --file ./data/dvSave-2025_10_22_18_39_29.aedat4 \
    --shutter boxcar \
    --period 0.15 \
    --duty 0.3
```

#### Morlet Wavelet Shutter

```bash
python src/frame_based_capture.py --source file \
    --file ./data/dvSave-2025_10_22_18_39_29.aedat4 \
    --shutter morlet
```

#### Record Comparison Videos (DCE vs No-DCE)

Generate two videos simultaneously to compare the effect of DCE:

```bash
python src/frame_based_capture.py \
    --source file \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --record-comparison \
    --output ./output/videos/my_test.mp4 \
    --shutter boxcar \
    --period 0.1 \
    --duty 0.25
```

This creates:
- `./output/videos/my_test_with_dce.mp4` (with DCE applied)
- `./output/videos/my_test_no_dce.mp4` (without DCE, all events weighted equally)

**Note**: Comparison mode disables the display window for maximum performance.

#### Adjust Brightness

Increase the brightness of event dots:

```bash
python src/frame_based_capture.py \
    --source file \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --record \
    --output ./output/videos/bright.mp4 \
    --brightness 2.0
```

Brightness values:
- `1.0` = normal brightness
- `2.0` = twice as bright
- `3.0` = three times as bright
- Higher values make events more visible

#### Enable Adaptive Decay

Automatically adjust decay rate based on scene activity:

```bash
python src/frame_based_capture.py \
    --source file \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --record \
    --output ./output/videos/adaptive.mp4 \
    --enable-adaptive-decay \
    --min-decay 0.99 \
    --max-decay 0.3 \
    --low-activity 5000 \
    --high-activity 40000
```

#### Custom Frame Rate

```bash
python src/frame_based_capture.py \
    --source file \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --fps 60 \
    --record \
    --output ./output/videos/60fps.mp4
```

#### File Processing with Correct Timing (IMPORTANT)

**Always use `--use-event-time` when processing files** to ensure video duration matches recording duration:

```bash
python src/frame_based_capture.py \
    --source file \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --record-comparison \
    --output ./output/videos/my_video.mp4 \
    --use-event-time \
    --no-pacing
```

Without `--use-event-time`, videos will be longer than the actual recording (frames generated based on processing time, not event timestamps).

### Controls

- **'q'**: Quit the application
- **Close window**: Exit application
- **Ctrl+C**: Stop recording (in comparison mode)

### Output

- **Red pixels**: Polarity 0 events (OFF events)
- **Green pixels**: Polarity 1 events (ON events)
- **Frame rate**: Configurable (default 30 fps)
- **DCE weighting**: Visual effect of Digital Coded Exposure applied

### Architecture

The system is organized into modular components:

- **`utils/event_processor.py`**: Applies DCE weighting to events
- **`utils/frame_generator.py`**: Creates 2D frames from events
- **`utils/video_writer.py`**: Handles MP4 output
- **`frame_based_capture.py`**: Main orchestration script

### How It Works

1. **Event Acquisition**: Events are read from camera or file and buffered
2. **Time-based Binning**: Events are grouped into time windows (e.g., 33.33ms for 30fps)
3. **DCE Weighting**: Each event is weighted based on its timestamp using the configured shutter function
4. **Frame Accumulation**: Weighted events are accumulated into pixel arrays
5. **Normalization**: Frame values are normalized to 0-255 range
6. **Display/Record**: Frames are displayed in real-time and optionally written to MP4

### DCE Shutter Functions

#### Boxcar Shutter

Periodic shutter that opens for a fraction of each period.

- **period**: Duration of one full cycle (seconds)
- **duty**: Fraction of time shutter is open (0-1)

#### Morlet Wavelet Shutter

Continuous weighting function based on Morlet wavelet.

- **frequency**: Center frequency (Hz)
- **sigma**: Width parameter (seconds)

## process_dual_pipeline.py

Process events from AEDAT4 file through two pipelines simultaneously:

1. **Time-based**: Generate frames at fixed FPS intervals
2. **Event-based**: Generate frames after accumulating N events

Outputs frames as JPEG images in separate directories.

### Basic Usage

```bash
python src/process_dual_pipeline.py \
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
python src/process_dual_pipeline.py \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --output-dir ./output/dual_pipeline/
```

This creates:
- `./output/dual_pipeline/time_based/` - Time-based frames (frame_0001.jpg, frame_0002.jpg, ...)
- `./output/dual_pipeline/event_based/` - Event-based frames (frame_0001.jpg, frame_0002.jpg, ...)

#### Custom FPS and Events Per Frame

```bash
python src/process_dual_pipeline.py \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --fps 60 \
    --events-per-frame 5000 \
    --output-dir ./output/custom/
```

#### Custom DCE Settings

```bash
python src/process_dual_pipeline.py \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --shutter boxcar \
    --period 0.15 \
    --duty 0.3 \
    --brightness 2.0 \
    --output-dir ./output/custom_dce/
```

#### High Quality JPEG Output

```bash
python src/process_dual_pipeline.py \
    --file ./data/dvSave-2025_10_22_18_42_06.aedat4 \
    --jpeg-quality 95 \
    --output-dir ./output/high_quality/
```

#### Morlet Wavelet Shutter

```bash
python src/process_dual_pipeline.py \
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

- Processing speed depends on file size and number of events
- Progress is reported every 100,000 events
- Final statistics show total frames generated and processing time

## record_events.py

Records events from camera or file to AEDAT4 format for later processing.

### Basic Usage

#### Record from Camera

```bash
python src/record_events.py --source camera --output-dir ./data/
```

#### Copy File to Output Directory

```bash
python src/record_events.py --source file \
    --file ./data/input.aedat4 \
    --output-dir ./data/
```

### Command-Line Options

| Option                  | Type            | Default     | Description                                                      |
| ----------------------- | --------------- | ----------- | ----------------------------------------------------------------- |
| `--source`              | `camera`, `file` | `camera`    | Input source: camera or file                                      |
| `--file`                | string          | `./data/test.aedat4` | Path to input AEDAT4 file (if using file source)                |
| `--output-dir`           | string          | `./data/`   | Output directory for recorded files                               |
| `--no-preview`           | flag            | `False`     | Disable preview window                                            |
| `--no-noise-filter`      | flag            | `False`     | Disable background activity noise filter (default: enabled)        |
| `--noise-filter-period`  | float           | `1.0`       | Noise filter activity period in milliseconds (default: 1.0ms)     |

### Usage Examples

#### Record with Preview

```bash
python src/record_events.py --source camera --output-dir ./data/
```

Press 'q' to stop recording. Output file will be automatically named with timestamp: `dvSave-YYYY_MM_DD_HH_MM_SS.aedat4`

#### Record without Preview (Faster)

```bash
python src/record_events.py --source camera --output-dir ./data/ --no-preview
```

#### Custom Noise Filter Settings

```bash
python src/record_events.py --source camera \
    --output-dir ./data/ \
    --noise-filter-period 2.0
```

## Utility Scripts

### scripts/aedat_to_mp4.py

Converts AEDAT4 event camera files to MP4 video files. Supports both time-based and event-based frame generation.

### scripts/check_video_fps.py

Diagnostic tool to check the actual FPS metadata of MP4 video files.

**Usage:**

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

### scripts/create_timestamp_based_frames.py

Helper script to analyze event timestamp distribution in AEDAT4 files, useful for diagnosing timing issues.

**Usage:**

```bash
python scripts/create_timestamp_based_frames.py path/to/file.aedat4
```

This shows the actual event time span and expected video duration.

### scripts/setup_camera.py

Camera setup helper script for testing camera connections.

## Common Workflows

### Workflow 1: Record and Process Events

1. **Record events from camera:**
   ```bash
   python src/record_events.py --source camera --output-dir ./data/
   ```

2. **Process recorded file with DCE:**
   ```bash
   python src/frame_based_capture.py \
       --source file \
       --file ./data/dvSave-YYYY_MM_DD_HH_MM_SS.aedat4 \
       --record \
       --output ./output/videos/processed.mp4 \
       --use-event-time \
       --no-pacing
   ```

### Workflow 2: Comparison Analysis

Generate side-by-side comparison videos:

```bash
python src/frame_based_capture.py \
    --source file \
    --file ./data/recording.aedat4 \
    --record-comparison \
    --output ./output/comparison.mp4 \
    --shutter boxcar \
    --period 0.1 \
    --duty 0.25 \
    --use-event-time \
    --no-pacing
```

### Workflow 3: Batch Processing with Dual Pipeline

Process file through both time-based and event-based pipelines:

```bash
python src/process_dual_pipeline.py \
    --file ./data/recording.aedat4 \
    --output-dir ./output/batch/ \
    --fps 30 \
    --events-per-frame 10000
```

### Workflow 4: Verify Video Timing

After processing, verify the video FPS and duration:

```bash
python scripts/check_video_fps.py ./output/videos/my_video.mp4 --expected-fps 30
```

## Notes

- Frame resolution is automatically detected from camera or events
- Events are downsampled by default (50:1) for performance in camera mode
- Press 'q' in display windows to quit
- MP4 recording is written frame-by-frame as events are processed
- Always use `--use-event-time` when processing files to ensure correct video duration


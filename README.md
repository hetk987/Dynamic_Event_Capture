# Event Camera Frame Capture with Digital Coded Exposure (DCE)

A Python-based system for processing event camera data (DVXplorer) into traditional video frames using Digital Coded Exposure (DCE) techniques. Supports both live camera streaming and pre-recorded AEDAT4 files.

## Features

-   **Real-time frame generation** from event camera data at configurable FPS (default 30fps)
-   **Digital Coded Exposure (DCE)** with multiple shutter functions (boxcar, Morlet, no shutter)
-   **Live camera support** via DVXplorer camera
-   **File playback** from pre-recorded AEDAT4 files
-   **Video recording** to MP4 format
-   **Comparison mode** to generate side-by-side videos with/without DCE
-   **Adaptive decay** for dynamic scene activity adjustment
-   **Dual pipeline processing** for time-based and event-based frame generation

## Quick Start

### Installation

For complete setup instructions, see **[SETUP.md](docs/SETUP.md)**.

Quick installation:

```bash
# Clone the repository
git clone https://github.com/hetk987/Code.git
cd Code

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install dv  # Additional package for file reading
```

### Basic Usage

**View pre-recorded data:**

```bash
python frame_based_capture.py --source file --file ./data/dvSave-2025_10_22_18_39_29.aedat4
```

**View live camera:**

```bash
python frame_based_capture.py --source camera
```

**Record to MP4:**

```bash
python frame_based_capture.py --source file \
    --file ./data/dvSave-2025_10_22_18_39_29.aedat4 \
    --record \
    --output ./output/my_video.mp4
```

For more detailed usage examples, see [docs/QUICK_START.md](docs/QUICK_START.md).

## Project Structure

```
.
├── frame_based_capture.py    # Main frame-based capture script
├── record_events.py          # Event recording to AEDAT4 format
├── process_dual_pipeline.py  # Dual pipeline processing (time + event-based)
├── utils/                    # Utility modules
│   ├── frame_generator.py    # Frame generation from events
│   ├── event_based_generator.py  # Event-based frame generation
│   ├── event_processor.py    # DCE event processing
│   ├── video_writer.py       # MP4 video output
│   └── adaptive_decay.py     # Adaptive decay controller
├── scripts/                  # Utility scripts
│   └── setup_camera.py       # Camera setup helper
├── tests/                    # Test scripts
│   ├── test_camera.py        # Camera connection test
│   └── test_visualization.py # Visualization test
├── docs/                     # Documentation
│   ├── SETUP.md              # Complete setup guide
│   ├── QUICK_START.md        # Quick start guide
│   ├── FRAME_BASED_README.md # Frame-based capture documentation
│   ├── COMPARISON_MODE_SUMMARY.md  # Comparison mode docs
│   └── IMPLEMENTATION_SUMMARY.md   # Implementation details
├── archive/                  # Old/experimental scripts
│   ├── Dynamic_Frames_With_DCA.py  # Old visualization script
│   └── Plot_wDCE.py          # Old plotting script
├── data/                     # Input data files (AEDAT4)
├── output/                   # Output videos and frames
└── requirements.txt          # Python dependencies
```

## Main Scripts

### `frame_based_capture.py`

Main script for frame-based event camera capture with DCE. Supports live camera and file input, real-time display, and MP4 recording.

**Key features:**

-   Time-based frame generation at configurable FPS
-   Multiple DCE shutter functions
-   Adaptive decay based on scene activity
-   Comparison mode for DCE vs no-DCE videos

### `record_events.py`

Records events from camera or file to AEDAT4 format for later processing.

### `process_dual_pipeline.py`

Processes events through two pipelines simultaneously:

-   **Time-based**: Generates frames at fixed FPS intervals
-   **Event-based**: Generates frames after accumulating N events

Outputs frames as JPEG images in separate directories.

## Documentation

-   **[Setup Guide](docs/SETUP.md)** - Complete setup instructions (git clone, environment, installation)
-   **[Quick Start Guide](docs/QUICK_START.md)** - Get started quickly
-   **[Frame-Based Capture](docs/FRAME_BASED_README.md)** - Detailed documentation for frame-based capture
-   **[Comparison Mode](docs/COMPARISON_MODE_SUMMARY.md)** - Comparison mode documentation
-   **[Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md)** - Technical implementation details

## Requirements

-   Python 3.8+
-   dv-processing (for camera support)
-   opencv-python (for video processing)
-   numpy
-   vispy (for visualization, optional)

See `requirements.txt` for complete list.

## Testing

Test camera connection:

```bash
python tests/test_camera.py
```

## License

[Add your license here]

## Author

[Add your name/contact here]

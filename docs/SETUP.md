# Setup Guide

Complete setup instructions for the Event Camera Frame Capture with Digital Coded Exposure (DCE) project.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Git Clone](#git-clone)
3. [Python Environment Setup](#python-environment-setup)
4. [Package Installation](#package-installation)
5. [Verification](#verification)
6. [Next Steps](#next-steps)

## Prerequisites

### Required Software

-   **Python 3.8 to 3.12** (Python 3.13 and higher are not supported)

    -   Check your version: `python3 --version` or `python --version`
    -   Download from: https://www.python.org/downloads/
    -   **Important**: Python 3.13+ is not compatible with this project. Use Python 3.12 or lower.

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
git clone https://github.com/hetk987/Code.git

# Navigate to the project directory
cd Code
```

### Verify Repository Structure

After cloning, you should see the following structure:

```
Code/
├── README.md
├── requirements.txt
├── src/                      # Main application scripts
│   ├── frame_based_capture.py
│   ├── record_events.py
│   └── process_dual_pipeline.py
├── utils/                    # Utility modules
├── tests/                    # Test scripts
├── scripts/                  # Utility scripts
├── docs/                     # Documentation
├── data/                     # Input data files (AEDAT4)
└── output/                   # Output videos and frames
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
python src/frame_based_capture.py --source file --file ./data/dvSave-2025_10_22_18_39_29.aedat4
```

If everything is set up correctly, you should see a window displaying event camera frames.

## Next Steps

After successful setup:

1. **Read the documentation**: Check [USAGE.md](USAGE.md) for detailed usage instructions
2. **Test with sample data**: Use the provided AEDAT4 files in `data/` directory
3. **Explore options**: Try different DCE settings and parameters
4. **Record your own data**: Use `src/record_events.py` to capture new events
5. **Process your data**: Use `src/process_dual_pipeline.py` for batch processing

## Additional Resources

-   **[Usage Guide](USAGE.md)** - Complete usage documentation for all scripts
-   **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions
-   **[Main README](../README.md)** - Project overview and quick start

# Real-time DVXplorer visualization with Digital Coded Exposure (DCE)
# Visualize event camera data with VisPy and apply Digital Coded Exposure

from re import A
import dv_processing as dv
import vispy
vispy.use('Glfw')
from vispy import scene
from vispy.scene import visuals
from vispy.scene.visuals import Text
from vispy.app import run
import numpy as np
import time
import threading
from collections import deque

# Camera settings
DOWNSAMPLING = 50   # Reduce for more data, increase for better performance
BUFFER_SIZE = 50000  # Number of events to keep in buffer
UPDATE_INTERVAL = 0.1  # Update visualization every 100ms

# Buffer and visualization settings
EVENTS_PER_PLOT = 1000  # Number of events to accumulate before plotting
BUFFER_CLEAR_SIZE = 5000  # Number of events that triggers buffer clearing

# Frame management settings
MAX_FRAMES = 0  # Maximum number of frames to keep in history
FRAME_SPACING = 25  # Spacing between frames in z-axis

# DCE Settings
SHUTTER_TYPE = 'boxcar'  # or 'morlet'
BOXCAR_PERIOD = 0.1      # seconds
BOXCAR_DUTY = 0.25       # 25% duty cycle
MORLET_FREQ = 100.0      # Hz
MORLET_SIGMA = 0.01      # seconds

# --- Digital Coded Exposure Functions ---
def boxcar_shutter(t, period=0.1, duty=0.25, phase=0.0):
    """Boxcar shutter: open for duty*period, closed otherwise."""
    t_mod = (t - phase) % period
    return 1.0 if t_mod < duty * period else 0.0

def morlet_shutter(t, f=100.0, sigma=0.01):
    """Morlet wavelet shutter centered at frequency f [Hz]."""
    return np.exp(-0.5 * (t/sigma)**2) * np.cos(2*np.pi*f*t)

# Global data buffers for real-time streaming
event_buffer = deque(maxlen=BUFFER_SIZE)
frame_buffer = deque(maxlen=MAX_FRAMES)  # Store recent frames
data_lock = threading.Lock()
running = True

def process_frame(events):
    """Process a batch of events into a frame"""
    # Convert to numpy arrays efficiently
    events_array = np.array([(e['x'], e['y'], e['polarity']) 
                          for e in events],
                          dtype=[('x', 'i4'), ('y', 'i4'), ('polarity', 'i4')])
    
    # Get unique positions and calculate polarities
    unique_positions, indices = np.unique(
        events_array[['x', 'y']], 
        return_inverse=True
    )
    
    # Calculate average polarity for each position
    polarities = events_array['polarity'].astype(float)
    position_counts = np.bincount(indices)
    polarity_sums = np.bincount(indices, weights=polarities)
    avg_polarities = polarity_sums / position_counts
    
    return {
        'positions': unique_positions,
        'polarities': avg_polarities,
        'timestamp': time.time()
    }

def stream_camera_data():
    """Stream data from DVXplorer camera"""
    global event_buffer, running
    
    try:
        # Open camera
        print("Opening camera...")
        capture = dv.io.camera.open()
        
        print(f"Connected to camera: {capture.getCameraName()}")
        
        if capture.isEventStreamAvailable():
            resolution = capture.getEventResolution()
            print(f"Event resolution: {resolution[0]}x{resolution[1]}")
        
        print("Starting real-time data streaming...")
        print("Move something in front of the camera to generate events!")
        
        event_count = 0
        batch_count = 0
        
        while running:
            # Get next batch of events
            events = capture.getNextEventBatch()
            
            if events is not None and len(events) > 0:
                batch_count += 1
                event_count += len(events)
                
                # Print status every 10 batches
                if batch_count % 10 == 0:
                    print(f"Received batch {batch_count}: {len(events)} events (total: {event_count})")
                
                # Convert to numpy array
                events_np = events.numpy()
                
                # Downsample for performance
                if len(events_np) > DOWNSAMPLING:
                    events_np = events_np[::DOWNSAMPLING]
                
                timestamps = events_np['timestamp']
                x_coords = events_np['x']
                y_coords = events_np['y']
                polarities = events_np['polarity']
                
                with data_lock:
                    # Add new events to buffer
                    for i in range(len(timestamps)):
                        event_buffer.append({
                            'timestamp': timestamps[i],
                            'x': x_coords[i],
                            'y': y_coords[i],
                            'polarity': polarities[i]
                        })
            
            time.sleep(0.001)  # Small delay to prevent busy waiting
                        
    except Exception as e:
        print(f"Error connecting to camera: {e}")
        print("Make sure your DVXplorer camera is connected via USB")
        running = False

def process_events():
    """Process events from buffer and return visualization data with DCE applied"""
    global event_buffer, frame_buffer
    
    with data_lock:
        if len(event_buffer) < EVENTS_PER_PLOT:
            return None, None
            
        events_list = list(event_buffer)
        if len(event_buffer) >= BUFFER_CLEAR_SIZE:
            frame = process_frame(events_list)
            frame_buffer.append(frame)
            event_buffer.clear()
    
    if len(events_list) == 0:
        return None, None
    
    # Convert events to numpy arrays for efficient processing
    events_array = np.array([(e['timestamp'], e['x'], e['y'], e['polarity']) 
                            for e in events_list],
                           dtype=[('timestamp', 'f8'), ('x', 'i4'), 
                                 ('y', 'i4'), ('polarity', 'i4')])
    
    # Normalize timestamps to seconds relative to the first event
    t0 = events_array['timestamp'][0]
    timestamps = (events_array['timestamp'] - t0) * 1e-6  # Convert microseconds to seconds
    
    # Apply DCE shutter function
    if SHUTTER_TYPE == 'boxcar':
        weights = np.array([boxcar_shutter(t, BOXCAR_PERIOD, BOXCAR_DUTY) 
                          for t in timestamps])
    else:  # morlet
        weights = np.array([morlet_shutter(t, MORLET_FREQ, MORLET_SIGMA) 
                          for t in timestamps])
    
    # Filter out events where weight is zero or very small
    mask = weights > 0.01
    if not np.any(mask):
        return None, None
    
    # Create points array with weighted events
    points = np.column_stack((
        events_array['x'][mask],
        events_array['y'][mask],
        np.zeros_like(events_array['x'][mask])
    ))
    
    # Create colors with alpha channel modulated by weights
    colors = np.zeros((len(points), 4))
    polarities = events_array['polarity'][mask]
    weights_masked = weights[mask]
    
    # Red for polarity 0, Green for polarity 1, with weighted alpha
    colors[polarities == 0] = [1.0, 0.0, 0.0, 0.8]
    colors[polarities == 1] = [0.0, 1.0, 0.0, 0.8]
    colors[:, 3] *= weights_masked  # Modify alpha channel by weights
    
    all_points = [points]
    all_colors = [colors]
    
    # Add historical frames with decreasing alpha
    for z_index, frame in enumerate(frame_buffer, start=1):
        frame_points = np.column_stack((
            frame['positions']['x'],
            frame['positions']['y'],
            np.full(len(frame['positions']), z_index * FRAME_SPACING)
        ))
        
        frame_colors = np.zeros((len(frame['polarities']), 4))
        frame_colors[frame['polarities'] == 0] = [1.0, 0.0, 0.0, 0.8]
        frame_colors[frame['polarities'] == 1] = [0.0, 1.0, 0.0, 0.8]
        # Reduce alpha for older frames
        frame_colors[:, 3] *= 0.8 ** z_index
        
        all_points.append(frame_points)
        all_colors.append(frame_colors)
    
    if not all_points:
        return None, None
        
    points = np.vstack(all_points)
    colors = np.vstack(all_colors)
    
    return points, colors

# --- Real-time Visualization with VisPy ---
canvas = scene.SceneCanvas(keys='interactive', show=True, bgcolor='black',
                           size=(1200, 800), title='Real-time DVXplorer Events with Digital Coded Exposure')

view = canvas.central_widget.add_view()

# Scatter plot (will be updated in real-time)
scatter = visuals.Markers()
# Initialize with dummy data to avoid bounds error
scatter.set_data(np.array([[0, 0, 0]]), face_color='white', size=1)
view.add(scatter)

# XYZ axis with labels
scale_factor = 0.1
xyz_axis = visuals.XYZAxis(parent=view.scene)
xyz_axis.transform = vispy.visuals.transforms.STTransform(scale=(100*scale_factor, 100*scale_factor, 100*scale_factor))

# Text labels for axes
# text_x = Text("Time (s)", color='red', font_size=10000, pos=[100, 0, 0], parent=view.scene)
# text_y = Text("X", color='green', font_size=10000, pos=[0, 100, 0], parent=view.scene)
# text_z = Text("Y", color='blue', font_size=10000, pos=[0, 0, 100], parent=view.scene)

# # Status text
# status_text = Text("Connecting to camera...", color='white', font_size=8000, 
#                    pos=[50, 50, 50], parent=view.scene)

# 3D camera with interactive controls
view.camera = scene.cameras.TurntableCamera(fov=30, elevation=0, azimuth=0)

# Center camera on the middle of the sensor
view.camera.distance = 100  # Initial camera distance

# Set up camera ranges for better interaction
view.camera.set_range(x=(-500, 500), y=(-12, 36), z=(6, 42))

# Enable interactive features
view.interactive = True  # Enable all interactive features at once

update_count = 0

def update_visualization():
    """Update the visualization with new data"""
    global running, update_count
    
    update_count += 1
    
    points, colors = process_events()
    
    if points is not None and len(points) > 0:
        # Debug output every 10 updates
        if update_count % 10 == 0:
            print(f"Visualization update {update_count}: Displaying {len(points)} points, buffer has {len(event_buffer)} events")
        
        min_vals = points.min(axis=0)
        max_vals = points.max(axis=0)
        center = (min_vals + max_vals) / 2
        
        # Optionally, calculate the span and set distance
        span = np.linalg.norm(max_vals - min_vals)
        distance = span * scale_factor * 2  # Adjust multiplier as needed

        # Update camera
        view.camera.center = center * scale_factor
        view.camera.distance = distance

        # Update scatter plot with fixed size for better performance
        scatter.set_data(points*scale_factor, face_color=colors, size=3, edge_color=None)
        
        # Update axis scaling only on significant changes
        if points.max() > 0:
            max_vals = points.max(axis=0)
            xyz_axis.transform = vispy.visuals.transforms.STTransform(
                translate=(0, 0, 0), scale=(max_vals[0]*scale_factor, max_vals[1]*scale_factor, max_vals[2]*scale_factor)
            )
    else:
        if update_count % 20 == 0:
            print(f"Visualization update {update_count}: No events yet, buffer size: {len(event_buffer)}")
    
    # Schedule next update
    if running:
        canvas.update()

def on_close(event):
    """Handle window close event"""
    global running
    running = False
    print("Stopping camera stream...")

# Connect close event
canvas.events.close.connect(on_close)

print("=" * 50)
print("Initializing Real-time DVXplorer Visualization")
print("=" * 50)

# Start camera streaming thread
print("Starting camera thread...")
camera_thread = threading.Thread(target=stream_camera_data, daemon=True)
camera_thread.start()
print("Camera thread started")

# Setup timer for updates
print("Setting up visualization timer...")
timer = vispy.app.Timer(UPDATE_INTERVAL, connect=lambda e: update_visualization())
timer.start()
print("Timer started")

print("\n" + "=" * 50)
print("Visualization window opened!")
print("Wave your hand in front of the camera to see events")
print("Press Ctrl+C or close the window to stop")
print("=" * 50 + "\n")

run()

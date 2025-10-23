# Real-time DVXplorer visualization with Digital Coded Exposure (DCE)
# Visualize event camera data with VisPy and apply Digital Coded Exposure

import dv_processing as dv
import vispy
from vispy import scene
from vispy.scene import visuals
from vispy.scene.visuals import Text
from vispy.app import run
import numpy as np
import time
import threading
from collections import deque

# Camera settings
DOWNSAMPLING = 10   # Reduce for more data, increase for better performance
BUFFER_SIZE = 50000  # Number of events to keep in buffer
UPDATE_INTERVAL = 0.1  # Update visualization every 100ms

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
data_lock = threading.Lock()
running = True

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
    """Process events from buffer and return visualization data"""
    global event_buffer
    
    with data_lock:
        if len(event_buffer) == 0:
            return None, None, None
            
        # Convert buffer to lists
        events_list = list(event_buffer)
    
    if len(events_list) == 0:
        return None, None, None
    
    # Extract data from events
    t = np.array([e['timestamp'] for e in events_list])
    x = np.array([e['x'] for e in events_list])
    y = np.array([e['y'] for e in events_list])
    polarity = np.array([e['polarity'] for e in events_list])
    
    # Convert timestamps to seconds
    t = t / 1e6
    
    # Normalize and scale time axis for better visibility
    if t.max() > t.min():
        t_scaled = (t - t.min()) * 500
    else:
        t_scaled = t * 0
    
    # Flip x and y axis to match footage
    if x.max() > 0:
        x = x.max() - x
    if y.max() > 0:
        y = y.max() - y
    
    # --- Apply Digital Coded Exposure ---
    # Map polarity to ±1
    polarity_signed = np.where(polarity > 0, 1, -1)
    
    # Choose shutter function
    period = 0.1   # seconds
    duty = 0.25    # 25% duty cycle
    shutter_vals = np.array([boxcar_shutter(tt, period, duty) for tt in t])
    
    weighted_polarity = polarity_signed * shutter_vals
    
    # Stack into 3D points
    points = np.column_stack((t_scaled, x, y))
    
    # Color by weighted polarity
    red   = [1.0, 0.0, 0.0, 1.0]  # negative
    green = [0.0, 1.0, 0.0, 1.0]  # positive
    colors = np.array([
        green if wp > 0 else red if wp < 0 else [0.5, 0.5, 0.5, 0.3]
        for wp in weighted_polarity
    ])
    
    return points, colors, (t_scaled, x, y)

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

# 3D camera
view.camera = scene.cameras.TurntableCamera(fov=45, elevation=30, azimuth=60)
view.camera.set_range()

update_count = 0

def update_visualization():
    """Update the visualization with new data"""
    global running, update_count
    
    update_count += 1
    
    points, colors, ranges = process_events()
    
    if points is not None and len(points) > 0:
        # Debug output every 10 updates
        if update_count % 10 == 0:
            print(f"Visualization update {update_count}: Displaying {len(points)} points, buffer has {len(event_buffer)} events")
        
        # Update scatter plot
        scatter.set_data(points*scale_factor, face_color=colors, size=3, edge_color=None)
        
        # Update axis scaling
        t_scaled, x, y = ranges
        if t_scaled.max() > 0 and x.max() > 0 and y.max() > 0:
            xyz_axis.transform = vispy.visuals.transforms.STTransform(
                translate=(0, 0, 0), scale=(t_scaled.max()*scale_factor, x.max()*scale_factor, y.max()*scale_factor)
            )
            
            # Update text positions
            text_x.pos = [t_scaled.max() + 50, 0, 0]
            text_y.pos = [0, x.max() + 50, 0]
            text_z.pos = [0, 0, y.max() + 50]
            
            # Update status
            status_text.text = f"Events: {len(points)} | Buffer: {len(event_buffer)}/{BUFFER_SIZE}"
            status_text.pos = [t_scaled.max() / 2, -50, -50]
            
            # Auto-fit camera to data
            view.camera.set_range()
    else:
        if update_count % 20 == 0:
            print(f"Visualization update {update_count}: No events yet, buffer size: {len(event_buffer)}")
        status_text.text = "Waiting for events... (move something in front of camera)"
        status_text.pos = [100, 100, 0]
    
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

# pca_1_vispy_dce_fixed.py
# Visualize event camera data with VisPy and apply Digital Coded Exposure (DCE)

import dv
import vispy
from vispy import scene
from vispy.scene import visuals
from vispy.scene.visuals import Text
from vispy.app import run
import numpy as np

# Change this to your own directory
datapath = r'./data/dvSave-2025_10_22_18_39_29.aedat4'

DOWNSAMPLING = 10   # 10, 100, 1_000, 10_000, 100_000
MAXIMUM = 1_000_000

# --- Digital Coded Exposure Functions ---
def boxcar_shutter(t, period=0.1, duty=0.25, phase=0.0):
    """Boxcar shutter: open for duty*period, closed otherwise."""
    t_mod = (t - phase) % period
    return 1.0 if t_mod < duty * period else 0.0

def morlet_shutter(t, f=100.0, sigma=0.01):
    """Morlet wavelet shutter centered at frequency f [Hz]."""
    return np.exp(-0.5 * (t/sigma)**2) * np.cos(2*np.pi*f*t)

with dv.AedatFile(datapath) as f:
    events = np.hstack([packet for packet in f['events'].numpy()])
    t, x, y, polarity = events['timestamp'], events['x'], events['y'], events['polarity']

    # Downsampling and limiting
    t, x, y, polarity = t[::DOWNSAMPLING], x[::DOWNSAMPLING], y[::DOWNSAMPLING], polarity[::DOWNSAMPLING]
    t, x, y, polarity = t[:MAXIMUM], x[:MAXIMUM], y[:MAXIMUM], polarity[:MAXIMUM]
    print(f"Downsampling: {DOWNSAMPLING}")
    print(f"Maximum: {MAXIMUM}")
    print(f"Plotted {len(t)} events!")
    print(f"t range: {t.min()} - {t.max()}")
    print(f"x range: {x.min()} - {x.max()}")
    print(f"y range: {y.min()} - {y.max()}")
    print(f"Polarity values: {np.unique(polarity)}")

    # Convert timestamps to seconds
    t = t / 1e6

    # Normalize and scale time axis for better visibility
    t_scaled = (t - t.min()) * 500

    # Flip x and y axis to match footage
    x = x.max() - x
    y = y.max() - y

    # --- Apply Digital Coded Exposure ---
    # Map polarity to ±1
    polarity_signed = np.where(polarity > 0, 1, -1)

    # Choose shutter function
    period = 0.1   # seconds
    duty = 0.25    # 25% duty cycle
    shutter_vals = np.array([boxcar_shutter(tt, period, duty) for tt in t])
    # shutter_vals = np.array([morlet_shutter(tt, f=100.0, sigma=0.01) for tt in t])  # alternative

    weighted_polarity = polarity_signed * shutter_vals

    # Stack into 3D points
    points = np.column_stack((t_scaled, x, y))

    # Color by weighted polarity
    red   = [1.0, 0.0, 0.0, 1.0]  # negative
    green = [0.0, 1.0, 0.0, 1.0]  # positive
    colors = np.array([
        green if wp > 0 else red if wp < 0 else [0, 0, 0, 0]
        for wp in weighted_polarity
    ])

# --- Visualization with VisPy ---
canvas = scene.SceneCanvas(keys='interactive', show=True, bgcolor='black',
                           size=(1200, 800), title='Events in 3D with Digital Coded Exposure')

view = canvas.central_widget.add_view()

# Scatter plot
scatter = visuals.Markers()
scatter.set_data(points, face_color=colors, size=5, edge_color=None)
view.add(scatter)

# XYZ axis with labels
xyz_axis = visuals.XYZAxis(parent=view.scene)
xyz_axis.transform = vispy.visuals.transforms.STTransform(
    translate=(0, 0, 0), scale=(t_scaled.max(), x.max(), y.max())
)
text_x = Text("Time (s)", color='red', font_size=10000, pos=[t_scaled.max() + 50, 0, 0], parent=view.scene)
text_y = Text("X", color='green', font_size=10000, pos=[0, x.max() + 50, 0], parent=view.scene)
text_z = Text("Y", color='blue', font_size=10000, pos=[0, 0, y.max() + 50], parent=view.scene)

# Axis ticks
test_origin = Text("0.0", color='white', font_size=5000, pos=[-10, -10, -10], parent=view.scene)
for i in np.arange(0, t_scaled.max() - 1, (t_scaled.max() - 1) / 4):
    Text(f"{(i + t_scaled.max() - 1) / 4 / 500:.1f}", color='white', font_size=5000,
         pos=[i + (t_scaled.max() - 1) / 4, -10, -10], parent=view.scene)
for j in np.arange(0, x.max() - 1, (x.max() - 1) / 4):
    Text(f"{j + (x.max() - 1) / 4:.1f}", color='white', font_size=5000,
         pos=[-10, j + (x.max() - 1) / 4, -10], parent=view.scene)
for k in np.arange(0, y.max() - 1, (y.max() - 1) / 4):
    Text(f"{k + (y.max() - 1) / 4:.1f}", color='white', font_size=5000,
         pos=[-10, -10, k + (y.max() - 1) / 4], parent=view.scene)

# 3D camera
view.camera = scene.cameras.TurntableCamera(fov=45, elevation=30, azimuth=60)
view.camera.set_range()

run()

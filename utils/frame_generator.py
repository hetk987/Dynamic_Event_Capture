"""
FrameGenerator: Creates 2D frames from events using time-based buffering
"""
import numpy as np
from .event_processor import EventProcessor


class FrameGenerator:
    """Generate 30fps frames from event data using time-based buffering"""
    
    def __init__(self, width, height, fps=30, 
                 shutter_type='boxcar', period=0.1, duty=0.25,
                 morlet_freq=100.0, morlet_sigma=0.01):
        """
        Initialize frame generator
        
        Args:
            width: Frame width in pixels
            height: Frame height in pixels
            fps: Target frames per second
            shutter_type: 'boxcar' or 'morlet' shutter function
            period: Period for boxcar shutter (seconds)
            duty: Duty cycle for boxcar shutter (0-1)
            morlet_freq: Frequency for Morlet wavelet (Hz)
            morlet_sigma: Sigma parameter for Morlet wavelet (seconds)
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.frame_interval = 1.0 / fps  # seconds per frame
        
        # Initialize event processor
        self.processor = EventProcessor(
            shutter_type=shutter_type,
            period=period,
            duty=duty,
            morlet_freq=morlet_freq,
            morlet_sigma=morlet_sigma
        )
        
        # Initialize frame buffer
        self.frame = np.zeros((height, width, 3), dtype=np.float32)
        self.event_count = 0
        
    def reset_frame(self):
        """Reset the current frame buffer"""
        self.frame.fill(0)
        self.event_count = 0
    
    def add_events(self, timestamps_us, x_coords, y_coords, polarities):
        """
        Add events to the current frame with DCE weighting
        
        Args:
            timestamps_us: Array of timestamps in microseconds
            x_coords: Array of x coordinates
            y_coords: Array of y coordinates
            polarities: Array of polarity values (0 or 1)
        
        Returns:
            Number of events added
        """
        if len(timestamps_us) == 0:
            return 0
        
        # Convert timestamps to seconds
        timestamps_s, t0 = self.processor.convert_timestamps_to_seconds(timestamps_us)
        
        # Apply DCE shutter function
        weights = self.processor.apply_shutter(timestamps_s)
        
        # Filter out events where weight is too small
        mask = weights > 0.01
        
        if not np.any(mask):
            return 0
        
        # Get valid events
        valid_x = x_coords[mask]
        valid_y = y_coords[mask]
        valid_polarities = polarities[mask]
        valid_weights = weights[mask]
        
        # Clip coordinates to valid range
        valid_x = np.clip(valid_x, 0, self.width - 1)
        valid_y = np.clip(valid_y, 0, self.height - 1)
        
        # Accumulate events into frame
        for i in range(len(valid_x)):
            x, y = int(valid_x[i]), int(valid_y[i])
            polarity = valid_polarities[i]
            weight = valid_weights[i]
            
            # Add weighted contribution
            # Polarity 0 = Red, Polarity 1 = Green
            if polarity == 0:
                self.frame[y, x, 2] += weight  # Red channel
            else:
                self.frame[y, x, 1] += weight  # Green channel
        
        self.event_count += len(valid_x)
        return len(valid_x)
    
    def get_frame(self, normalize=True):
        """
        Get the current frame as a uint8 image
        
        Args:
            normalize: If True, normalize values to 0-255 range
        
        Returns:
            Frame as uint8 array (H, W, 3)
        """
        frame = self.frame.copy()
        
        if normalize:
            # Normalize to 0-255 range
            if frame.max() > 0:
                frame = (frame / frame.max() * 255).astype(np.uint8)
            else:
                frame = frame.astype(np.uint8)
        else:
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        
        return frame
    
    def get_event_count(self):
        """Get the number of events in the current frame"""
        return self.event_count


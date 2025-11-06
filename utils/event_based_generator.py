"""
EventBasedFrameGenerator: Creates 2D frames from events using event-count-based buffering
"""
import numpy as np
from .event_processor import EventProcessor


class EventBasedFrameGenerator:
    """Generate frames from event data using event-count-based buffering"""
    
    def __init__(self, width, height, events_per_frame=10000,
                 shutter_type='boxcar', period=0.1, duty=0.25,
                 morlet_freq=100.0, morlet_sigma=0.01, brightness=1.0, decay_rate=1.0):
        """
        Initialize event-based frame generator
        
        Args:
            width: Frame width in pixels
            height: Frame height in pixels
            events_per_frame: Number of events to accumulate before generating a frame
            shutter_type: 'boxcar' or 'morlet' shutter function
            period: Period for boxcar shutter (seconds)
            duty: Duty cycle for boxcar shutter (0-1)
            morlet_freq: Frequency for Morlet wavelet (Hz)
            morlet_sigma: Sigma parameter for Morlet wavelet (seconds)
            brightness: Brightness multiplier (1.0 = normal, >1.0 = brighter)
            decay_rate: Frame persistence decay (1.0 = no decay, 0.95 = 5% fade per frame)
        """
        self.width = width
        self.height = height
        self.events_per_frame = events_per_frame
        self.brightness = brightness
        self.decay_rate = decay_rate
        
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
        self.total_events_added = 0
        
    def reset_frame(self, decay_override=None):
        """
        Reset the current frame buffer
        
        Args:
            decay_override: Optional decay rate to use instead of self.decay_rate
        """
        # If no events were added, don't decay (preserve static content)
        if self.event_count == 0:
            return
        
        decay = decay_override if decay_override is not None else self.decay_rate
        
        if decay < 1.0:
            self.frame *= decay
        else:
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
            Tuple of (events_added, should_generate_frame)
            - events_added: Number of events actually added
            - should_generate_frame: True if event threshold reached
        """
        if len(timestamps_us) == 0:
            return 0, False
        
        # Convert timestamps to seconds (keep absolute time for DCE shutter)
        timestamps_s = timestamps_us * 1e-6
        
        # Apply DCE shutter function
        weights = self.processor.apply_shutter(timestamps_s)
        
        # Filter out events where weight is too small
        mask = weights > 0.01
        
        if not np.any(mask):
            return 0, False
        
        # Get valid events
        valid_x = x_coords[mask]
        valid_y = y_coords[mask]
        valid_polarities = polarities[mask]
        valid_weights = weights[mask]
        
        # Clip coordinates to valid range
        valid_x = np.clip(valid_x, 0, self.width - 1)
        valid_y = np.clip(valid_y, 0, self.height - 1)
        
        # Accumulate events into frame using signed polarity for DCE
        for i in range(len(valid_x)):
            x, y = int(valid_x[i]), int(valid_y[i])
            polarity = valid_polarities[i]
            weight = valid_weights[i]
            
            # Map polarity to ±1 and apply shutter weight (as in Plot_wDCE.py)
            polarity_signed = 1.0 if polarity > 0 else -1.0
            weighted_polarity = polarity_signed * weight
            
            # Positive weighted polarity = Green, Negative = Red
            if weighted_polarity > 0:
                self.frame[y, x, 1] += weighted_polarity  # Green channel
            else:
                self.frame[y, x, 2] += abs(weighted_polarity)  # Red channel
        
        events_added = len(valid_x)
        self.event_count += events_added
        self.total_events_added += events_added
        
        # Check if we've reached the threshold
        should_generate_frame = self.event_count >= self.events_per_frame
        
        return events_added, should_generate_frame
    
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
                frame = (frame / frame.max() * 255 * self.brightness).astype(np.uint8)
            else:
                frame = frame.astype(np.uint8)
        else:
            frame = np.clip(frame * self.brightness, 0, 255).astype(np.uint8)
        
        return frame
    
    def get_event_count(self):
        """Get the number of events in the current frame"""
        return self.event_count
    
    def get_total_events_added(self):
        """Get the total number of events added since initialization"""
        return self.total_events_added
    
    def set_events_per_frame(self, events_per_frame):
        """Update the events-per-frame threshold"""
        self.events_per_frame = events_per_frame


"""
AdaptiveDecayController: Dynamically adjusts frame decay rate based on scene activity
"""
import numpy as np


class AdaptiveDecayController:
    """Controls frame decay rate based on scene activity"""
    
    def __init__(self, min_decay=0.98, max_decay=0.75, low_thresh=10000,
                 high_thresh=40000, alpha=0.2, hysteresis=0.05):
        """
        Initialize adaptive decay controller
        
        Args:
            min_decay: Minimum decay rate (for low activity/static scenes)
            max_decay: Maximum decay rate (for high activity/motion)
            low_thresh: Activity threshold below which decay is minimized
            high_thresh: Activity threshold above which decay is maximized
            alpha: Smoothing factor for decay transitions (0-1, lower = smoother)
            hysteresis: Minimum change required to update decay (prevents flicker)
        """
        self.min_decay = min_decay
        self.max_decay = max_decay
        self.low = low_thresh
        self.high = high_thresh
        self.alpha = alpha
        self.hyst = hysteresis
        self.s_decay = min_decay  # Smoothed decay value
    
    def activity_to_decay(self, events_this_frame, buffer_len):
        """
        Convert activity metrics to decay rate
        
        Args:
            events_this_frame: Number of events added in current frame
            buffer_len: Current size of event buffer
            
        Returns:
            Decay rate (between max_decay and min_decay)
        """
        # Activity metric: use events this frame or scaled buffer size (whichever is larger)
        activity = max(events_this_frame, int(0.5 * buffer_len))
        
        # Map activity to target decay rate
        if activity <= self.low:
            target = self.min_decay
        elif activity >= self.high:
            target = self.max_decay
        else:
            # Linear interpolation between thresholds
            k = (activity - self.low) / (self.high - self.low)
            target = self.min_decay + k * (self.max_decay - self.min_decay)
        
        # Apply hysteresis to prevent rapid oscillation
        if abs(target - self.s_decay) < self.hyst:
            target = self.s_decay
        
        # Smooth decay transitions
        self.s_decay = self.alpha * target + (1 - self.alpha) * self.s_decay
        
        # Clamp to valid range
        return float(np.clip(self.s_decay, self.max_decay, self.min_decay))





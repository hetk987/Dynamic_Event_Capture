"""
EventProcessor: Handles DCE weighting and event processing
"""
import numpy as np


class EventProcessor:
    """Process events and apply Digital Coded Exposure (DCE) weighting"""
    
    def __init__(self, shutter_type='boxcar', period=0.1, duty=0.25, 
                 morlet_freq=100.0, morlet_sigma=0.01):
        """
        Initialize event processor with DCE parameters
        
        Args:
            shutter_type: 'boxcar' or 'morlet' shutter function
            period: Period for boxcar shutter (seconds)
            duty: Duty cycle for boxcar shutter (0-1)
            morlet_freq: Frequency for Morlet wavelet (Hz)
            morlet_sigma: Sigma parameter for Morlet wavelet (seconds)
        """
        self.shutter_type = shutter_type
        self.period = period
        self.duty = duty
        self.morlet_freq = morlet_freq
        self.morlet_sigma = morlet_sigma
    
    @staticmethod
    def boxcar_shutter(t, period=0.1, duty=0.25, phase=0.0):
        """
        Boxcar shutter: open for duty*period, closed otherwise.
        
        Args:
            t: Time value(s) in seconds
            period: Period of the shutter (seconds)
            duty: Duty cycle (0-1)
            phase: Phase offset (seconds)
        
        Returns:
            Weight value(s): 1.0 when open, 0.0 when closed
        """
        t_mod = (t - phase) % period
        if isinstance(t, np.ndarray):
            return np.where(t_mod < duty * period, 1.0, 0.0)
        return 1.0 if t_mod < duty * period else 0.0
    
    @staticmethod
    def morlet_shutter(t, f=100.0, sigma=0.01):
        """
        Morlet wavelet shutter centered at frequency f [Hz].
        
        Args:
            t: Time value(s) in seconds
            f: Center frequency (Hz)
            sigma: Width parameter (seconds)
        
        Returns:
            Weight value(s) from Morlet wavelet
        """
        return np.exp(-0.5 * (t/sigma)**2) * np.cos(2*np.pi*f*t)
    
    @staticmethod
    def no_shutter(t):
        """
        No shutter: return 1.0 for all timestamps
        
        Args:
            t: Time value(s) in seconds
        
        Returns:
            Weight value(s): 1.0 for all timestamps
        """
        return np.ones_like(t)
    
    def apply_shutter(self, timestamps, phase=0.0):
        """
        Apply the configured shutter function to timestamps
        
        Args:
            timestamps: Array of timestamps in seconds
            phase: Phase offset for boxcar shutter (seconds)
        
        Returns:
            Array of weights corresponding to each timestamp
        """
        if self.shutter_type == 'boxcar':
            return np.array([self.boxcar_shutter(t, self.period, self.duty, phase) 
                            for t in timestamps])
        elif self.shutter_type == 'morlet':
            return np.array([self.morlet_shutter(t, self.morlet_freq, self.morlet_sigma) 
                            for t in timestamps])
        elif self.shutter_type == 'no_shutter':
            return np.array([self.no_shutter(t) for t in timestamps])
        else:
            raise ValueError(f"Unknown shutter type: {self.shutter_type}")
        
    
    
    def convert_timestamps_to_seconds(self, timestamps_us):
        """
        Convert microsecond timestamps to seconds relative to first event
        
        Args:
            timestamps_us: Array of timestamps in microseconds
        
        Returns:
            Tuple of (timestamps_s, t0) where:
                - timestamps_s: Timestamps in seconds relative to start
                - t0: First timestamp in microseconds
        """
        if len(timestamps_us) == 0:
            return timestamps_us, 0
        
        t0 = timestamps_us[0]
        timestamps_s = (timestamps_us - t0) * 1e-6
        return timestamps_s, t0


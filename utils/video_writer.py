"""
VideoWriter: Handles MP4 video output
"""
import cv2
import os


class VideoWriter:
    """Write frames to MP4 video file"""
    
    def __init__(self, output_path, width, height, fps=30, codec='mp4v'):
        """
        Initialize video writer
        
        Args:
            output_path: Path to output video file
            width: Video width in pixels
            height: Video height in pixels
            fps: Frames per second
            codec: Video codec (mp4v, avc1, etc.)
        """
        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps
        self.codec = codec
        self.writer = None
        self.frame_count = 0
        self.initialized = False
    
    def _initialize_writer(self):
        """Initialize the video writer"""
        if self.initialized:
            return
        
        # Create output directory if needed
        output_dir = os.path.dirname(self.output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Create fourcc codec
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        
        # Initialize writer
        self.writer = cv2.VideoWriter(
            self.output_path,
            fourcc,
            self.fps,
            (self.width, self.height)
        )
        
        if not self.writer.isOpened():
            raise RuntimeError(f"Failed to open video writer for {self.output_path}")
        
        self.initialized = True
        print(f"Video writer initialized: {self.output_path}")
    
    def write_frame(self, frame):
        """
        Write a frame to the video
        
        Args:
            frame: Frame as numpy array (H, W, 3) uint8
        
        Returns:
            True if successful, False otherwise
        """
        if frame is None:
            return False
        
        # Ensure frame is correct size
        if frame.shape[:2] != (self.height, self.width):
            frame = cv2.resize(frame, (self.width, self.height))
        
        # Initialize writer on first frame
        if not self.initialized:
            self._initialize_writer()
        
        # Write frame
        self.writer.write(frame)
        self.frame_count += 1
        
        return True
    
    def release(self):
        """Release the video writer"""
        if self.writer is not None:
            self.writer.release()
            self.writer = None
            self.initialized = False
            print(f"Video writer released: {self.frame_count} frames written to {self.output_path}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()


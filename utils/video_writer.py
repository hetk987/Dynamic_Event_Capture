"""
VideoWriter: Handles MP4 video output
"""
import cv2
import os


class VideoWriter:
    """Write frames to MP4 video file"""
    
    def __init__(self, output_path, width, height, fps=30, codec='avc1'):
        """
        Initialize video writer
        
        Args:
            output_path: Path to output video file
            width: Video width in pixels
            height: Video height in pixels
            fps: Frames per second
            codec: Video codec ('avc1' recommended for H.264, 'mp4v' for older compatibility)
        """
        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps
        self.codec = codec
        self.codec_fallbacks = ['avc1', 'H264', 'X264', 'mp4v']  # Fallback codecs to try
        self.writer = None
        self.frame_count = 0
        self.initialized = False
    
    def _initialize_writer(self):
        """Initialize the video writer with codec fallback support"""
        if self.initialized:
            return
        
        # Create output directory if needed
        output_dir = os.path.dirname(self.output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Try to initialize with requested codec first
        codecs_to_try = [self.codec] + [c for c in self.codec_fallbacks if c != self.codec]
        
        for codec in codecs_to_try:
            try:
                # Create fourcc codec
                fourcc = cv2.VideoWriter_fourcc(*codec)
                
                # Initialize writer
                self.writer = cv2.VideoWriter(
                    self.output_path,
                    fourcc,
                    self.fps,
                    (self.width, self.height)
                )
                
                # Check if writer opened successfully
                if self.writer.isOpened():
                    self.initialized = True
                    codec_msg = f" (using {codec})" if codec != self.codec else ""
                    print(f"Video writer initialized: {self.output_path}{codec_msg}")
                    print(f"  Codec: {codec}, FPS: {self.fps}, Resolution: {self.width}x{self.height}")
                    return
                else:
                    # Release failed writer
                    if self.writer is not None:
                        self.writer.release()
                        self.writer = None
            except Exception as e:
                print(f"Warning: Codec '{codec}' failed: {e}")
                continue
        
        # If we get here, all codecs failed
        raise RuntimeError(
            f"Failed to open video writer for {self.output_path}. "
            f"Tried codecs: {', '.join(codecs_to_try)}"
        )
    
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


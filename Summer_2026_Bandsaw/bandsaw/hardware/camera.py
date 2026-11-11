import os
import time
import cv2

picam2 = None

class _PicameraCapture:
    def __init__(self, camera):
        self.camera = camera

    def read(self):
        return True, self.camera.capture_array()

    def release(self):
        self.camera.stop()


def open_video_source(source="picamera"):
    """Open Picamera2, an OpenCV camera index, or a video file."""
    global picam2

    if source is None or str(source).lower() in ("picamera", "csi"):
        try:
            from picamera2 import Picamera2

            picam2 = Picamera2()
            picam2.preview_configuration.main.size = (1280, 720)
            picam2.preview_configuration.main.format = "RGB888"
            picam2.configure("preview")
            picam2.start()
            print("Picamera2 initialized successfully.")
            return _PicameraCapture(picam2)
        except Exception as error:
            print(f"Error initializing Picamera2: {error}")
            picam2 = None
            return None

    if isinstance(source, str) and source.isdigit():
        source = int(source)
    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        print(f"Error: Could not open video source {source!r}.")
        capture.release()
        return None
    return capture

def get_frame(source=None):
    """Read one frame from an opened video source."""
    if source is None and picam2 is not None:
        source = _PicameraCapture(picam2)
    if source is None:
        return False, None
    try:
        return source.read()
    except Exception as error:
        print(f"Failed to capture frame: {error}")
        return False, None

def release_video(source=None):
    """Release an opened source and reset the legacy Picamera2 handle."""
    global picam2
    if source is None and picam2 is not None:
        source = _PicameraCapture(picam2)
    if source is not None:
        source.release()
    if source is None or isinstance(source, _PicameraCapture):
        picam2 = None
        print("Picamera2 stopped.")


class VideoRecorder:
    """Helper class for video recording with advanced features"""
    
    def __init__(self, output_dir="recordings", fps=30.0, codec='mp4v'):
        """
        Initialize a video recorder
        
        Args:
            output_dir: Directory to save recordings
            fps: Frames per second for recording
            codec: Four character code for the codec (e.g., 'mp4v', 'XVID')
        """
        self.output_dir = output_dir
        self.fps = fps
        self.fourcc = cv2.VideoWriter_fourcc(*codec)
        self.writer = None
        self.recording = False
        self.start_time = None
        self.frame_count = 0
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created recordings directory: {output_dir}")
    
    def start(self, frame, prefix="recording"):
        """
        Start recording a video
        
        Args:
            frame: Initial frame to determine dimensions
            prefix: Filename prefix
            
        Returns:
            Path to the video file
        """
        if self.recording:
            self.stop()
        
        # Create filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.mp4"
        filepath = os.path.join(self.output_dir, filename)
        
        # Get frame dimensions
        height, width = frame.shape[:2]
        
        # Initialize video writer
        self.writer = cv2.VideoWriter(filepath, self.fourcc, self.fps, (width, height))
        
        if not self.writer.isOpened():
            print(f"Error: Could not open video writer for {filepath}")
            self.writer = None
            return None
        
        self.recording = True
        self.start_time = time.time()
        self.frame_count = 0
        print(f"Started recording: {filepath}")
        
        # Write the first frame
        self.write(frame)
        
        return filepath
    
    def write(self, frame):
        """
        Write a frame to the video
        
        Args:
            frame: Frame to write
            
        Returns:
            True if successful, False otherwise
        """
        if not self.recording or self.writer is None:
            return False
        
        try:
            self.writer.write(frame)
            self.frame_count += 1
            return True
        except Exception as e:
            print(f"Error writing video frame: {e}")
            return False
    
    def stop(self):
        """
        Stop recording and release resources
        
        Returns:
            Tuple (duration, frame_count)
        """
        if not self.recording or self.writer is None:
            return (0, 0)
        
        duration = time.time() - self.start_time
        
        try:
            self.writer.release()
            print(f"Stopped recording. Duration: {duration:.1f}s, Frames: {self.frame_count}")
        except Exception as e:
            print(f"Error stopping recording: {e}")
        
        self.writer = None
        self.recording = False
        
        return (duration, self.frame_count)
    
    def is_recording(self):
        """Check if recording is active"""
        return self.recording

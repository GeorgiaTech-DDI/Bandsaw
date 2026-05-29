# video_capture.py
from picamera2 import Picamera2
import os
import time
import cv2


class Camera:
    def __init__(self, size=(1280,720), fmt="RGB888"):
        self._cam = None
        self.size = size
        self.fmt = fmt

    def open(self):
        if self._cam:
            return True
        try:
            self._cam = Picamera2()
            self._cam.preview_configuration.main.size = self.size
            self._cam.preview_configuration.main.format = self.fmt
            self._cam.configure("preview")
            self._cam.start()
            return True
        except Exception as e:
            print(f"Error initializing Picamera2: {e}")
            self._cam = None
            return False

    def get_frame(self):
        if not self._cam:
            return False, None
        try:
            frame = self._cam.capture_array()
            return True, frame
        except Exception as e:
            print(f"Failed to capture frame: {e}")
            return False, None

    def stop(self):
        if self._cam:
            try:
                self._cam.stop()
            except Exception as e:
                print(f"Error stopping camera: {e}")
            finally:
                self._cam = None

    def is_open(self):
        return self._cam is not None

def open_video_source(x=None):
    """
    Initialize Picamera2 for video input.
    """
    cam = Camera()
    if cam.open():
        ok, frame = cam.get_frame()
        # pass `cam` or `frame` to other components
    cam.release()
    
    try:
        cam = Picamera2()
        cam.preview_configuration.main.size = (1280, 720)
        cam.preview_configuration.main.format = "RGB888"
        cam.configure("preview")
        cam.start()
        print("Picamera2 initialized successfully.")
        return True  # dummy object to match old usage
    except Exception as e:
        print(f"Error initializing Picamera2: {e}")
        return None


def get_frame(x=None):
    """
    Capture a frame using Picamera2.
    """
    cam = Camera()
    if cam.open():
        ok, frame = cam.get_frame()
        # pass `cam` or `frame` to other components
    cam.release()

    try:
        frame = cam.get_frame()
        return True, frame
    except Exception as e:
        print(f"Failed to capture frame: {e}")
        return False, None


def release_video(x=None):
    """
    Stop the camera and release resources.
    """
    cam = Camera()
    if cam.open():
        ok, frame = cam.get_frame()
        # pass `cam` or `frame` to other components
    cam.release()

    if cam:
        cam.stop()
        print("Picamera2 stopped.")


class VideoRecorder:
    """Helper class for video recording with advanced features"""

    def __init__(self, output_dir="recordings", fps=30.0, codec="mp4v"):
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
            print(
                f"Stopped recording. Duration: {duration:.1f}s, Frames: {self.frame_count}"
            )
        except Exception as e:
            print(f"Error stopping recording: {e}")

        self.writer = None
        self.recording = False

        return (duration, self.frame_count)

    def is_recording(self):
        """Check if recording is active"""
        return self.recording

from picamera2 import Picamera2
import os
import time
import cv2


class PiCameraCapture:
    """
    Encapsulates Picamera2 lifecycle and frame capture.
    """

    def __init__(self, resolution=(1280, 720), format="RGB888"):
        try:
            self.picam2 = Picamera2()
            self.picam2.preview_configuration.main.size = resolution
            self.picam2.preview_configuration.main.format = format
            self.picam2.configure("preview")
            self.picam2.start()
            print("Picamera2 initialized successfully.")
        except Exception as e:
            raise RuntimeError(f"Error initializing Picamera2: {e}")

    def get_frame(self):
        try:
            frame = self.picam2.capture_array()
            return True, frame
        except Exception as e:
            print(f"Failed to capture frame: {e}")
            return False, None

    def release(self):
        try:
            self.picam2.stop()
            print("Picamera2 stopped.")
        except Exception as e:
            print(f"Error stopping Picamera2: {e}")
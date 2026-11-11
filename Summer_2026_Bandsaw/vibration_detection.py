# vibration_detection.py
import threading
import time
import sys
import os

# Try to import from process directory first, then try direct import
try:
    from process.mpu6050_sensor import MPU6050
except ImportError:
    try:
        from mpu6050_sensor import MPU6050
    except ImportError:
        print("Error: Cannot import MPU6050 module. Make sure mpu6050_sensor.py is in the same directory.")
        sys.exit(1)

class VibrationDetector:
    def __init__(self, threshold=0.5, cooldown_time=1.0, mock_mode=True):
        """
        Initialize vibration detector
        
        Args:
            threshold: Vibration threshold to detect bandsaw activity
            cooldown_time: Time to wait after stopping detection before restarting
            mock_mode: Whether to use mock mode for MPU6050
        """
        self.mpu = MPU6050(mock_mode=mock_mode)
        self.threshold = threshold
        self.cooldown_time = cooldown_time
        self.running = False
        self.is_active = False
        self.last_inactive_time = 0
        self.callback = None
        self.detection_thread = None
        self.mock_mode = mock_mode
        self.debug = False
    
    def set_activity_callback(self, callback):
        """Set callback function to be called when activity state changes"""
        self.callback = callback
    
    def start_detection(self, debug=False):
        """Start vibration detection in a separate thread"""
        if self.detection_thread and self.detection_thread.is_alive():
            return
        
        self.debug = debug
        self.running = True
        self.detection_thread = threading.Thread(target=self._monitor_vibration)
        self.detection_thread.daemon = True
        self.detection_thread.start()
        print("Vibration detection started")
    
    def stop_detection(self):
        """Stop vibration detection"""
        self.running = False
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=1.0)
        print("Vibration detection stopped")
    
    def set_mock_vibration(self, level):
        """Set mock vibration level for testing"""
        if self.mock_mode and hasattr(self.mpu, 'set_mock_vibration'):
            self.mpu.set_mock_vibration(level)
    
    def _monitor_vibration(self):
        """Thread function to monitor vibration levels"""
        while self.running:
            try:
                # Get vibration magnitude
                vibration = self.mpu.get_vibration_magnitude()
                
                if self.debug:
                    print(f"Current vibration: {vibration:.4f}, threshold: {self.threshold:.4f}")
                
                current_time = time.time()
                was_active = self.is_active
                
                # Check if bandsaw is active based on vibration
                if vibration > self.threshold:
                    self.is_active = True
                    if self.debug and not was_active:
                        print(f"Vibration {vibration:.4f} exceeded threshold {self.threshold:.4f}")
                elif current_time - self.last_inactive_time > self.cooldown_time:
                    self.is_active = False
                    self.last_inactive_time = current_time
                    if self.debug and was_active:
                        print(f"Vibration {vibration:.4f} below threshold for {self.cooldown_time}s")
                
                # Call callback if state changed
                if was_active != self.is_active and self.callback:
                    self.callback(self.is_active)
                
                time.sleep(0.1)
            except Exception as e:
                print(f"Error in vibration monitoring: {e}")
                time.sleep(1.0)  # Wait longer on error
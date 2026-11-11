# test_mpu6050.py
# Simple test script for MPU6050 sensor on Raspberry Pi

from mpu6050_sensor import MPU6050
import time

print("\n===== MPU6050 Sensor Test =====")

# Initialize the sensor in real hardware mode
sensor = MPU6050(mock_mode=False)

try:
    while True:
        ax, ay, az = sensor.get_acceleration()
        vibration = sensor.get_vibration_magnitude()

        print(f"Accel (g) -> X: {ax:.3f}, Y: {ay:.3f}, Z: {az:.3f} | Vibration: {vibration:.4f}")
        time.sleep(0.2)

except KeyboardInterrupt:
    print("\nTest stopped by user")

except Exception as e:
    print(f"\nError reading from MPU6050: {e}")

# Worked code
import smbus2
import time
import math
import cv2
import numpy as np
import threading
from picamera2 import Picamera2

# I2C address for MPU6050
MPU6050_ADDR = 0x68
THRESHOLD = 0.2  # Adjust based on testing
NO_MOVEMENT_TIMEOUT = 5  # Seconds before stopping camera sensor

# Initialize I2C bus
bus = smbus2.SMBus(1)

# Initialize MPU6050 (Wake up)
def write_i2c_byte(addr, reg, value):
    bus.write_byte_data(addr, reg, value)

def read_i2c_word(addr, reg):
    high = bus.read_byte_data(addr, reg)
    low = bus.read_byte_data(addr, reg + 1)
    value = (high << 8) + low
    if value >= 0x8000:
        value = -((65535 - value) + 1)
    return value

write_i2c_byte(MPU6050_ADDR, 0x6B, 0)  

# Initialize Camera
camera = Picamera2()
camera.configure(camera.create_preview_configuration(main={"size": (640, 480)}))
camera.start_preview()  # Keep preview open
camera.start()  # Start camera initially but stop sensor later
camera_on = False  
last_movement_time = time.time()

# Read MPU6050 sensor
def read_mpu6050():
    acc_x = read_i2c_word(MPU6050_ADDR, 0x3B) / 4096.0
    acc_y = read_i2c_word(MPU6050_ADDR, 0x3D) / 4096.0
    acc_z = read_i2c_word(MPU6050_ADDR, 0x3F) / 4096.0
    return acc_x, acc_y, acc_z

def calculate_magnitude(acc_x, acc_y, acc_z):
    return math.sqrt(acc_x**2 + acc_y**2 + acc_z**2)

prev_magnitude = None  

# Function to monitor MPU6050
def bandsaw_active():
    global camera_on, last_movement_time, prev_magnitude

    while True:
        acc_x, acc_y, acc_z = read_mpu6050()
        current_magnitude = calculate_magnitude(acc_x, acc_y, acc_z)

        if prev_magnitude is not None:
            delta_magnitude = abs(current_magnitude - prev_magnitude)
            movement_detected = delta_magnitude > THRESHOLD
        else:
            delta_magnitude = 0
            movement_detected = False

        if movement_detected:
            print("Movement detected!")
            last_movement_time = time.time()

            if not camera_on:
                print("Turning ON camera sensor...")
                camera.start()
                camera_on = True

        if camera_on and (time.time() - last_movement_time) > NO_MOVEMENT_TIMEOUT:
            print("No movement detected for 5 seconds. Turning OFF camera sensor...")
            camera.stop()  # Stop sensor but keep preview open
            camera_on = False
            cv2.destroyAllWindows()

        prev_magnitude = current_magnitude
        time.sleep(0.1)  # Check every 100ms

# Run MPU6050 monitoring in a separate thread
mpu_thread = threading.Thread(target=bandsaw_active, daemon=True)
mpu_thread.start()

# Main loop to display frames continuously
while True:
    if camera_on:
        frame = camera.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow("Camera Feed", frame)
    else:
        idle_frame = np.zeros((480, 630, 3), dtype=np.uint8)
        cv2.putText(idle_frame, "Camera Off", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow("Camera Feed", idle_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


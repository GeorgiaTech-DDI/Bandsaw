# # Worked code
# import time
# from mpu6050 import mpu6050
# import math
# 
# # Initialize the MPU6050 sensor
# MPU_ADDR = 0x68  # Address of the MPU6050 (use 0x69 if AD0 is high)
# sensor = mpu6050(MPU_ADDR)
# 
# # Define movement threshold (tuning required)
# MOVEMENT_THRESHOLD = 0.5  # Change in magnitude (g) to consider as "movement"
# 
# # Function to calculate the magnitude of acceleration (distance from 0,0,0)
# def calculate_magnitude(x, y, z):
#     return math.sqrt(x**2 + y**2 + z**2)
# 
# # Initial state of the sensor
# previous_magnitude = None
# 
# try:
#     while True:
#         # Get accelerometer data
#         accel_data = sensor.get_accel_data()
#         x, y, z = accel_data['x'], accel_data['y'], accel_data['z']
#         
#         # Calculate the magnitude of acceleration
#         accel_magnitude = calculate_magnitude(x, y, z)
#         
#         # Check if the magnitude change is significant
#         if previous_magnitude is not None:
#             # Compare current magnitude with the previous state
#             magnitude_change = abs(accel_magnitude - previous_magnitude)
#             
#             if magnitude_change > MOVEMENT_THRESHOLD:
#                 print("Movement detected!")
#             else:
#                 print(f"Stable - Accelerometer Data: {accel_data}")
#         else:
#             print(f"Initial Accelerometer Data: {accel_data}")
#         
#         # Update the previous magnitude
#         previous_magnitude = accel_magnitude
# 
#         # Wait before taking another reading (to control the frequency)
#         time.sleep(0.3)
# 
# except KeyboardInterrupt:
#     print("Program interrupted. Exiting...")
# 
# finally:
#     # Any cleanup or closing tasks (if necessary) can go here
#     print("Exiting program safely.")

import smbus2
import time
import math
import json

# I2C address for MPU6050
MPU6050_ADDR = 0x68
THRESHOLD = 0.3  # Adjust based on testing

def write_i2c_byte(addr, reg, value):
    bus.write_byte_data(addr, reg, value)

def read_i2c_word(addr, reg):
    high = bus.read_byte_data(addr, reg)
    low = bus.read_byte_data(addr, reg + 1)
    value = (high << 8) + low
    if value >= 0x8000:
        value = -((65535 - value) + 1)
    return value

# Initialize I2C bus
bus = smbus2.SMBus(1)

# Initialize MPU6050 (Wake up)
write_i2c_byte(MPU6050_ADDR, 0x6B, 0)  

def read_mpu6050():
    acc_x = read_i2c_word(MPU6050_ADDR, 0x3B) / 4096.0
    acc_y = read_i2c_word(MPU6050_ADDR, 0x3D) / 4096.0
    acc_z = read_i2c_word(MPU6050_ADDR, 0x3F) / 4096.0
    gyro_x = read_i2c_word(MPU6050_ADDR, 0x43) / 65.5
    gyro_y = read_i2c_word(MPU6050_ADDR, 0x45) / 65.5
    gyro_z = read_i2c_word(MPU6050_ADDR, 0x47) / 65.5
    angle_roll = math.atan2(acc_y, math.sqrt(acc_x**2 + acc_z**2)) * (180 / math.pi)
    angle_pitch = -math.atan2(acc_x, math.sqrt(acc_y**2 + acc_z**2)) * (180 / math.pi)
    return acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, angle_roll, angle_pitch

def calculate_magnitude(acc_x, acc_y, acc_z):
    """Calculate the magnitude of the acceleration vector."""
    return math.sqrt(acc_x**2 + acc_y**2 + acc_z**2)

def jsonify_data(asset_id, timestamp, roll, pitch, acc_x, acc_y, acc_z, delta_magnitude, movement_detected):
    data = {
        "assetID": asset_id,
        "timestamp": timestamp,
        "roll_angle": roll,
        "pitch_angle": pitch,
        "accX": acc_x,
        "accY": acc_y,
        "accZ": acc_z,
        "delta_magnitude": delta_magnitude,
        "movement_detected": movement_detected
    }
    print(json.dumps(data, indent=4))

prev_magnitude = None  # Store previous magnitude

while True:
    acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, angle_roll, angle_pitch = read_mpu6050()
    current_magnitude = calculate_magnitude(acc_x, acc_y, acc_z)
    
    if prev_magnitude is not None:
        delta_magnitude = abs(current_magnitude - prev_magnitude)
        movement_detected = delta_magnitude > THRESHOLD
    else:
        delta_magnitude = 0
        movement_detected = False
    
    if movement_detected:
        print("Significant movement detected!")

    timestamp = time.time()
    jsonify_data("Sanding_WoodRoom", timestamp, angle_roll, angle_pitch, acc_x, acc_y, acc_z, delta_magnitude, movement_detected)

    prev_magnitude = current_magnitude  # Update previous magnitude
    time.sleep(0.3)


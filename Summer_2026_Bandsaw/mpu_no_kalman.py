# import smbus2
# import time
# import json
# import serial
# from datetime import datetime
# 
# # MPU6050 I2C Address
# MPU6050_ADDR = 0x68  
# 
# # Register Addresses for Accelerometer & Gyroscope Data
# ACCEL_XOUT_H = 0x3B
# GYRO_XOUT_H = 0x43
# PWR_MGMT_1 = 0x6B  
# 
# # Initialize I2C Bus
# bus = smbus2.SMBus(1)  
# 
# # Wake up the MPU6050 (it's in sleep mode by default)
# bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)
# 
# def read_raw_data(addr):
#     """ Read two bytes of data from given register address. """
#     high = bus.read_byte_data(MPU6050_ADDR, addr)   # Read higher byte
#     low = bus.read_byte_data(MPU6050_ADDR, addr+1)  # Read lower byte
#     value = (high << 8) | low  # Combine bytes
#     
#     # Convert to signed 16-bit integer
#     if value > 32767:
#         value -= 65536
#     return value
# 
# # Set up serial port for data transmission
# serial_port = "/dev/ttyAMA10"
# baud_rate = 57600
# ser = serial.Serial(serial_port, baud_rate)
# 
# while True:
#     # Read raw values
#     raw_acc_x = read_raw_data(ACCEL_XOUT_H)
#     raw_acc_y = read_raw_data(ACCEL_XOUT_H + 2)
#     raw_acc_z = read_raw_data(ACCEL_XOUT_H + 4)
# 
#     raw_gyro_x = read_raw_data(GYRO_XOUT_H)
#     raw_gyro_y = read_raw_data(GYRO_XOUT_H + 2)
#     raw_gyro_z = read_raw_data(GYRO_XOUT_H + 4)
# 
#     # Get timestamp
#     current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#     
#     # Create JSON data packet
#     data_dict = {
#         "timestamp": current_datetime,
#         "accX": raw_acc_x,
#         "accY": raw_acc_y,
#         "accZ": raw_acc_z,
#         "gyroX": raw_gyro_x,
#         "gyroY": raw_gyro_y,
#         "gyroZ": raw_gyro_z
#     }
#     
#     # Convert to JSON string and send over serial
#     payload = json.dumps(data_dict)
#     ser.write(payload.encode('utf-8'))
#     ser.write(b'\n')  # Ensure new line for readability
#     
#     print(payload)  # Print data for debugging
#     
#     time.sleep(1)  # Delay before next reading

import smbus2
import time
import math
import json

# I2C address for MPU6050
MPU6050_ADDR = 0x68

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

def jsonify_data(asset_id, timestamp, roll, pitch, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z):
    data = {
        "assetID": asset_id,
        "timestamp": timestamp,
        "roll_angle": roll,
        "pitch_angle": pitch,
        "accX": acc_x,
        "accY": acc_y,
        "accZ": acc_z,
        "gyroX": gyro_x,
        "gyroY": gyro_y,
        "gyroZ": gyro_z
    }
    print(json.dumps(data, indent=4))

while True:
    acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, angle_roll, angle_pitch = read_mpu6050()
    timestamp = time.time()
    jsonify_data("Moving_bandsaw_no_kalman", timestamp, angle_roll, angle_pitch, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z)
    time.sleep(0.1)

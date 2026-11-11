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
    low = bus.read_byte_data(addr, reg+1)
    value = (high << 8) + low
    if value >= 0x8000:
        value = -((65535 - value) + 1)
    return value

# Initialize I2C bus
bus = smbus2.SMBus(1)

# Initialize MPU6050
write_i2c_byte(MPU6050_ADDR, 0x6B, 0)  # Wake up MPU6050

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

def kalman_filter(state, uncertainty, input, measurement):
    state += 0.004 * input
    uncertainty += (0.004**2) * (4**2)
    kalman_gain = uncertainty / (uncertainty + 3**2)
    state += kalman_gain * (measurement - state)
    uncertainty *= (1 - kalman_gain)
    return state, uncertainty

kalman_angle_roll, kalman_uncertainty_roll = 0, 4
kalman_angle_pitch, kalman_uncertainty_pitch = 0, 4

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
    kalman_angle_roll, kalman_uncertainty_roll = kalman_filter(kalman_angle_roll, kalman_uncertainty_roll, gyro_x, angle_roll)
    kalman_angle_pitch, kalman_uncertainty_pitch = kalman_filter(kalman_angle_pitch, kalman_uncertainty_pitch, gyro_y, angle_pitch)
    timestamp = time.time()
    jsonify_data("Moving_bandsaw_kalman", timestamp, kalman_angle_roll, kalman_angle_pitch, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z)
    time.sleep(0.5)


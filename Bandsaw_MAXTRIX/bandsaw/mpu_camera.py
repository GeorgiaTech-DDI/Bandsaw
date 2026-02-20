# mpu_camera.py
import smbus2
import math
import time

MPU6050_ADDR = 0x68
bus = smbus2.SMBus(1)
bus.write_byte_data(MPU6050_ADDR, 0x6B, 0)  # Wake up

ACCEL_THRESHOLD = 0.3
INACTIVITY_TIMEOUT = 7

prev_magnitude = None
last_motion_time = time.time()


def read_mpu6050():
    def read_word(reg):
        high = bus.read_byte_data(MPU6050_ADDR, reg)
        low = bus.read_byte_data(MPU6050_ADDR, reg + 1)
        val = (high << 8) + low
        if val >= 0x8000:
            val = -((65535 - val) + 1)
        return val / 4096.0

    ax = read_word(0x3B)
    ay = read_word(0x3D)
    az = read_word(0x3F)
    return ax, ay, az


def bandsaw_active():
    global prev_magnitude, last_motion_time

    try:
        ax, ay, az = read_mpu6050()
        magnitude = math.sqrt(ax**2 + ay**2 + az**2)

        if prev_magnitude is not None:
            delta = abs(magnitude - prev_magnitude)
            if delta > ACCEL_THRESHOLD:
                last_motion_time = time.time()

        prev_magnitude = magnitude
        active = (time.time() - last_motion_time) < INACTIVITY_TIMEOUT
        return active

    except RuntimeError as e:
        print("MPU6050 read error:", e)
        return True  # Fail-safe

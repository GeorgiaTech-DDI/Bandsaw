# # mpu6050_sensor.py - Completely simplified mock version
# import math
# import random
# 
# class MPU6050:
#     def __init__(self, bus=1, address=0x68, mock_mode=True):
#         self.mock_vibration_level = 0.0
#         print("MPU6050 initialized in MOCK MODE")
#     
#     def get_acceleration(self):
#         """Get simulated acceleration data"""
#         noise = random.uniform(-0.05, 0.05)
#         vibration = random.uniform(-self.mock_vibration_level, self.mock_vibration_level)
#         
#         ax = 0.05 + noise + vibration
#         ay = 0.02 + noise + vibration
#         az = 0.98 + noise + vibration  # Mostly gravity in z direction
#         
#         return (ax, ay, az)
#     
#     def get_vibration_magnitude(self):
#         """Get magnitude of acceleration vector (removing gravity)"""
#         ax, ay, az = self.get_acceleration()
#         magnitude = math.sqrt(ax*ax + ay*ay + az*az)
#         vibration = abs(magnitude - 1.0)
#         return vibration
#     
#     def set_mock_vibration(self, level):
#         """Set the mock vibration level for testing"""
#         self.mock_vibration_level = max(0.0, min(1.0, level))
#         print(f"Mock vibration level set to: {self.mock_vibration_level}")

# mpu6050_sensor.py - Real hardware I2C-based MPU6050 reader
import smbus2
import time
import math

class MPU6050:
    def __init__(self, bus=1, address=0x68, mock_mode=False):
        self.mock_mode = mock_mode
        self.address = address

        if not self.mock_mode:
            self.bus = smbus2.SMBus(bus)
            self.bus.write_byte_data(self.address, 0x6B, 0)  # Wake up sensor
            print("MPU6050 initialized in REAL MODE")
        else:
            print("MPU6050 initialized in MOCK MODE")
            self.mock_vibration_level = 0.0

    def get_acceleration(self):
        if self.mock_mode:
            import random
            noise = random.uniform(-0.05, 0.05)
            vibration = random.uniform(-self.mock_vibration_level, self.mock_vibration_level)
            ax = 0.05 + noise + vibration
            ay = 0.02 + noise + vibration
            az = 0.98 + noise + vibration
            return (ax, ay, az)

        def read_word(reg):
            high = self.bus.read_byte_data(self.address, reg)
            low = self.bus.read_byte_data(self.address, reg + 1)
            val = (high << 8) + low
            return val if val < 32768 else val - 65536

        # Read raw acceleration data
        raw_ax = read_word(0x3B)
        raw_ay = read_word(0x3D)
        raw_az = read_word(0x3F)

        # Convert to g's (sensitivity = 16384 LSB/g)
        ax = raw_ax / 16384.0
        ay = raw_ay / 16384.0
        az = raw_az / 16384.0

        return (ax, ay, az)

    def get_vibration_magnitude(self):
        ax, ay, az = self.get_acceleration()
        magnitude = math.sqrt(ax*ax + ay*ay + az*az)
        vibration = abs(magnitude - 1.0)
        return vibration

    def set_mock_vibration(self, level):
        if self.mock_mode:
            self.mock_vibration_level = max(0.0, min(1.0, level))
            print(f"Mock vibration level set to: {self.mock_vibration_level}")
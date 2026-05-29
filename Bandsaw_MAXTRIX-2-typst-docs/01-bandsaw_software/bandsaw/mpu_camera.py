# mpu_camera.py
import smbus2
import math
import time

class MPU6050Monitor:
    def __init__(
        self,
        bus_id=1,
        address=0x68,
        accel_threshold=0.3,
        inactivity_timeout=7,
    ):
        self.address = address
        self.accel_threshold = accel_threshold
        self.inactivity_timeout = inactivity_timeout

        self.bus = smbus2.SMBus(bus_id)
        self.bus.write_byte_data(self.address, 0x6B, 0)  # Start

        self.prev_magnitude = None
        self.last_motion_time = time.time()



    def read_mpu6050(self):
        def read_word(reg):
            high = self.bus.read_byte_data(self.address, reg)
            low = self.bus.read_byte_data(self.address, reg + 1)
            val = (high << 8) + low
            if val >= 0x8000:
                val = -((65535 - val) + 1)
            return val / 4096.0

        ax = self.read_word(0x3B)
        ay = self.read_word(0x3D)
        az = self.read_word(0x3F)
        return ax, ay, az

    # nethod
    def bandsaw_active(self):

        try:
            ax, ay, az = self.read_mpu6050()
            magnitude = math.sqrt(ax**2 + ay**2 + az**2)

            if self.prev_magnitude is not None:
                delta = abs(magnitude - self.prev_magnitude)
                if delta > self.ACCEL_THRESHOLD:
                    last_motion_time = time.time()

            self.prev_magnitude = magnitude
            active = (time.time() - last_motion_time) < self.INACTIVITY_TIMEOUT
            return active

        except RuntimeError as e:
            print("MPU6050 read error:", e)
            return True  # Fail-safe

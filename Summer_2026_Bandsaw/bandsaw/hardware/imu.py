"""MPU6050 motion sensing with injectable bus and clock dependencies."""

import math
import time
from typing import Callable, Optional


MPU6050_ADDR = 0x68
ACCEL_THRESHOLD = 0.25
INACTIVITY_TIMEOUT = 30


class MPU6050MotionSensor:
    """Read acceleration and determine whether the saw is moving."""

    def __init__(
        self,
        bus=None,
        address=MPU6050_ADDR,
        accel_threshold=ACCEL_THRESHOLD,
        inactivity_timeout=INACTIVITY_TIMEOUT,
        clock: Callable[[], float] = time.time,
    ):
        if bus is None:
            try:
                import smbus2
            except ImportError as error:
                raise RuntimeError("MPU6050 support requires smbus2") from error
            bus = smbus2.SMBus(1)

        self.bus = bus
        self.address = address
        self.accel_threshold = accel_threshold
        self.inactivity_timeout = inactivity_timeout
        self.clock = clock
        self.previous_magnitude: Optional[float] = None
        self.last_motion_time = clock()
        self.bus.write_byte_data(self.address, 0x6B, 0)

    def read_acceleration(self):
        def read_word(register):
            high = self.bus.read_byte_data(self.address, register)
            low = self.bus.read_byte_data(self.address, register + 1)
            value = (high << 8) + low
            if value >= 0x8000:
                value -= 0x10000
            return value / 4096.0

        return (
            read_word(0x3B),
            read_word(0x3D),
            read_word(0x3F),
        )

    def is_active(self):
        ax, ay, az = self.read_acceleration()
        magnitude = math.sqrt(ax ** 2 + ay ** 2 + az ** 2)

        if self.previous_magnitude is not None:
            if abs(magnitude - self.previous_magnitude) > self.accel_threshold:
                self.last_motion_time = self.clock()

        self.previous_magnitude = magnitude
        return self.clock() - self.last_motion_time < self.inactivity_timeout


_default_sensor = None


def _get_default_sensor():
    global _default_sensor
    if _default_sensor is None:
        _default_sensor = MPU6050MotionSensor()
    return _default_sensor


def read_mpu6050():
    return _get_default_sensor().read_acceleration()


def bandsaw_active():
    try:
        return _get_default_sensor().is_active()
    except Exception as error:
        print("MPU6050 read error:", error)
        return True

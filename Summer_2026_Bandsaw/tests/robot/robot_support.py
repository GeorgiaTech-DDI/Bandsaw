"""Robot Framework keywords for deterministic, hardware-free tests."""

import numpy as np

from bandsaw.hardware.imu import MPU6050MotionSensor
from bandsaw.geometry import check_hand_near_boundary as _check_hand_near_boundary
from bandsaw.vision.hands import expand_bounding_box as _expand_bounding_box
from bandsaw.vision.slit import SlitDetector


class FakeBus:
    def __init__(self):
        self.registers = {}
        self.set_acceleration((0, 0, 4096))

    def write_byte_data(self, address, register, value):
        self.registers[register] = value

    def read_byte_data(self, address, register):
        return self.registers.get(register, 0)

    def set_acceleration(self, values):
        for register, value in zip((0x3B, 0x3D, 0x3F), values):
            encoded = value & 0xFFFF
            self.registers[register] = encoded >> 8
            self.registers[register + 1] = encoded & 0xFF


_bus = None
_sensor = None
_now = 100.0


def create_fake_motion_sensor():
    global _bus, _sensor, _now
    _now = 100.0
    _bus = FakeBus()
    _sensor = MPU6050MotionSensor(bus=_bus, clock=lambda: _now)


def set_fake_acceleration(acc_x, acc_y, acc_z):
    _bus.set_acceleration((int(acc_x), int(acc_y), int(acc_z)))


def set_test_clock(timestamp):
    global _now
    _now = float(timestamp)


def saw_is_active():
    return _sensor.is_active()


def read_fake_acceleration():
    return _sensor.read_acceleration()


def hand_is_near_slit(hand_bbox, slit_bbox):
    hand = None if hand_bbox is None else tuple(int(value) for value in hand_bbox)
    slit = None if slit_bbox is None else tuple(float(value) for value in slit_bbox)
    return _check_hand_near_boundary(hand, slit)


def expanded_hand_box(x, y, width, height, scale=1.5, frame_shape=None):
    shape = None if frame_shape is None else tuple(int(value) for value in frame_shape)
    return _expand_bounding_box(
        int(x), int(y), int(width), int(height), float(scale), shape
    )


def blank_slit_calibration_is_missing():
    detector = SlitDetector(stabilization_time=0)
    detector.start_detection()
    slit, _ = detector.detect_slit(np.zeros((120, 160, 3), dtype=np.uint8))
    return slit is None and detector.is_slit_missing()
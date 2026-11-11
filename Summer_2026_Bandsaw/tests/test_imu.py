import unittest

from bandsaw.hardware.imu import MPU6050MotionSensor


class FakeBus:
    def __init__(self, acceleration=(0, 0, 4096)):
        self.registers = {}
        self.write_byte_data(0x68, 0x6B, 0)
        self.set_acceleration(acceleration)

    def write_byte_data(self, address, register, value):
        self.registers[register] = value

    def read_byte_data(self, address, register):
        return self.registers.get(register, 0)

    def set_acceleration(self, values):
        for register, value in zip((0x3B, 0x3D, 0x3F), values):
            encoded = value & 0xFFFF
            self.registers[register] = encoded >> 8
            self.registers[register + 1] = encoded & 0xFF


class MPU6050MotionSensorTests(unittest.TestCase):
    def test_sensor_can_use_injected_bus_without_hardware_package(self):
        timestamps = iter((100.0, 100.0, 100.1, 100.1))
        bus = FakeBus()
        sensor = MPU6050MotionSensor(bus=bus, clock=lambda: next(timestamps))

        self.assertTrue(sensor.is_active())
        bus.set_acceleration((0, 0, 0))
        self.assertTrue(sensor.is_active())
        self.assertAlmostEqual(sensor.previous_magnitude, 0.0)

    def test_legacy_module_import_does_not_open_sensor(self):
        import mpu_camera
        from bandsaw.hardware import imu

        self.assertTrue(callable(mpu_camera.bandsaw_active))
        self.assertIsNone(imu._default_sensor)


if __name__ == "__main__":
    unittest.main()
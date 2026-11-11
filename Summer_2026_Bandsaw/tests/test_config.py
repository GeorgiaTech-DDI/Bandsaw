import unittest

from bandsaw.config import MonitorConfig, parse_arguments


class MonitorConfigTests(unittest.TestCase):
    def test_defaults_target_raspberry_pi_camera(self):
        self.assertEqual(parse_arguments([]), MonitorConfig())

    def test_file_source_and_options_are_independent_of_hardware(self):
        config = parse_arguments([
            "--video", "sample.mp4",
            "--record", "clips",
            "--stabilization", "3.5",
            "--alert-interval", "1.25",
            "--debug",
        ])

        self.assertEqual(config.video, "sample.mp4")
        self.assertEqual(config.record, "clips")
        self.assertEqual(config.stabilization, 3.5)
        self.assertEqual(config.alert_interval, 1.25)
        self.assertTrue(config.debug)


if __name__ == "__main__":
    unittest.main()
"""Command-line configuration for the production monitor."""

import argparse
from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class MonitorConfig:
    debug: bool = False
    video: str = "picamera"
    record: str = "recordings"
    threshold: float = 0.5
    stabilization: float = 5.0
    alert_interval: float = 2.0


def parse_arguments(argv: Optional[Sequence[str]] = None) -> MonitorConfig:
    parser = argparse.ArgumentParser(
        description="Bandsaw Safety Monitoring System",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument(
        "--video", default="picamera",
        help="Source: picamera, webcam index, or video file",
    )
    parser.add_argument("--record", default="recordings", help="Recording directory")
    parser.add_argument(
        "--threshold", type=float, default=0.5,
        help="Vibration threshold (retained for the legacy entry point)",
    )
    parser.add_argument(
        "--stabilization", type=float, default=5.0,
        help="Slit detection stabilization time in seconds",
    )
    parser.add_argument(
        "--alert-interval", type=float, default=2.0,
        help="Minimum time between alerts in seconds",
    )
    return MonitorConfig(**vars(parser.parse_args(argv)))

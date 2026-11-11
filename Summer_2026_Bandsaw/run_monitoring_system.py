#!/usr/bin/env python3
"""
Bandsaw Monitoring System - Wrapper Script
This script provides a simple interface to run the monitoring system
with various command-line options.
"""

import os
import sys
import argparse
import time
import signal
import subprocess

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'opencv-python',
        'numpy',
        # Optional packages
        'mediapipe'
    ]
    
    missing_packages = []
    optional_missing = []
    
    # Check each package
    for package in required_packages:
        try:
            if package == 'opencv-python':
                import cv2
            elif package == 'numpy':
                import numpy
            elif package == 'mediapipe':
                try:
                    import mediapipe
                except ImportError:
                    optional_missing.append(package)
        except ImportError:
            missing_packages.append(package)
    
    # Report results
    if missing_packages:
        print("ERROR: Missing required packages:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print("\nPlease install them using:")
        print(f"  pip install {' '.join(missing_packages)}")
        return False
    
    if optional_missing:
        print("WARNING: Some optional packages are missing:")
        for pkg in optional_missing:
            print(f"  - {pkg}")
        print("\nThe system will run with reduced functionality.")
        print("To install optional packages:")
        print(f"  pip install {' '.join(optional_missing)}")
    
    return True

def setup_arguments():
    """Set up command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Bandsaw Safety Monitoring System",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Basic arguments
    parser.add_argument('--debug', action='store_true', 
                        help='Run in debug mode with simulated sensors')
    parser.add_argument('--video', type=str, default='0',
                        help='Video source (0 for webcam, or path to video file)')
    parser.add_argument('--record', type=str, default='recordings',
                        help='Directory to save recordings')
    
    # Advanced settings
    advanced = parser.add_argument_group('Advanced Settings')
    advanced.add_argument('--threshold', type=float, default=0.5,
                         help='Vibration threshold for bandsaw detection')
    advanced.add_argument('--stabilization', type=float, default=5.0,
                         help='Stabilization time for slit detection (seconds)')
    advanced.add_argument('--alert-interval', type=float, default=2.0,
                         help='Minimum time between alerts (seconds)')
    
    return parser.parse_args()

def run_monitoring_system(args):
    """Run the monitoring system with the specified arguments"""
    # Prepare command
    cmd = [sys.executable, 'main.py']
    
    if args.debug:
        cmd.append('--debug')
    
    cmd.extend(['--video', args.video])
    cmd.extend(['--record', args.record])
    cmd.extend(['--threshold', str(args.threshold)])
    cmd.extend(['--stabilization', str(args.stabilization)])
    cmd.extend(['--alert-interval', str(args.alert_interval)])
    
    # Run the system
    try:
        print(f"Starting Bandsaw Monitoring System with command: {' '.join(cmd)}")
        process = subprocess.Popen(cmd)
        
        # Wait for the process to complete
        process.wait()
        
        return process.returncode
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, stopping monitoring system...")
        process.send_signal(signal.SIGINT)
        time.sleep(1)
        if process.poll() is None:
            process.terminate()
        return 1
    except Exception as e:
        print(f"Error running monitoring system: {e}")
        return 1

def main():
    """Main entry point"""
    print("Bandsaw Safety Monitoring System - Wrapper Script")
    print("===============================================")
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Parse arguments
    args = setup_arguments()
    
    # Create recordings directory if it doesn't exist
    if not os.path.exists(args.record):
        os.makedirs(args.record)
        print(f"Created recordings directory: {args.record}")
    
    # Run the monitoring system
    return run_monitoring_system(args)

if __name__ == "__main__":
    sys.exit(main())
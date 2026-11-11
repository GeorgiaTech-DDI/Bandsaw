#!/usr/bin/env python3
"""
Setup script for the Bandsaw Safety Monitoring System
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    required_version = (3, 6)
    current_version = sys.version_info
    
    if current_version < required_version:
        print(f"Error: Python {required_version[0]}.{required_version[1]}+ is required.")
        print(f"You are using Python {current_version[0]}.{current_version[1]}.{current_version[2]}")
        return False
    
    return True

def install_requirements():
    """Install required packages"""
    requirements_file = "requirements.sty"
    
    if not os.path.exists(requirements_file):
        print(f"Error: {requirements_file} not found.")
        return False
    
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
        print("Package installation completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        return False

def setup_raspberry_pi():
    """Configure Raspberry Pi-specific settings"""
    # Check if we're on a Raspberry Pi
    if "raspberrypi" not in platform.node().lower() and not os.path.exists("/proc/device-tree/model"):
        print("This is not a Raspberry Pi. Skipping Raspberry Pi setup.")
        return True
    
    print("Detected Raspberry Pi. Setting up specific configurations...")
    
    # Install RPi.GPIO
    try:
        print("Installing RPi.GPIO package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "RPi.GPIO"])
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to install RPi.GPIO: {e}")
        print("You may need to run this script with sudo for GPIO access.")
    
    # Create a systemd service file for autostart
    service_file = "/tmp/bandsaw-monitoring.service"
    current_dir = os.path.abspath(os.path.dirname(__file__))
    
    service_content = f"""[Unit]
Description=Bandsaw Safety Monitoring System
After=network.target

[Service]
ExecStart={sys.executable} {os.path.join(current_dir, "run_monitoring_system.py")}
WorkingDirectory={current_dir}
StandardOutput=inherit
StandardError=inherit
Restart=always
User={os.getenv('USER', 'pi')}

[Install]
WantedBy=multi-user.target
"""
    
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        print("\nCreated systemd service file.")
        print("To install the service for autostart, run:")
        print(f"sudo mv {service_file} /etc/systemd/system/")
        print("sudo systemctl daemon-reload")
        print("sudo systemctl enable bandsaw-monitoring.service")
        print("sudo systemctl start bandsaw-monitoring.service")
    except Exception as e:
        print(f"Warning: Failed to create service file: {e}")
    
    print("Raspberry Pi setup completed.")
    return True

def create_test_dirs():
    """Create required directories"""
    dirs = ["recordings"]
    
    for directory in dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

def main():
    """Main setup function"""
    print("Setting up Bandsaw Safety Monitoring System...")
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Install requirements
    if not install_requirements():
        return 1
    
    # Create directories
    create_test_dirs()
    
    # Raspberry Pi setup
    setup_raspberry_pi()
    
    print("\nSetup completed successfully!")
    print("You can now run the system using:")
    print("python run_monitoring_system.py --debug")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
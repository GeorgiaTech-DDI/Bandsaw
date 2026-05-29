#set document(
  title: "Bandsaw Monitor Quick Start Guide",
  author: "MATRIX Team",
  date: datetime.today(),
)

#set page(
  paper: "a4",
  margin: (left: 1.5cm, right: 1.5cm, top: 2cm, bottom: 2cm),
  numbering: "1",
  number-align: center,
  footer: [
    #set text(size: 9pt, fill: gray)
    Bandsaw Monitor System Documentation 
  ],
)

#set text(font: "Calibri", size: 11pt)
#set heading(numbering: "1.1.1")


//TITLE PAGE


#align(center)[
  #v(2cm)
  #text(size: 28pt, weight: "bold")[Bandsaw Monitor System Quick Start]
  #v(0.5cm)
  #text(size: 14pt, fill: gray)[User & Operator Guide]
  #v(3cm)
  #text(size: 12pt)[MATRIX Project]
  #v(0.5cm)
  #text(size: 10pt, fill: gray)[Version 1.0 - #datetime.today().display("[month repr:long] [day], [year]")]
  #v(2cm)
]

#pagebreak()

// TABLE OF CONTENTS

#outline(title: "Table of Contents", depth: 2)

#pagebreak()

// OVERVIEW

= Overview

== What is the Bandsaw Monitor System?

The Bandsaw Monitor System is a real-time safety monitoring solution designed to protect operators during bandsaw operations. Using computer vision and AI-powered hand detection, the system continuously monitors for operator hands near the cutting blade. When a hand enters the danger zone while the blade is active, the system immediately triggers visual alerts to prevent injuries.

*Key Features:*
- Real-time hand detection using MediaPipe
- Blade and slit position tracking 
- GUI dashboard for monitoring and configuration
- Future Containerized deployment through Docker

== System Components

The Bandsaw Monitor System consists of:

- *Video Capture*: Real-time video processing from camera feeds
- *Hand Detection*: AI-powered hand presence detection for safety monitoring
- *Slit Detection*: Blade and workpiece position detection
- *Alerts*: Notification system for safety events
- *Monitoring Dashboard*: GUI for system status and monitoring

=== System Architecture Diagram

#figure(
  table(
    columns: (1fr,),
    stroke: (x, y) => (
      left: if x == 0 { 2pt } else { 0pt },
      right: if x == 1 { 2pt } else { 0pt },
      top: if y == 0 { 2pt } else { 0pt },
      bottom: if y == 5 { 2pt } else { 0pt },
    ),
    inset: 10pt,
    align: left,
    [*Bandsaw Monitor System Architecture*, Chat GPT-generated diagram illustrating component flow and data paths],
    [],
    box(
      width: 100%,
      inset: 8pt,
      stroke: 1pt + rgb("222222"),
      [
        ```
        ┌─────────────────────────────────────────────────────┐
        │                   INPUT SOURCES                      │
        │   ┌──────────────┐          ┌──────────────┐        │
        │   │ Pi Camera /  │          │   USB Video  │        │
        │   │   Webcam     │          │    Source    │        │
        │   └────────┬─────┘          └──────┬───────┘        │
        └────────────┼──────────────────────┼────────────────┘
                     │                      │
                     └──────────┬───────────┘
                                │
        ┌───────────────────────▼────────────────────────────┐
        │              VIDEO CAPTURE MODULE                  │
        │     (PiCameraCapture / VideoRecorder)             │
        └───────────────────────┬────────────────────────────┘
                                │ Frame Stream (30fps)
        ┌───────────────────────▼────────────────────────────┐
        │          PROCESSING PIPELINE (Threading)           │
        └──┬────────────────────┬─────────────────────┬──────┘
           │                    │                     │
        ┌──▼────────┐    ┌──────▼──────┐    ┌────────▼─────┐
        │   Hand    │    │    Slit     │    │   Bandsaw    │
        │ Detection │    │  Detection  │    │   Active?    │
        │ (MediaPipe)    │ (Stabilizer)│    │  (MPU6050)   │
        └──┬────────┘    └──────┬──────┘    └────────┬─────┘
           │   Hand Box         │ Slit Box          │ Active?
           └────────────┬───────┴────────┬──────────┘
                        │                │
        ┌───────────────▼────────────────▼──────────────────┐
        │      SAFETY LOGIC MODULE                         │
        │  check_hand_near_boundary()                      │
        │  ├─ Hand detected?                               │
        │  ├─ Slit detected?                               │
        │  └─ Proximity < threshold?  → ALERT TRIGGERED!  │
        └───────────────┬───────────────────────────────────┘
                        │ Risk Level
        ┌───────────────▼─────────────────────────────────┐
        │            ALERT SYSTEM                         │
        │   ┌──────────────────────────────────────┐      │
        │   │  NeoPixel LED Strip Controller       │      │
        │   │  ├─ Blink Pattern (Red 0.3s)        │      │
        │   │  ├─ Alert Threading                 │      │
        │   │  └─ Minimum Interval Throttling     │      │
        │   └──────────────────────────────────────┘      │
        └────────────┬─────────────────────────────────────┘
                     │ Visual Alert
        ┌────────────▼──────────────────────────────────────┐
        │            OUTPUT & MONITORING                   │
        │   ┌─────────────────┐    ┌──────────────────┐   │
        │   │ Video Recording │    │ PyQt5 Dashboard  │   │
        │   │ (MP4 clips)     │    │ + Alerts Log     │   │
        │   └─────────────────┘    └──────────────────┘   │
        └─────────────────────────────────────────────────┘
        ```
      ]
    ),
  ),
  caption: "Figure 1: System Architecture - Component Flow and Data Paths"
)

#pagebreak()

//GETTING STARTED

= Getting Started

== System Requirements

*Hardware Requirements:*
- Camera: Raspberry Pi Camera Module 
- Processor: Raspberry Pi 5


*Software Requirements:*
- Python 3.11 or higher
- Operating System: Raspberry Pi OS / Ubuntu Linux / Windows 10+
- Dependencies installed: numpy, opencv-python, mediapipe, smbus2, picamera2

=== Hardware Block Diagram

#figure(
  table(
    columns: (1fr,),
    stroke: (x, y) => (
      left: if x == 0 { 2pt } else { 0pt },
      right: if x == 1 { 2pt } else { 0pt },
      top: if y == 0 { 2pt } else { 0pt },
      bottom: if y == 1 { 2pt } else { 0pt },
    ),
    inset: 10pt,
    align: left,
    [*Hardware Block Diagram*, Chat GPT-generated diagram illustrating component flow and data paths],
    box(
      width: 100%,
      inset: 8pt,
      stroke: 1pt + rgb("222222"),
      [
        ```
        SENSORS & INPUT                PROCESSING              OUTPUT & ACTUATION
        ═══════════════════════════════════════════════════════════════════════════

        ┌─────────────────┐                                ┌────────────────────┐
        │ Raspberry Pi    │       ┌────────────────┐      │
        │ Camera Module   ├──────▶│ Raspberry Pi 5 │      │      │
        │ (CSI Interface) │       │ or Desktop PC  │ SPI──▶│ (Expansion)        │
        │ +5V / GND       │       │                │      │          │
        └─────────────────┘       │  MemFree:      │      └────────────────────┘
                                  │  • 4GB RAM min │
        ┌─────────────────┐       │  • 8GB ideal   │      ┌────────────────────┐
        │ MPU6050 Accel   │ I2C───│                │      │  Monitor Display   │
        │ (Optional)      │       │  Bandsaw       │ HDMI │  / USB Devices     │
        │ SDA / SCL       │       │  Monitor App   │◀─────│  (PyQt5 GUI)       │
        │ +3.3V / GND     │       │                │      └────────────────────┘
        └─────────────────┘       └────────────────┘
                        

        POWER DISTRIBUTION & CONNECTIVITY:
        • Raspberry Pi:  USB Power 5V 3A minimum
        • Network:       Ethernet or WiFi (built-in on Pi 5)
        ```
      ]
    ),
  ),
  caption: "Figure 2: Hardware Connections and Pin Layout"
)

== Installation


=== Option 1: From Source

```bash
git clone https://github.com/GeorgiaTech-DDI/bandsaw.git
cd bandsaw/01-bandsaw_software
pip install -e .
```

*Additional Setup for Raspberry Pi:*
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pil python3-numpy python3-pip
```

== Initial Setup

1. *Hardware Connections*: Connect camera to CSI port (Raspberry Pi) or USB port (Desktop). Connect power.
2. *Verify Camera Detection*: Run `libcamera-hello` (Pi) or test with v4l2-ctl to confirm camera is detected and working.
3. *Validate Dependencies*: Run the test suite with `pytest tests/robot/` to ensure all modules load correctly.
4. *Test System*: Launch the monitoring system with `python -m bandsaw.bandsaw_monitor --debug` to verify hand detection and alerts are working.

#pagebreak()

// CORE FEATURES

= Core Features

== Video Capture

=== Overview

The video capture module handles real-time images from Raspberry Pi Camera.


=== Video Processing Pipeline Diagram

#figure(
  table(
    columns: (1fr,),
    stroke: (x, y) => (
      left: if x == 0 { 2pt } else { 0pt },
      right: if x == 1 { 2pt } else { 0pt },
      top: if y == 0 { 2pt } else { 0pt },
      bottom: if y == 1 { 2pt } else { 0pt },
    ),
    inset: 10pt,
    align: left,
    [*Video Processing Data Flow*, Chat GPT-generated diagram illustrating component flow and data paths],
    box(
      width: 100%,
      inset: 8pt,
      stroke: 1pt + rgb("222222"),
      [
        ```
        ┌──────────────────────────────────────────────────────┐
        │ INPUT: Camera Frame (30 FPS, 1920x1080 or variable) │
        └────────────────┬─────────────────────────────────────┘
                         │
        ┌────────────────▼─────────────────────────────────────┐
        │ THREAD 1: Capture Thread (Non-blocking)             │
        │ • Read frame from camera                            │
        │ • Update shared buffer (thread-safe)               │
        │ • Minimal processing (fast loop: < 50ms/frame)     │
        └────────────────┬─────────────────────────────────────┘
                         │
                    Frame Buffer
                         │
        ┌────────────────▼─────────────────────────────────────┐
        │ THREAD 2: Processing Thread                         │
        │ ├─ Hand Detection (MediaPipe)                       │
        │ ├─ Slit Detection (Edge Analysis)                   │
        │ ├─ Generate Annotations                            │
        │ └─ Safety Logic (Proximity Check)                   │
        │ Processing Time: 50-100ms per frame (10-20 FPS)    │
        └────────────────┬──────────────┬──────────────────────┘
                         │              │
            Detection Results      Annotated Frame
                         │              │
        ┌───────────────▼┐    ┌────────▼──────────────────────┐
        │ THREAD 3 Part A:    │ THREAD 3 Part B:               │
        │ Alert Dispatcher    │ Video Recording Thread        │
        │ ├─ Risk Level       │ ├─ Buffer frames              │
        │ ├─ Threshold Check  │ ├─ Write to file (H.264)      │
        │ └─ Signal Alert     │ └─ Maintain circular buffer   │
        │                     │ (Only records on alert)       │
        └─────────┬───────────┴────────────────────────────────┘
                  │
        ┌─────────▼──────────────────────────────────────────┐
        │ OUTPUT                                             │
        │ ├─ Alert Triggered                                 │
        │ ├─ Video Clip → MP4 File in ./recordings/         │
        │ ├─ GUI Display → PyQt5 Dashboard                  │
        │ └─ Logs → Console + File                          │
        └────────────────────────────────────────────────────┘
        ```
      ]
    ),
  ),
  caption: "Figure 3: Multi-threaded Video Processing Pipeline"
)

=== Configuration

Configure via command-line arguments when launching the monitor:

```bash
python -m bandsaw.bandsaw_monitor \
  --video 0 \
```

=== Troubleshooting

*Issue: "Cannot open camera"*
- Verify camera is physically connected
- Check permissions: `sudo usermod -a -G video $USER`

---

== Hand Detection

=== Overview

Hand detection uses *Google MediaPipe Hands*, a state-of-the-art real-time hand tracking model. The system can detect up to 2 hands simultaneously with 21 landmark points per hand, enabling precise bounding box calculation. The model uses machine learning to identify hands and their position regardless of orientation or size.
=== Configuration

Configuration is currently hardcoded in `hand_detection.py`:

```python
hands_detector = mp.solutions.hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
```

== Slit Detection

=== Overview

Slit detection tracks the blade position and cutting boundaries during bandsaw operation. The system identifies where the blade intersects with the material and maintains a stabilized estimate of the active cutting area. This information is used to determine if detected hands are actually in the danger zone.

*How It Works:*
- Analyzes frame contrast to identify blade edges
- Tracks slit position across consecutive frames
- Applies temporal smoothing to reduce jitter
- Stores detected slit position over a configurable stabilization period
- Finalizes slit position once threshold is met

=== Configuration

Configure via command-line arguments:

```bash
python -m bandsaw.bandsaw_monitor \
  --stabilization 5.0 \
  --threshold 0.5
```

*Configuration Parameters:*
- `--stabilization SECONDS`: Time window for slit position stabilization (default: 5.0 seconds). Longer = more stable but slower to detect changes
- `--threshold VALUE`: Vibration/motion threshold (default: 0.5, currently unused)

*Tuning Guidance:*
- Lower stabilization time (2-3s) for faster response, less stable detection
- Higher stabilization time (7-10s) for more stable position tracking, slower response to blade movement
- Typical range: 3-5 seconds

=== Usage

The slit detection is automatically managed by the BandsawMonitor class:

```python
from bandsaw.slit_detection import SlitDetector

slit_detector = SlitDetector(
    stabilization_time=5.0,
    debug=True  # Enables console output
)

# Start detection when bandsaw begins operation
slit_detector.start_detection()

# In monitoring loop
slit_bbox = slit_detector.detect(frame)
# slit_bbox = (x, y, width, height, angle) or None

# Stop detection when bandsaw stops
slit_detector.stop_detection()
```



== Alert System

=== Overview

The alert system provides immediate visual feedback when safety conditions are violated. When a hand is detected approaching or entering the slit (blade area), the system activates addressable NeoPixel LED strips to create a blinking alert pattern. This provides real-time feedback to both the operator and nearby personnel.


=== Alert Types

- *Hand Detected Near Slit*: Steady red blinking (0.3 second intervals) when hand bounding box overlaps with blade area
- *High-Risk Proximity*: Continuous red illumination for critical danger zone violations
- *System Clear*: Green when hand leaves danger zone or bandsaw becomes inactive

*Alert Timing:*
- Minimum alert interval: 2.0 seconds (prevents alert spam from multiple detections)
- Blink interval: 0.3 seconds (fast, attention-grabbing)
- Alert colors: Red (0xFF0000) for danger can be customized

=== Configuring Alerts

Configure via command-line arguments:

```bash
python -m bandsaw.bandsaw_monitor \
  --alert-interval 2.0
```

*Configuration Parameters:*
- `--alert-interval SECONDS`: Minimum time between consecutive alerts (default: 2.0 seconds)

*Programmatic Configuration:*

```python
from bandsaw.alert import start_alert, stop_alert, clear_alert

# Trigger red alert
start_alert(color=(255, 0, 0))  # RGB tuple

# Stop alert (turn off LEDs)
stop_alert()

# Clear all LEDs
clear_alert()
```

*Customization:*
Edit `alert.py` to change:
- `NUM_PIXELS`: Number of LEDs in your strip
- `brightness`: LED brightness (0.0-1.0)
- Color values in `start_alert()` calls


#pagebreak()

//  USING THE DASHBOARD

= Using the Dashboard

== Launching the Application

*Option 1: Command-line Monitoring (Recommended for Raspberry Pi)*

```bash
python -m bandsaw.bandsaw_monitor --debug
```

*Option 2: PyQt5 GUI Dashboard*

```bash
python gui/pyqt_app.py
```

The GUI provides a graphical interface with real-time video feed visualization and alert status.

*Option 3: Headless Remote Monitoring*

```bash
python gui/headless_monitor.py --host 0.0.0.0 --port 5000
```

== Dashboard Interface

The PyQt5 dashboard provides the following components:

- *Status Panel*: Displays current system state (Running/Stopped), bandsaw active status, detected hands, alert count
- *Live Video Feed*: Real-time camera stream with hand detection bounding boxes and slit detection overlay
- *Alerts Log*: Chronological list of all detected hand-slit proximity events with timestamps
- *Settings Panel*: Adjustable parameters for detection sensitivity, alert thresholds, and recording options
- *Control Buttons*: Start/Stop monitoring, Clear alerts, Export video clips

== Common Tasks

=== Start Monitoring

1. Launch the monitor: `python -m bandsaw.bandsaw_monitor`
2. Verify camera stream appears in terminal or GUI
3. System is now actively monitoring for hand detection

=== Stop Monitoring

1. Press `Ctrl+C` in terminal 
2. Any active recordings will be saved to the recordings directory

=== View Alert History

1. Alerts are logged in real-time during monitoring
2. Check the alerts log file: `./logs/alerts.log`
3. In GUI: View the Alerts Log panel which shows all detections with timestamps
4. Each entry shows: timestamp, hand count, slit status, proximity level

=== Export Data

1. Video recordings are automatically saved to the `recordings/` directory
2. Export format: MP4 video files named with timestamp
3. To manually export: Copy the recordings folder to external storage
4. Logs can be exported as CSV: `python -m bandsaw.utils.export_logs output.csv`

// TROUBLESHOOTING

= Troubleshooting

== Common Issues

=== Issue: Camera Not Detected

*Symptoms:* "Error: No camera available" or black/frozen video feed

*Solutions:*
1. *For Raspberry Pi Camera:* Enable CSI camera in raspi-config:
   ```bash
   sudo raspi-config
   # Navigate to: Interface Options > Camera > Enable
   # Reboot
   ```

2. *Verify camera connection:*
   ```bash
   libcamera-hello --verbose  # Pi OS
   v4l2-ctl --list-devices   # Linux
   ```

3. *Check permissions:*
   ```bash
   sudo usermod -a -G video $USER
   # Log out and back in, or use: newgrp video
   ```

4. *Try alternative video source:*
   ```bash
   # Test USB webcam
   python -m bandsaw.bandsaw_monitor --video /dev/video0
   ```

5. *Debug camera initialization:*
   ```bash
   python -m bandsaw.bandsaw_monitor --debug
   # Look for camera initialization messages in output
   ```

---

=== Issue: Hand Detection Not Working

*Symptoms:* No bounding boxes appear around hands, or constant false detections

*Solutions - No Detection:*
1. *Verify lighting:* Hand detection requires adequate lighting. Test the camera feed visually first.
   ```bash
   libcamera-hello  # Or run GUI to see raw video
   ```

2. *Check MediaPipe installation:*
   ```bash
   python -c "import mediapipe; print(mediapipe.__version__)"
   # Should print version (e.g., 0.10.32)
   ```

3. *Lower detection sensitivity:*
   - Edit `bandsaw/hand_detection.py` line 14
   - Change `min_detection_confidence=0.7` to `0.5 or 0.6`
   - More permissive but may increase false positives

4. *Debug hand detection:*
   ```python
   from bandsaw.hand_detection import detect_hands
   import cv2
   cap = cv2.VideoCapture(0)
   ret, frame = cap.read()
   hands, annotated = detect_hands(frame)
   print(f"Detected {len(hands)} hands")
   ```

*Solutions - Too Many False Detections:*
1. *Increase confidence threshold:* Edit line 14, change to `min_detection_confidence=0.85`
2. *Improve lighting:* Better lighting reduces false detection in shadows
3. *Clean camera lens:* Smudged lens causes detection errors

---

=== Issue: Alerts Not Triggering

1. *Verify hand-slit proximity detection:*
   - Run with `--debug` flag to see detection logs
   - Confirm `check_hand_near_boundary()` returns True
   - May need to adjust bounding box thresholds in `bandsaw_monitor.py`!!!

2. *Check alert interval:*
   - Reduce interval: `--alert-interval 1.0`

---

=== Issue: System Performance is Slow

*Symptoms:* Low FPS (< 5 fps), laggy video, delayed detections (>500ms)

*Solutions:*
1. *Check system resources:*
   ```bash
   top  # Monitor CPU and memory usage
   # Typical usage: 15-20% CPU, 100-200MB RAM
   ```

2. *Reduce video resolution:* Edit `bandsaw/video_capture.py`
   - Lower resolution = faster processing
   - Change resolution configuration from 1920x1080 to 1280x720 or 640x480
---


//  FAQ

= Frequently Asked Questions

*Q: How often should I maintain the system?*

A: Maintenance recommendations:
- *Monthly*: Clean camera lens with soft, dry cloth
- *Quarterly*: Check NeoPixel LED connections for corrosion
- *Annually*: Replace camera if dust buildup prevents focus
- *As needed*: Update software with `pip install --upgrade bandsaw`

---

*Q: Can I customize the alerts?*

A: Yes. Modify `bandsaw/alert.py` to:
- Change LED color: Edit RGB values in `start_alert()` call
- Change blink pattern: Modify interval in `_blink_loop()` function
- Change number of LEDs: Update `NUM_PIXELS` variable
- Add audio alerts: Integrate sound synthesis library in alert function

---

*Q: What if the system detects false hands (objects, shadows)?*

A: Several mitigation strategies:
1. Increase detection confidence threshold (0.8-0.85) to filter out uncertain detections
2. Improve lighting conditions near the bandsaw
3. Train a custom hand detection model on your specific lighting conditions
4. Implement a confidence-weighted alert system that requires multiple consecutive detections

#pagebreak()

// SUPPORT & RESOURCES

= Support & Resources

== Getting Help

- *Issue Tracker*: https://github.com/GeorgiaTech-DDI/bandsaw/issues
- *GitHub Repository*: https://github.com/GeorgiaTech-DDI/bandsaw
- *MATRIX Lab VIP*: Georgia Tech DDI MatrixLab
- *Email Support*: #raw("rlohan@gatech.edu")

== Additional Resources

- *MediaPipe Documentation*: https://developers.google.com/mediapipe/solutions/vision/hand_landmarker
- *Raspberry Pi Camera Documentation*: https://www.raspberrypi.com/documentation/cameras/
- *NeoPixel LED Documentation*: https://learn.adafruit.com/adafruit-neopixel-uberguide
- *PyQt5 Documentation*: https://www.riverbankcomputing.com/static/Docs/PyQt5/
- *Project Repository*: https://github.com/GeorgiaTech-DDI/bandsaw


*Create an Issue:*
Visit: https://github.com/GeorgiaTech-DDI/bandsaw/issues/new

#pagebreak()

// APPENDIX

= Appendix

== A. Installation Troubleshooting

*Error: "ModuleNotFoundError: No module named 'mediapipe'"*

Solution:
```bash
pip install mediapipe
# For Pi with arm64: May require compilation
pip install mediapipe --no-binary mediapipe
```

*Error: "ModuleNotFoundError: No module named 'picamera2'"*

Solution (Raspberry Pi only):
```bash
sudo apt-get install -y python3-picamera2
```

*Error: "OSError: picamera2 not found"*

Solution: Not on Raspberry Pi hardware. Fall back to OpenCV WebCam:
```python
# Edit bandsaw/bandsaw_monitor.py
# Comment out: self.camera = PiCameraCapture()
# Use: self.cap = cv2.VideoCapture(0)  # Standard webcam
```

== B. Hardware Setup Guide

*Raspberry Pi Camera Setup:*
1. Power off the Raspberry Pi
2. Open camera slot on Pi board
3. Insert ribbon cable (blue contacts face outward)
4. Close and clamp the slot
5. Boot Pi and run: `libcamera-hello`

== C. Command Reference

*Launch Monitoring System:*
```bash
python -m bandsaw.bandsaw_monitor [OPTIONS]
```

*Full Option List:*
```
--debug              Enable debug logging
--video SOURCE       Video source (default: 0, or filepath)
--record DIRECTORY   Recording output directory (default: recordings/)
--threshold VALUE    Vibration threshold (default: 0.5, reserved)
--stabilization SEC  Slit stabilization time (default: 5.0)
--alert-interval SEC Alert minimum interval (default: 2.0)
```

*Launch GUI Dashboard:*
```bash
python gui/pyqt_app.py
```

*Launch Headless Monitor (Web API):*
```bash
python gui/headless_monitor.py --host 0.0.0.0 --port 5000
# Access at: http://<pi-ip>:5000
```

*Run Tests:*
```bash
pytest tests/
pytest --cov=bandsaw tests/ 
```

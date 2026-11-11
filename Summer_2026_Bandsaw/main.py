#!/usr/bin/env python3
"""
Bandsaw Safety Monitoring System - Main Application

This system monitors a bandsaw for safety using:
1. Vibration detection to determine when the bandsaw is active
2. Video processing to detect the bandsaw slit
3. Hand detection to identify when hands are near the slit
4. Alert system to warn when hands are dangerously close to the slit

Usage:
    python main.py [options]

Options:
    --debug             Run in debug mode with simulated sensors
    --video SOURCE      Video source (0 for webcam, path for video file)
    --threshold FLOAT   Vibration threshold for bandsaw detection
    --stabilization SEC Time for slit detection to stabilize
    --alert-interval SEC Minimum time between alerts
"""

import os
import sys
import time
import argparse
import threading
import cv2
import numpy as np

# Import custom modules
from mpu6050_sensor import MPU6050
from vibration_detection import VibrationDetector
from video_capture import open_video_source, get_frame, release_video, VideoRecorder
from hand_detection import detect_hands
from enhanced_slit_detection import SlitDetector
from alert_system import initialize_alerts, trigger_alert

# Global variables
running = True
recording = False
debug_mode = False
current_frame = None
frame_lock = threading.Lock()
bandsaw_active = False
last_alert_time = 0
recorder = None
slit_detector = None


def parse_arguments():
    parser = argparse.ArgumentParser(description="Bandsaw Safety Monitoring System",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--debug', action='store_true', help='Run in debug mode with simulated sensors')
    parser.add_argument('--video', type=str, default='0', help='Video source (0 for webcam, or path to video file)')
    parser.add_argument('--record', type=str, default='recordings', help='Directory to save recordings')
    parser.add_argument('--threshold', type=float, default=0.5, help='Vibration threshold for bandsaw detection')
    parser.add_argument('--stabilization', type=float, default=5.0, help='Stabilization time for slit detection (seconds)')
    parser.add_argument('--alert-interval', type=float, default=2.0, help='Minimum time between alerts (seconds)')
    return parser.parse_args()


def on_bandsaw_state_change(is_active):
    global recorder, recording, slit_detector, current_frame

    if is_active:
        print("🔴 Bandsaw ACTIVE")
        if not recording and current_frame is not None:
            recorder.start(current_frame, "bandsaw_activity")
            slit_detector.start_detection()
            recording = True
    else:
        print("🟢 Bandsaw INACTIVE")
        if recording:
            recorder.stop()
            slit_detector.stop_detection()
            recording = False


def vibration_activity_callback(is_active):
    global bandsaw_active
    if bandsaw_active != is_active:
        bandsaw_active = is_active
        on_bandsaw_state_change(is_active)


def check_hand_proximity(hand_bboxes, slit_bbox, proximity_threshold=50):
    if slit_bbox is None or not hand_bboxes:
        return False, None, None

    sx, sy, sw, sh = slit_bbox[:4]
    slit_center_x = sx + sw / 2
    slit_center_y = sy + sh / 2
    closest_distance = float('inf')
    closest_hand = None

    for hand_bbox in hand_bboxes:
        hx, hy, hw, hh = hand_bbox
        hand_center_x = hx + hw / 2
        hand_center_y = hy + hh / 2
        distance = np.sqrt((hand_center_x - slit_center_x)**2 + (hand_center_y - slit_center_y)**2)
        if distance < closest_distance:
            closest_distance = distance
            closest_hand = hand_bbox

    if closest_distance < proximity_threshold:
        return True, closest_distance, closest_hand

    return False, None, None


def display_status(frame, is_active, slit_bbox, hand_count):
    status_color = (0, 0, 255) if is_active else (0, 255, 0)
    status_text = "BANDSAW: ACTIVE" if is_active else "BANDSAW: INACTIVE"
    cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
    slit_status = "SLIT: DETECTED" if slit_bbox is not None else "SLIT: NOT DETECTED"
    cv2.putText(frame, slit_status, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
    cv2.putText(frame, f"HANDS: {hand_count}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    if debug_mode:
        cv2.putText(frame, "DEBUG MODE", (frame.shape[1] - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)


def process_video():
    global current_frame, running, bandsaw_active, last_alert_time, debug_mode, recorder, slit_detector

    args = parse_arguments()
    debug_mode = args.debug
    alert_interval = args.alert_interval

    cap = open_video_source(args.video)
    if cap is None:
        print("Error: Could not open video source.")
        return

    recorder = VideoRecorder(output_dir=args.record)
    slit_detector = SlitDetector(stabilization_time=args.stabilization, debug=debug_mode)
    initialize_alerts()

    try:
        while running:
            ret, frame = get_frame(cap)
            if not ret or frame is None:
                print("Error: Failed to get frame.")
                time.sleep(0.1)
                continue

            with frame_lock:
                current_frame = frame.copy()

            if bandsaw_active and recording:
                recorder.write(frame)
                slit_bbox, frame = slit_detector.detect_slit(frame)
                hand_bboxes, frame = detect_hands(frame)
                is_close, distance, close_hand = check_hand_proximity(hand_bboxes, slit_bbox)

                if is_close and time.time() - last_alert_time > alert_interval:
                    if close_hand and slit_bbox:
                        hx, hy, hw, hh = close_hand
                        sx, sy, sw, sh = slit_bbox[:4]
                        hand_center = (int(hx + hw / 2), int(hy + hh / 2))
                        slit_center = (int(sx + sw / 2), int(sy + sh / 2))
                        cv2.line(frame, hand_center, slit_center, (0, 0, 255), 2)
                        cv2.putText(frame, f"DANGER: {distance:.1f}px", (hand_center[0], hand_center[1] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    print(f"⚠️ DANGER: Hand detected near bandsaw slit! Distance: {distance:.1f}px")
                    trigger_alert(duration=0.5)
                    last_alert_time = time.time()
            else:
                hand_bboxes, frame = detect_hands(frame)
                slit_bbox = None

            display_status(frame, bandsaw_active, slit_bbox, len(hand_bboxes))
            cv2.imshow("Bandsaw Safety Monitoring", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                running = False
                break
            if debug_mode:
                time.sleep(0.05)

    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error in video processing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if recorder and recorder.is_recording():
            recorder.stop()
        if slit_detector:
            slit_detector.stop_detection()
        release_video(cap)
        cv2.destroyAllWindows()


def simulate_vibration(vibration_detector):
    global running
    print("Starting vibration simulation...")
    try:
        while running:
            print("Simulating bandsaw ON...")
            vibration_detector.set_mock_vibration(0.8)
            time.sleep(10)
            print("Simulating bandsaw OFF...")
            vibration_detector.set_mock_vibration(0.0)
            time.sleep(5)
    except KeyboardInterrupt:
        print("Vibration simulation interrupted by user")
    except Exception as e:
        print(f"Error in vibration simulation: {e}")


def main():
    global running, debug_mode
    print("Bandsaw Safety Monitoring System - Starting...")
    args = parse_arguments()
    debug_mode = args.debug
    print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")

    vibration_detector = VibrationDetector(
        threshold=args.threshold,
        cooldown_time=1.0,
        mock_mode=debug_mode
    )
    vibration_detector.set_activity_callback(vibration_activity_callback)
    vibration_detector.start_detection(debug=debug_mode)

    if debug_mode:
        sim_thread = threading.Thread(target=simulate_vibration, args=(vibration_detector,))
        sim_thread.daemon = True
        sim_thread.start()

    try:
        process_video()
    except KeyboardInterrupt:
        print("Main program interrupted by user")
    except Exception as e:
        print(f"Main program error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        running = False
        vibration_detector.stop_detection()
        print("Bandsaw Safety Monitoring System - Stopped")

if __name__ == "__main__":
    main()

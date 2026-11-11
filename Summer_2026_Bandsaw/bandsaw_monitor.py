# bandsaw_monitor.py
import os
import sys
import time
import argparse
import threading
import cv2
import numpy as np

# Import custom modules
from video_capture import open_video_source, get_frame, release_video, VideoRecorder
from hand_detection import detect_hands
from enhanced_slit_detection import SlitDetector
from alert import solid_white, show_calibration_direction, solid_green, solid_red, turn_off_leds
from mpu_camera import bandsaw_active

# Global variables
running = True
debug_mode = False
current_frame = None
frame_lock = threading.Lock()
bandsaw_active_state = False
last_alert_time = 0
camera_on = False
slit_bbox = None

# Track last motion timestamp
last_motion_time = time.time()
INACTIVITY_TIMEOUT = 10

# Function to monitor and update camera state
def manage_camera_state():
    global camera_on, last_motion_time

    is_active = bandsaw_active()
    if is_active:
        last_motion_time = time.time()
        if not camera_on:
            print("Motion detected. Turning ON camera.")
            camera_on = True
    elif time.time() - last_motion_time > INACTIVITY_TIMEOUT:
        if camera_on:
            print("No motion detected. Turning OFF camera.")
            camera_on = False

    return is_active

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Bandsaw Safety Monitoring System",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--video', type=str, default='0', help='Video source (0 for webcam)')
    parser.add_argument('--record', type=str, default='recordings', help='Directory to save recordings')
    parser.add_argument('--threshold', type=float, default=0.5, help='Vibration threshold (unused here)')
    parser.add_argument('--stabilization', type=float, default=5.0, help='Slit detection stabilization time')
    parser.add_argument('--alert-interval', type=float, default=2.0, help='Min time between alerts (seconds)')
    return parser.parse_args()

def check_hand_near_boundary(hand_bbox, slit_bbox, base_threshold=100):
    if hand_bbox is None or slit_bbox is None:
        return False

    hx, hy, hw, hh = hand_bbox
    hand_rect = np.array([
        [hx, hy],
        [hx + hw, hy],
        [hx + hw, hy + hh],
        [hx, hy + hh]
    ])

    sx, sy, sw, sh, angle = slit_bbox[:5]
    slit_center = (sx, sy)
    slit_size = (sw, sh)
    slit_box = cv2.boxPoints((slit_center, slit_size, angle))
    slit_box = np.intp(slit_box)

    hand_poly = cv2.convexHull(hand_rect)
    slit_poly = cv2.convexHull(slit_box)

    intersection = cv2.intersectConvexConvex(hand_poly, slit_poly)
    return intersection[0] > 0

def display_calibration_status(frame, slit_detector):
    """Draw slit calibration state below the main status text (uses y >= 110)."""
    if slit_detector.is_finalized:
        cv2.putText(frame, "CALIBRATED", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    elif slit_detector.is_active and slit_detector.start_time is not None:
        orange = (0, 165, 255)
        elapsed = time.time() - slit_detector.start_time
        progress = min(elapsed / slit_detector.stabilization_time, 1.0)
        # Past the time window but not yet locked = the detector is extending
        # calibration because live fps was too low for enough groove votes.
        label = "CALIBRATING" if progress < 1.0 else "CALIBRATING (gathering frames)"
        cv2.putText(frame, label, (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, orange, 2)
        bar_x, bar_y, bar_w, bar_h = 10, 130, 200, 12
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), orange, 1)
        if progress > 0:
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_w * progress), bar_y + bar_h), orange, -1)

def display_status(frame, is_active, slit_bbox, hand_count):
    status_text = "BANDSAW: ACTIVE" if is_active else "BANDSAW: INACTIVE"
    status_color = (0, 0, 255) if is_active else (0, 255, 0)
    cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
    slit_text = "SLIT: DETECTED" if slit_bbox else "SLIT: NOT DETECTED"
    cv2.putText(frame, slit_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
    cv2.putText(frame, f"HANDS: {hand_count}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    if debug_mode:
        cv2.putText(frame, "DEBUG MODE", (frame.shape[1] - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)

def process_video():
    global current_frame, running, bandsaw_active_state, last_alert_time, debug_mode, camera_on, slit_bbox
    args = parse_arguments()
    debug_mode = args.debug

    cap = open_video_source(args.video)
    if cap is None:
        print("Error: Could not open video source.")
        return

    recorder = VideoRecorder(output_dir=args.record)
    slit_detector = SlitDetector(stabilization_time=args.stabilization, debug=debug_mode)
    recording = False

    # Live-fps: MediaPipe hand detection is by far the heaviest stage of the
    # loop, and during the calibration window the slit detector needs as many
    # frames as possible for a well-sampled consensus vote. So while
    # calibrating we run hand detection only every Nth frame (reusing the last
    # boxes in between, so alerts still fire); once the slit is locked, hands
    # are checked on every frame as before.
    HAND_DETECT_EVERY_N_CALIB = 3
    calib_frame_idx = 0
    last_hand_bboxes = []

    try:
        while running:
            bandsaw_active_state = manage_camera_state()

            if camera_on:
                ret, frame = get_frame(cap)
                if not ret or frame is None:
                    print("Error: Failed to get frame.")
                    time.sleep(0.1)
                    continue

                with frame_lock:
                    current_frame = frame.copy()

                if bandsaw_active_state:
                    if not recording:
                        recorder.start(frame, "bandsaw_activity")
                        recording = True
                        slit_detector.start_detection()
                        calib_frame_idx = 0
                        last_hand_bboxes = []
                    if recorder.is_recording():
                        recorder.write(frame)
                    slit_bbox, frame = slit_detector.detect_slit(frame)

                    # Throttle MediaPipe while the slit is calibrating (see
                    # HAND_DETECT_EVERY_N_CALIB above); full rate once locked.
                    calibrating = not slit_detector.is_finalized
                    if (not calibrating) or (calib_frame_idx % HAND_DETECT_EVERY_N_CALIB == 0):
                        hand_bboxes, frame = detect_hands(frame)
                        last_hand_bboxes = hand_bboxes
                    else:
                        hand_bboxes = last_hand_bboxes
                    calib_frame_idx += 1

                    if calibrating:
                        if slit_detector.calibration_cx is None:
                            direction = None
                        else:
                            frame_center_x = frame.shape[1] / 2
                            deadband = frame.shape[1] * 0.08
                            offset = slit_detector.calibration_cx - frame_center_x
                            direction = "left" if offset < -deadband else (
                                "right" if offset > deadband else "center"
                            )
                        show_calibration_direction(direction)
                    elif slit_detector.is_slit_missing():
                        show_calibration_direction(None)
                    elif hand_bboxes and len(hand_bboxes) > 0:
                        any_hand_near_slit = False
                        for hand_bbox in hand_bboxes:
                            x, y, w_box, h_box = hand_bbox
                            if slit_bbox and check_hand_near_boundary(hand_bbox, slit_bbox, base_threshold=100):
                                any_hand_near_slit = True
                                box_color = (0, 0, 255)
                                cv2.putText(frame, "ALERT: Hand Too Close!", (x, y - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, box_color, 2)
                            else:
                                box_color = (0, 255, 0)
                            cv2.rectangle(frame, (x, y), (x + w_box, y + h_box), box_color, 3)

                        if any_hand_near_slit:
                            solid_red()
                        else:
                            solid_green()
                    else:
                        solid_white()

                else:
                    if recording:
                        recorder.stop()
                        recording = False
                        slit_detector.stop_detection()
                    slit_bbox = None
                    hand_bboxes, frame = detect_hands(frame)
                    turn_off_leds()

                display_status(frame, bandsaw_active_state, slit_bbox, len(hand_bboxes))
                display_calibration_status(frame, slit_detector)

            else:
                frame = np.zeros((480, 800, 3), dtype=np.uint8)
                cv2.putText(frame, "Camera Off", (280, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                display_status(frame, bandsaw_active_state, None, 0)

            resized_frame = cv2.resize(frame, (800, 480))
            cv2.imshow("Bandsaw Safety Monitoring", resized_frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                running = False
                break
            elif key == ord('r'):
                print("Re-initializing slit calibration...")
                slit_detector.start_detection()
            if debug_mode:
                time.sleep(0.05)
    finally:
        if recorder.is_recording():
            recorder.stop()
        slit_detector.stop_detection()
        release_video(cap)
        turn_off_leds()
        cv2.destroyAllWindows()

def main():
    global running, debug_mode
    print("Bandsaw Safety Monitoring System - Starting...")
    args = parse_arguments()
    debug_mode = args.debug
    print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")
    process_video()
    print("Bandsaw Safety Monitoring System - Stopped")

if __name__ == "__main__":
    main()



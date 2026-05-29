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
from alert import start_alert, stop_alert, clear_alert
from mpu_camera import bandsaw_active

# Global variables
running = True
debug_mode = False
current_frame = None
frame_lock = threading.Lock()
bandsaw_active_state = False
last_alert_time = 0


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Bandsaw Safety Monitoring System",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument(
        "--video", type=str, default="0", help="Video source (0 for webcam)"
    )
    parser.add_argument(
        "--record", type=str, default="recordings", help="Directory to save recordings"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.5, help="Vibration threshold (unused here)"
    )
    parser.add_argument(
        "--stabilization",
        type=float,
        default=5.0,
        help="Slit detection stabilization time",
    )
    parser.add_argument(
        "--alert-interval",
        type=float,
        default=2.0,
        help="Min time between alerts (seconds)",
    )
    return parser.parse_args()


def check_hand_near_boundary(hand_bbox, slit_bbox, base_threshold=100):
    if hand_bbox is None or slit_bbox is None:
        return False

    hx, hy, hw, hh = hand_bbox
    hand_rect = np.array([[hx, hy], [hx + hw, hy], [hx + hw, hy + hh], [hx, hy + hh]])

    sx, sy, sw, sh, angle = slit_bbox
    slit_center = (sx, sy)
    slit_size = (sw, sh)
    slit_box = cv2.boxPoints((slit_center, slit_size, angle))
    slit_box = np.intp(slit_box)

    # Check for intersection between hand_rect and slit_box
    hand_poly = cv2.convexHull(hand_rect)
    slit_poly = cv2.convexHull(slit_box)

    intersection = cv2.intersectConvexConvex(hand_poly, slit_poly)
    return intersection[0] > 0  # area of intersection > 0 means overlap


def display_status(frame, is_active, slit_bbox, hand_count):
    status_text = "BANDSAW: ACTIVE" if is_active else "BANDSAW: INACTIVE"
    status_color = (0, 0, 255) if is_active else (0, 255, 0)
    cv2.putText(
        frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2
    )
    slit_text = "SLIT: DETECTED" if slit_bbox else "SLIT: NOT DETECTED"
    cv2.putText(
        frame, slit_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2
    )
    cv2.putText(
        frame,
        f"HANDS: {hand_count}",
        (10, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2,
    )

    if debug_mode:
        cv2.putText(
            frame,
            "DEBUG MODE",
            (frame.shape[1] - 150, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 0, 255),
            2,
        )


def process_video():
    global current_frame, running, bandsaw_active_state, last_alert_time, debug_mode
    args = parse_arguments()
    debug_mode = args.debug

    cap = open_video_source(args.video)
    if cap is None:
        print("Error: Could not open video source.")
        return

    recorder = VideoRecorder(output_dir=args.record)
    slit_detector = SlitDetector(
        stabilization_time=args.stabilization, debug=debug_mode
    )
    recording = False

    try:
        while running:
            # Check vibration
            is_active = bandsaw_active()
            if is_active != bandsaw_active_state:
                bandsaw_active_state = is_active
                print("Bandsaw ACTIVE" if is_active else "Bandsaw INACTIVE")

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
                if recorder.is_recording():
                    recorder.write(frame)
                slit_bbox, frame = slit_detector.detect_slit(frame)
                hand_bboxes, frame = detect_hands(frame)

                if hand_bboxes and len(hand_bboxes) > 0:
                    any_hand_near_slit = False
                    for hand_bbox in hand_bboxes:
                        x, y, w_box, h_box = hand_bbox
                        if slit_bbox and check_hand_near_boundary(
                            hand_bbox, slit_bbox, base_threshold=100
                        ):
                            any_hand_near_slit = True
                            box_color = (0, 0, 255)  # Red alert
                            cv2.putText(
                                frame,
                                "ALERT: Hand Too Close!",
                                (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.8,
                                box_color,
                                2,
                            )
                            current_time = time.time()
                            if current_time - last_alert_time > args.alert_interval:
                                last_alert_time = current_time
                        else:
                            box_color = (0, 255, 0)  # Safe
                        cv2.rectangle(
                            frame, (x, y), (x + w_box, y + h_box), box_color, 3
                        )
                    if any_hand_near_slit:
                        if bandsaw_active_state:
                            start_alert()
                        else:
                            stop_alert()
                    else:
                        stop_alert()
                else:
                    print("No hands detected in this frame.")
                    stop_alert()

            else:
                if recording:
                    recorder.stop()
                    recording = False
                    slit_detector.stop_detection()
                slit_bbox = None
                hand_bboxes, frame = detect_hands(frame)

            display_status(frame, bandsaw_active_state, slit_bbox, len(hand_bboxes))
            resized_frame = cv2.resize(frame, (800, 480))
            cv2.imshow("Bandsaw Safety Monitoring", resized_frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                running = False
                break
            elif key == ord("r"):
                print("Re-initializing slit calibration...")
                slit_detector.start_detection()
            if debug_mode:
                time.sleep(0.05)
    finally:
        if recorder.is_recording():
            recorder.stop()
        slit_detector.stop_detection()
        release_video(cap)
        clear_alert()
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

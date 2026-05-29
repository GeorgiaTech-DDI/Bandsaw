# bandsaw_monitor.py
import os
import sys
import time
import argparse
import threading
import cv2
import numpy as np

# Import custom modules
from bandsaw.video_capture import PiCameraCapture, VideoRecorder
from bandsaw.hand_detection import detect_hands
from bandsaw.slit_detection import SlitDetector
from bandsaw.alert import start_alert, stop_alert, clear_alert
from bandsaw.mpu_camera import bandsaw_active


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


# Bandsaw class
class BandsawMonitor:
    def __init__(self, args):
        self.args = args
        self.running = True
        self.debug_mode = args.debug
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.bandsaw_active_state = False
        self.last_alert_time = 0
        self.camera = PiCameraCapture()
        # self.cap = open_video_source(args.video)

        # if self.cap is None:
        #     raise RuntimeError("Could not open video source.")

        self.recorder = VideoRecorder(output_dir=args.record)
        self.slit_detector = SlitDetector(
            stabilization_time=args.stabilization,
            debug=self.debug_mode,
        )
        self.recording = False


    def check_hand_near_boundary(self, hand_bbox, slit_bbox):
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




    def display_status(self, frame, is_active, slit_bbox, hand_count):
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

        if self.debug_mode:
            cv2.putText(
                frame,
                "DEBUG MODE",
                (frame.shape[1] - 150, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 255),
                2,
            )


    def process_video(self):
        print("Bandsaw Safety Monitoring System - Starting...")
        print(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")

        # cap = open_video_source(args.video)
        # if cap is None:
        #     print("Error: Could not open video source.")
        #     return

        # recorder = VideoRecorder(output_dir=args.record)
        # slit_detector = SlitDetector(
        #     stabilization_time=args.stabilization, debug=debug_mode
        # )
        # recording = False

        try:
            while self.running:
                # Check vibration
                is_active = bandsaw_active()
                if is_active != self.bandsaw_active_state:
                    self.bandsaw_active_state = is_active
                    print("Bandsaw ACTIVE" if is_active else "Bandsaw INACTIVE")

                ret, frame = self.camera.get_frame()
                if not ret or frame is None:
                    print("Error: Failed to get frame.")
                    time.sleep(0.1)
                    continue

                with self.frame_lock:
                    self.current_frame = frame.copy()
                    
                slit_bbox = None
                hand_bboxes = []

                if self.bandsaw_active_state:
                    if not self.recording:
                        self.recorder.start(frame, "bandsaw_activity")
                        self.recording = True
                        self.slit_detector.start_detection()
                    if self.recorder.is_recording():
                        self.recorder.write(frame)
                    slit_bbox, frame = self.slit_detector.detect_slit(frame)
                    hand_bboxes, frame = detect_hands(frame)

                    if hand_bboxes and len(hand_bboxes) > 0:
                        any_hand_near_slit = False
                        for hand_bbox in hand_bboxes:
                            x, y, w_box, h_box = hand_bbox
                            if slit_bbox and self.check_hand_near_boundary(hand_bbox, slit_bbox):
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
                                if current_time - self.last_alert_time > self.args.alert_interval:
                                    self.last_alert_time = current_time
                            else:
                                box_color = (0, 255, 0)  # Safe
                            cv2.rectangle(
                                frame, (x, y), (x + w_box, y + h_box), box_color, 3
                            )
                        if any_hand_near_slit:
                            start_alert()
                        else:
                            stop_alert()
                    else:
                        print("No hands detected in this frame.")
                        stop_alert()

                else:
                    if self.recording:
                        self.recorder.stop()
                        self.recording = False
                        self.slit_detector.stop_detection()
                    slit_bbox = None
                    hand_bboxes, frame = detect_hands(frame)

                self.display_status(frame, self.bandsaw_active_state, slit_bbox, len(hand_bboxes))
                resized_frame = cv2.resize(frame, (800, 480))
                cv2.imshow("Bandsaw Safety Monitoring", resized_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    self.running = False
                    break
                elif key == ord("r"):
                    print("Re-initializing slit calibration...")
                    self.slit_detector.start_detection()
                if self.debug_mode:
                    time.sleep(0.05)
        finally:
            self.processHelper()


    # cv2 Recorder helper
    def processHelper(self):
        if self.recorder.is_recording():
                self.recorder.stop()

        self.slit_detector.stop_detection()
        self.camera.release()
        clear_alert()
        cv2.destroyAllWindows()
        print("Bandsaw Safety Monitoring System - Stopped")

# Main method
def main():
    args = parse_arguments()
    monitor = BandsawMonitor(args)
    monitor.process_video()
        


if __name__ == "__main__":
    main()

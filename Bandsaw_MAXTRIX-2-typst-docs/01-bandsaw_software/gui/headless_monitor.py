#!/usr/bin/env python3
"""Headless bandsaw monitor: no GUI, runs detection and records on alert."""
import time
import argparse
import os
import cv2

try:
    from bandsaw.slit_detection import SlitDetector
except Exception:
    SlitDetector = None

try:
    from bandsaw.hand_detection import detect_hands
except Exception:
    def detect_hands(frame):
        return [], frame

try:
    from bandsaw.video_capture import PiCameraCapture, VideoRecorder
except Exception:
    PiCameraCapture = None
    VideoRecorder = None


class CameraSource:
    def __init__(self, src=0):
        self.src = src
        self.pi = None
        self.cap = None

    def open(self):
        if PiCameraCapture is not None:
            try:
                self.pi = PiCameraCapture()
                return True
            except Exception:
                self.pi = None
        self.cap = cv2.VideoCapture(self.src)
        return self.cap.isOpened()

    def read(self):
        if self.pi is not None:
            return self.pi.get_frame()
        if self.cap is not None:
            ok, frame = self.cap.read()
            return ok, frame
        return False, None

    def release(self):
        if self.pi is not None:
            try:
                self.pi.release()
            except Exception:
                pass
            self.pi = None
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None


class SimpleRecorder:
    def __init__(self, outdir="recordings", fps=20.0, codec="mp4v"):
        self.outdir = outdir
        self.fps = fps
        self.codec = codec
        self.writer = None
        self.path = None

    def start(self, frame, prefix="alert"):
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)
        ts = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{ts}.mp4"
        path = os.path.join(self.outdir, filename)
        h, w = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        self.writer = cv2.VideoWriter(path, fourcc, self.fps, (w, h))
        if self.writer.isOpened():
            self.path = path
            return path
        self.writer = None
        return None

    def write(self, frame):
        if self.writer is None:
            return False
        self.writer.write(frame)
        return True

    def stop(self):
        if self.writer:
            try:
                self.writer.release()
            except Exception:
                pass
        self.writer = None
        p = self.path
        self.path = None
        return p


def hand_near_slit(hand_bbox, slit_bbox):
    if hand_bbox is None or slit_bbox is None:
        return False
    try:
        hx, hy, hw, hh = hand_bbox
        hand_rect = ((hx, hy), (hx + hw, hy), (hx + hw, hy + hh), (hx, hy + hh))
        sx, sy, sw, sh, angle = slit_bbox
        slit_center = (sx, sy)
        slit_size = (sw, sh)
        slit_box = cv2.boxPoints((slit_center, slit_size, angle))
        slit_box = slit_box.astype(int)
        hand_poly = cv2.convexHull(cv2.UMat(np.array(hand_rect, dtype="int32")).get())
        slit_poly = cv2.convexHull(slit_box)
        inter = cv2.intersectConvexConvex(hand_poly, slit_poly)
        return inter[0] > 0
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", default=0, help="video source")
    parser.add_argument("--record-dir", default="recordings", help="output dir")
    parser.add_argument("--alert-interval", type=float, default=2.0)
    args = parser.parse_args()

    cam = CameraSource(src=args.video)
    if not cam.open():
        print("Failed to open camera source")
        return

    slit = SlitDetector(stabilization_time=1.0) if SlitDetector is not None else None
    if slit is not None:
        slit.start_detection()

    recorder = None
    if VideoRecorder is not None:
        try:
            recorder = VideoRecorder(output_dir=args.record_dir)
        except Exception:
            recorder = SimpleRecorder(outdir=args.record_dir)
    else:
        recorder = SimpleRecorder(outdir=args.record_dir)

    last_alert = 0
    recording = False

    try:
        while True:
            ok, frame = cam.read()
            if not ok or frame is None:
                time.sleep(0.05)
                continue

            # detect slit and hands
            s_bbox = None
            if slit is not None:
                try:
                    s_bbox, frame = slit.detect_slit(frame)
                except Exception:
                    s_bbox = None

            hands = []
            try:
                hands, frame = detect_hands(frame)
            except Exception:
                hands = []

            too_close = False
            for hb in hands:
                if hand_near_slit(hb, s_bbox):
                    too_close = True
                    break

            current = time.time()
            if too_close:
                print(f"ALERT at {time.strftime('%H:%M:%S')} - hand too close")
                last_alert = current
                if not recording:
                    path = recorder.start(frame, prefix="alert")
                    if path:
                        recording = True
                        print(f"Recording started: {path}")
            else:
                # stop recording if no alert for 2*alert_interval
                if recording and (current - last_alert) > (2 * args.alert_interval):
                    p = recorder.stop()
                    recording = False
                    print(f"Recording stopped: {p}")

            if recording:
                try:
                    recorder.write(frame)
                except Exception:
                    pass

            time.sleep(0.02)
    except KeyboardInterrupt:
        print("Stopping headless monitor")
    finally:
        if recording:
            recorder.stop()
        if slit is not None:
            slit.stop_detection()
        cam.release()


if __name__ == "__main__":
    main()

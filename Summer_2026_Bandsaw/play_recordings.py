#!/usr/bin/env python3
"""Play recorded clips back through the slit detector, on-screen, like a live run.

For each clip it starts slit detection fresh, runs the stabilization window
(CALIBRATING), locks the slit (LOCKED), then keeps looping the clip so you can
watch where the vertical "DESIRED SLIT" box landed. No camera / LEDs / MPU.

Keys:
    n / ->   next clip
    p / <-   previous clip
    r        recalibrate the current clip
    space    pause / resume
    q / Esc  quit
"""
import argparse
import glob
import os
import time

import cv2

from enhanced_slit_detection import SlitDetector

WIN = "Slit detection playback (recordings)"


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", nargs="?", default="recordings",
                    help="folder of .mp4 clips (default: recordings)")
    ap.add_argument("--stabilization", type=float, default=3.0,
                    help="seconds of CALIBRATING before the box locks")
    ap.add_argument("--width", type=int, default=1100,
                    help="display window width (height keeps aspect)")
    return ap.parse_args()


def open_clip(path):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened() or cap.get(cv2.CAP_PROP_FRAME_COUNT) < 1:
        return None, 30.0
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    return cap, fps


def banner(frame, text, color):
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 34), (0, 0, 0), -1)
    cv2.putText(frame, text, (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


def main():
    args = parse_args()
    clips = sorted(glob.glob(os.path.join(args.dir, "*.mp4")))
    if not clips:
        print(f"No .mp4 files in {args.dir}")
        return 1

    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
    detector = SlitDetector(stabilization_time=args.stabilization, debug=False)

    idx = 0
    while 0 <= idx < len(clips):
        path = clips[idx]
        cap, fps = open_clip(path)
        if cap is None:
            print(f"[skip] unreadable: {os.path.basename(path)}")
            idx += 1
            continue
        frame_delay = 1.0 / fps if fps > 0 else 1.0 / 30.0

        detector.stop_detection()
        detector.start_detection()
        print(f"[{idx+1}/{len(clips)}] {os.path.basename(path)}")

        paused = False
        go_to = None  # set to next index on a navigation key
        while go_to is None:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # loop the clip
                    continue
                _, frame = detector.detect_slit(frame)

            status = "LOCKED" if detector.is_finalized else "CALIBRATING..."
            color = (0, 255, 0) if detector.is_finalized else (0, 200, 255)
            disp = frame.copy()
            banner(disp, f"[{idx+1}/{len(clips)}] {os.path.basename(path)}   {status}"
                         f"   (n next | p prev | r recal | space pause | q quit)", color)

            scale = args.width / disp.shape[1]
            disp = cv2.resize(disp, (args.width, int(disp.shape[0] * scale)))
            cv2.imshow(WIN, disp)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), 27):
                cap.release(); cv2.destroyAllWindows(); return 0
            elif key in (ord('n'), 83, 9):       # n / right-arrow / tab
                go_to = idx + 1
            elif key in (ord('p'), 81):          # p / left-arrow
                go_to = max(0, idx - 1)
            elif key == ord('r'):
                detector.stop_detection(); detector.start_detection()
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                print("  recalibrating...")
            elif key == ord(' '):
                paused = not paused

            if not paused:
                time.sleep(frame_delay)

        cap.release()
        idx = go_to

    cv2.destroyAllWindows()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

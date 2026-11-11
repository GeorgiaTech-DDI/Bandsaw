#!/usr/bin/env python3
"""Render each recording with the slit-detector overlay burned in, as .mp4 you
can open in any video player (no live GUI / Wayland dependency).

Finalization is driven by FRAME COUNT here (not wall clock) so the
CALIBRATING -> LOCKED transition lands at a consistent point in every clip
regardless of how fast frames are processed offline.

Output: recordings_annotated/<name>.annot.mp4
"""
import glob
import os

import cv2

from enhanced_slit_detection import SlitDetector

OUT_DIR = "recordings_annotated"
STAB_SECONDS = 3.0


def banner(frame, text, color):
    cv2.rectangle(frame, (0, frame.shape[0] - 30), (frame.shape[1], frame.shape[0]),
                  (0, 0, 0), -1)
    cv2.putText(frame, text, (12, frame.shape[0] - 9),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


def render(path, out_dir):
    cap = cv2.VideoCapture(path)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if not cap.isOpened() or n < 1:
        return f"{os.path.basename(path):46s} -> unreadable/empty (skipped)"
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    stab_frames = min(int(STAB_SECONDS * fps), max(1, int(n * 0.5)))

    out_path = os.path.join(out_dir, os.path.basename(path).replace(".mp4", ".annot.mp4"))
    vw = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    det = SlitDetector(stabilization_time=1e9, debug=False)  # disable wall-clock finalize
    det.start_detection()

    i = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if i == stab_frames:
            det._finalize_detection()          # force the lock at a fixed frame
        _, frame = det.detect_slit(frame)
        status = ("LOCKED" if det.is_finalized and not det.is_slit_missing()
                  else "SLIT NOT FOUND" if det.is_slit_missing()
                  else "CALIBRATING...")
        color = ((0, 255, 0) if status == "LOCKED"
                 else (0, 0, 255) if status == "SLIT NOT FOUND"
                 else (0, 200, 255))
        banner(frame, f"{os.path.basename(path)}   {status}", color)
        vw.write(frame)
        i += 1

    vw.release()
    cap.release()
    fs = det.final_slit
    where = ("SLIT NOT FOUND (red)" if det.is_slit_missing()
             else f"locked cx={fs[0]:.0f} cy={fs[1]:.0f} ang={fs[4]:.1f}" if fs else "no lock")
    return f"{os.path.basename(path):46s} -> {where}\n    {out_path}"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    clips = sorted(glob.glob("recordings/*.mp4"))
    print(f"Rendering {len(clips)} clips -> {OUT_DIR}/\n")
    for c in clips:
        print(render(c, OUT_DIR))


if __name__ == "__main__":
    main()

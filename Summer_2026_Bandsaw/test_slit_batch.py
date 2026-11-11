#!/usr/bin/env python3
"""Headless batch test of the slit detector over recorded .mp4 clips.

Runs SlitDetector against each video with NO hardware and NO display: it feeds
frames, lets the stabilization window finalize, then writes an annotated frame
(showing the locked "DESIRED SLIT" box) per clip and prints the result. Use it
to eyeball where the detector lands across the different recording views.

Usage:
    python test_slit_batch.py                  # all recordings/*.mp4 + test_videos/*
    python test_slit_batch.py path/to/clip.mp4 [more.mp4 ...]
    python test_slit_batch.py --stabilization 3.0 --out /tmp/annot
"""
import argparse
import glob
import os

import cv2

from enhanced_slit_detection import SlitDetector


def run_clip(path, stabilization, out_dir):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened() or cap.get(cv2.CAP_PROP_FRAME_COUNT) < 1:
        return {"path": os.path.basename(path), "error": "unreadable/empty"}

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    nframes = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    det = SlitDetector(stabilization_time=stabilization, debug=False)
    det.start_detection()

    last_frame = None
    i = 0
    finalized_at = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, frame = det.detect_slit(frame)
        last_frame = frame
        i += 1
        if det.is_finalized and finalized_at is None:
            finalized_at = i
        if finalized_at is not None and i >= finalized_at + 5:
            break

    # If the clip ended before the time window elapsed, force finalize and
    # render one more frame in the finalized state.
    if not det.is_finalized and det.is_active:
        det._finalize_detection()
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, i - 1))
        ret, frame = cap.read()
        if ret:
            _, frame = det.detect_slit(frame)
            last_frame = frame

    out = None
    if last_frame is not None:
        out = os.path.join(out_dir, os.path.basename(path) + ".annot.png")
        cv2.imwrite(out, last_frame)
    cap.release()
    return {"path": os.path.basename(path), "res": f"{w}x{h}",
            "frames": nframes, "slit": det.final_slit, "annot": out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("videos", nargs="*", help="clips (default: recordings + test_videos)")
    ap.add_argument("--stabilization", type=float, default=3.0)
    ap.add_argument("--out", default="annot_out")
    args = ap.parse_args()

    clips = args.videos or (sorted(glob.glob("recordings/*.mp4")) +
                            sorted(glob.glob("test_videos/*.mp4")))
    os.makedirs(args.out, exist_ok=True)
    print(f"Testing {len(clips)} clips (stabilization={args.stabilization}s) "
          f"-> annotated frames in {args.out}/\n")

    for c in clips:
        r = run_clip(c, args.stabilization, args.out)
        if r.get("error"):
            print(f"{r['path']:48s} -> {r['error']}")
            continue
        s = r["slit"]
        if s is None:
            verdict = "SLIT NOT FOUND (fail-safe / red)"
        else:
            cx, cy, ang = s[0], s[1], s[4]
            verdict = f"cx={cx:.0f} cy={cy:.0f} ang={ang:.1f}"
        print(f"{r['path']:48s} {r['res']:9s} fr={r['frames']:>4} -> {verdict}")


if __name__ == "__main__":
    main()

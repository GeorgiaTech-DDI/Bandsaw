import os
import sys
from typing import Tuple
import cv2
import numpy as np

from bandsaw.slit_detection import SlitDetector


def _add_build_lib_to_path():
    # Add the built package path so we can import the standalone helper
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    build_lib = os.path.join(root, '01-bandsaw_software', 'build', 'lib')
    if build_lib not in sys.path:
        sys.path.insert(0, build_lib)


class BandsawLibrary:
    """Robot Framework library with small wrappers around project functions.

    This library provides simple keywords used by the example Robot tests.
    """

    def expand_bounding_box(self, x, y, w, h, scale=1.5, frame_shape=None):
        # Local reimplementation to avoid importing MediaPipe at test runtime
        if frame_shape and isinstance(frame_shape, str):
            parts = [int(p.strip()) for p in frame_shape.split(',')]
            frame_shape = (parts[0], parts[1], parts[2] if len(parts) > 2 else 3)
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        scale = float(scale)
        cx, cy = x + w // 2, y + h // 2
        new_w = int(w * scale)
        new_h = int(h * scale)
        new_x = max(cx - new_w // 2, 0)
        new_y = max(cy - new_h // 2, 0)
        if frame_shape is not None:
            new_w = min(new_w, frame_shape[1] - new_x)
            new_h = min(new_h, frame_shape[0] - new_y)
        return new_x, new_y, new_w, new_h

    def smooth_bbox(self, new_bbox, old_bbox):
        def parse(b):
            if isinstance(b, str):
                return tuple(float(p.strip()) for p in b.split(','))
            return tuple(float(p) for p in b)

        new = parse(new_bbox)
        old = parse(old_bbox)
        sd = SlitDetector()
        return sd.smooth_bbox(new, old)

    def finalize_detection(self):
        sd = SlitDetector()
        # small sample set of detections to finalize
        sd.detected_slits = [
            (10, 20, 30, 40, 5.0),
            (12, 22, 32, 42, 6.0),
        ]
        sd._finalize_detection()
        return sd.final_slit

    def check_hand_near_boundary(self, hand_bbox, slit_bbox):
        def parse(b):
            if isinstance(b, str):
                return tuple(float(p.strip()) for p in b.split(','))
            return tuple(float(p) for p in b)

        h = parse(hand_bbox)
        s = parse(slit_bbox)
        hand = (int(h[0]), int(h[1]), int(h[2]), int(h[3]))
        sx, sy, sw, sh, angle = float(s[0]), float(s[1]), float(s[2]), float(s[3]), float(s[4])

        hx, hy, hw, hh = hand
        hand_rect = np.array([[hx, hy], [hx + hw, hy], [hx + hw, hy + hh], [hx, hy + hh]])

        slit_center = (sx, sy)
        slit_size = (sw, sh)
        slit_box = cv2.boxPoints((slit_center, slit_size, angle))
        slit_box = np.intp(slit_box)

        hand_poly = cv2.convexHull(hand_rect)
        slit_poly = cv2.convexHull(slit_box)

        intersection = cv2.intersectConvexConvex(hand_poly, slit_poly)
        return bool(intersection[0] > 0)


if __name__ == "__main__":
    print("BandsawLibrary helper - not intended to be run directly")

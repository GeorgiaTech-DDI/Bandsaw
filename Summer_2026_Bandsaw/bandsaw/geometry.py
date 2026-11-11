"""Geometry helpers shared by monitor and offline analysis tools."""

import cv2
import numpy as np


def check_hand_near_boundary(hand_bbox, slit_bbox, base_threshold=100):
    if hand_bbox is None or slit_bbox is None:
        return False

    hx, hy, hand_width, hand_height = hand_bbox
    hand_rect = np.array([
        [hx, hy],
        [hx + hand_width, hy],
        [hx + hand_width, hy + hand_height],
        [hx, hy + hand_height],
    ])

    sx, sy, slit_width, slit_height, angle = slit_bbox[:5]
    slit_box = cv2.boxPoints(
        ((sx, sy), (slit_width, slit_height), angle)
    )
    slit_box = np.intp(slit_box)

    hand_poly = cv2.convexHull(hand_rect)
    slit_poly = cv2.convexHull(slit_box)
    intersection = cv2.intersectConvexConvex(hand_poly, slit_poly)
    return intersection[0] > 0

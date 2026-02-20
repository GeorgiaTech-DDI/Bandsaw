# slit_detection.py
import cv2
import numpy as np
import time
import math


class SlitDetector:
    def __init__(self, stabilization_time=5.0, debug=False):
        self.stabilization_time = stabilization_time
        self.start_time = None
        self.is_active = False
        self.is_finalized = False
        self.final_slit = None
        self.detected_slits = []
        self.prev_slit_bbox = None
        self.alpha = 0.3
        self.debug = debug
        self.detection_count = 0
        self.success_count = 0
        self.processing_times = []

    def start_detection(self):
        self.is_active = True
        self.is_finalized = False
        self.start_time = time.time()
        self.detected_slits = []
        self.final_slit = None
        print("Slit detection started")

    def stop_detection(self):
        self.is_active = False
        self.is_finalized = False
        self.start_time = None
        if self.detection_count > 0:
            success_rate = (self.success_count / self.detection_count) * 100
            avg_time = (
                sum(self.processing_times) / len(self.processing_times)
                if self.processing_times
                else 0
            )
            print(
                f"Slit detection stopped. Success rate: {success_rate:.1f}%, Avg processing time: {avg_time * 1000:.1f}ms"
            )
        else:
            print("Slit detection stopped (no frames processed)")

    def smooth_bbox(self, new_bbox, old_bbox):
        if len(new_bbox) == 5:
            return (
                int(self.alpha * new_bbox[0] + (1 - self.alpha) * old_bbox[0]),
                int(self.alpha * new_bbox[1] + (1 - self.alpha) * old_bbox[1]),
                int(self.alpha * new_bbox[2] + (1 - self.alpha) * old_bbox[2]),
                int(self.alpha * new_bbox[3] + (1 - self.alpha) * old_bbox[3]),
                self.alpha * new_bbox[4] + (1 - self.alpha) * old_bbox[4],
            )
        else:
            return tuple(
                int(self.alpha * n + (1 - self.alpha) * o)
                for n, o in zip(new_bbox, old_bbox)
            )

    def _finalize_detection(self):
        if not self.detected_slits:
            print("Warning: No slits detected during stabilization period")
            self.is_finalized = True
            return
        x_vals = [b[0] for b in self.detected_slits]
        y_vals = [b[1] for b in self.detected_slits]
        w_vals = [b[2] for b in self.detected_slits]
        h_vals = [b[3] for b in self.detected_slits]
        a_vals = [b[4] for b in self.detected_slits]
        avg = lambda vals: sum(vals) / len(vals)
        self.final_slit = (
            avg(x_vals),
            avg(y_vals),
            avg(w_vals),
            avg(h_vals),
            avg(a_vals),
        )
        self.is_finalized = True
        print(f"Slit detection finalized at {self.final_slit}")

    def detect_slit(self, frame):
        start_time = time.time()
        self.detection_count += 1
        viz_frame = frame.copy() if self.debug else frame

        if self.is_finalized and self.final_slit is not None:
            center, size, angle = (
                self.final_slit[0:2],
                (self.final_slit[2], self.final_slit[3]),
                self.final_slit[4],
            )
            box = cv2.boxPoints((center, size, angle))
            box = np.int0(box)
            cv2.drawContours(frame, [box], 0, (0, 0, 255), 2)
            cv2.putText(
                frame,
                "FINALIZED SLIT",
                (int(center[0]), int(center[1]) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )
            self.processing_times.append(time.time() - start_time)
            self.success_count += 1
            return self.final_slit, frame

        if not self.is_active:
            self.processing_times.append(time.time() - start_time)
            return self.prev_slit_bbox, frame

        if (
            self.start_time is not None
            and time.time() - self.start_time >= self.stabilization_time
        ):
            if not self.is_finalized:
                self._finalize_detection()
            self.processing_times.append(time.time() - start_time)
            return self.final_slit, frame

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        binary = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        edges = cv2.Canny(binary, 50, 150)
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=80, minLineLength=50, maxLineGap=20
        )

        if lines is None:
            self.processing_times.append(time.time() - start_time)
            return self.prev_slit_bbox, frame

        h, w = frame.shape[:2]
        center_x = w // 2
        best_line = None
        best_score = float("inf")

        for line in lines:
            x1, y1, x2, y2 = line[0]
            dx, dy = x2 - x1, y2 - y1
            if abs(dx) < 1:
                slope_error = 0
            else:
                slope = dy / float(dx)
                if abs(slope) < 1:
                    continue
                slope_error = 1.0 / abs(slope + 1e-9)
            mid_x = (x1 + x2) / 2.0
            center_error = abs(mid_x - center_x)
            length = np.sqrt(dx * dx + dy * dy)
            length_bonus = 100.0 / (length + 1e-9)
            score = slope_error + 0.01 * center_error + length_bonus
            if score < best_score:
                best_score = score
                best_line = (x1, y1, x2, y2)

        if best_line is None:
            self.processing_times.append(time.time() - start_time)
            return self.prev_slit_bbox, frame

        x1, y1, x2, y2 = best_line
        if y1 > y2:
            x1, y1, x2, y2 = x2, y2, x1, y1

        cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        center = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
        length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        width = 30
        rotated_rect = (center, (length, width), angle)  # FIXED: swapped length/width
        box = cv2.boxPoints(rotated_rect)
        box = np.int0(box)
        cv2.drawContours(frame, [box], 0, (255, 0, 0), 2)

        slit_bbox = (
            center[0],
            center[1],
            length,
            width,
            angle,
        )  # Updated ordering to match rotated_rect
        self.detected_slits.append(slit_bbox)
        if len(self.detected_slits) > 30:
            self.detected_slits = self.detected_slits[-30:]
        if self.prev_slit_bbox is not None:
            slit_bbox = self.smooth_bbox(slit_bbox, self.prev_slit_bbox)
        self.prev_slit_bbox = slit_bbox
        self.processing_times.append(time.time() - start_time)
        self.success_count += 1
        return slit_bbox, frame

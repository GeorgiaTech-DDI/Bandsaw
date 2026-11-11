# import cv2
# import numpy as np
# 
# # Global variable to store the previous bounding box for smoothing.
# prev_slit_bbox = None
# # Smoothing factor for exponential moving average (0 < alpha <= 1). Lower values yield more smoothing.
# alpha = 0.3
# 
# def smooth_bbox(new_bbox, old_bbox, alpha=0.3):
#     """
#     Smooths the new bounding box by taking a weighted average of new and previous values.
#     Both new_bbox and old_bbox are tuples: (x, y, w, h).
#     Returns a new tuple of smoothed values.
#     """
#     return tuple(int(alpha * new + (1 - alpha) * old) for new, old in zip(new_bbox, old_bbox))
# 
# def get_slit_bbox(frame):
#     """
#     Detects the bandsaw slit in the provided frame using edge and line detection.
#     It returns a smoothed axis-aligned bounding box (x, y, w, h) around the best candidate line.
#     If no candidate is detected (e.g., the slit is occluded by a cut piece), 
#     it returns the previous valid bounding box if available.
#     
#     Parameters:
#       frame: The current frame from the camera.
#       
#     Returns:
#       A tuple (bx, by, bw, bh) representing the bounding box of the slit,
#       or None if no box is detected and no previous box exists.
#     """
#     global prev_slit_bbox, alpha
# 
#     # Convert the frame to grayscale.
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     # Apply Gaussian blur to reduce noise.
#     gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)
#     # Use Canny edge import cv2
# import numpy as np
# 
# # Global variable to store the previous bounding box for smoothing.
# prev_slit_bbox = None
# # Smoothing factor for exponential moving average (0 < alpha <= 1). Lower values yield more smoothing.
# alpha = 0.3
# 
# def smooth_bbox(new_bbox, old_bbox, alpha=0.3):
#     """
#     Smooths the new bounding box by taking a weighted average of new and previous values.
#     Both new_bbox and old_bbox are tuples: (x, y, w, h).
#     Returns a new tuple of smoothed values.
#     """
#     return tuple(int(alpha * new + (1 - alpha) * old) for new, old in zip(new_bbox, old_bbox))
# 
# def get_slit_bbox(frame):
#     """
#     Detects the bandsaw slit in the provided frame using edge and line detection.
#     It returns a smoothed axis-aligned bounding box (x, y, w, h) around the best candidate line.
#     If no candidate is detected (e.g., the slit is occluded by a cut piece), 
#     it returns the previous valid bounding box if available.
#     detection.
#     edges = cv2.Canny(gray_blur, 50, 150, apertureSize=3)
#     
#     # Use HoughLinesP to detect line segments.
#     lines = cv2.HoughLinesP(edges,
#                             rho=1,
#                             theta=np.pi/180,
#                             threshold=80,
#                             minLineLength=50,
#                             maxLineGap=20)
#     # If no lines are detected, return the previous bounding box (if available).
#     if lines is None:
#         # Log for debugging.
#         print("No lines detected. Using previous bounding box." if prev_slit_bbox is not None else "No lines detected, and no previous box available.")
#         return prev_slit_bbox
# 
#     h, w = frame.shape[:2]
#     center_x = w // 2
#     best_line = None
#     best_score = float('inf')
#     
#     # Evaluate each detected line.
#     for line in lines:
#         x1, y1, x2, y2 = line[0]
#         dx = x2 - x1
#         dy = y2 - y1
#         # We want near-vertical lines.
#         if dx == 0:
#             slope_error = 0
#         else:
#             slope = dy / float(dx)
#             # Only consider lines with an absolute slope of at least 1.
#             if abs(slope) < 1:
#                 continue
#             slope_error = 1.0 / abs(slope + 1e-9)
#         
#         # Determine the midpoint and its distance from the center.
#         mid_x = (x1 + x2) / 2.0
#         center_error = abs(mid_x - center_x)
#         # Lower score indicates a better candidate.
#         score = slope_error + 0.01 * center_error
#         
#         if score < best_score:
#             best_score = score
#             best_line = (x1, y1, x2, y2)
# 
#     if best_line is None:
#         print("No suitable vertical line found. Using previous bounding box." if prev_slit_bbox is not None else "No suitable vertical line found.")
#         return prev_slit_bbox
# 
#     # Optionally draw the chosen line (for debugging).
#     x1, y1, x2, y2 = best_line
#     cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
#     
#     # Create an axis-aligned bounding box around the best line.
#     minx = min(x1, x2)
#     maxx = max(x1, x2)
#     miny = min(y1, y2)
#     maxy = max(y1, y2)
#     margin_x = 20
#     margin_y = 20
#     bx = max(0, minx - margin_x)
#     by = max(0, miny - margin_y)
#     bw = (maxx - minx) + 2 * margin_x
#     bh = (maxy - miny) + 2 * margin_y
#     candidate_bbox = (bx, by, bw, bh)
#     
#     # Optionally, you might want to filter out candidate boxes that are not slim enough (bandsaw slit should be narrow).
#     # For example, if width/height > some threshold, we consider it not valid.
#     aspect_ratio = bw / float(bh) if bh != 0 else float('inf')
#     aspect_ratio_thresh = 0.3  # Adjust as necessary.
#     if aspect_ratio > aspect_ratio_thresh:
#         print("Candidate bounding box rejected due to aspect ratio. Using previous box." if prev_slit_bbox is not None else "Candidate bounding box rejected due to aspect ratio.")
#         return prev_slit_bbox
# 
#     # Smooth the bounding box using an exponential moving average.
#     if prev_slit_bbox is None:
#         smoothed_bbox = candidate_bbox
#     else:
#         smoothed_bbox = smooth_bbox(candidate_bbox, prev_slit_bbox, alpha)
#     
#     prev_slit_bbox = smoothed_bbox
#     
#     # Draw the final smoothed bounding box for debugging.
#     cv2.rectangle(frame, (smoothed_bbox[0], smoothed_bbox[1]),
#                   (smoothed_bbox[0] + smoothed_bbox[2], smoothed_bbox[1] + smoothed_bbox[3]),
#                   (255, 0, 0), 2)
#     
#     return smoothed_bbox
# PATCH: Correct the alignment of the rotated slit bounding box
# Use (length, width) instead of (width, length) so the long edge aligns with the angle.

# enhanced_slit_detection.py
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
            avg_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
            print(f"Slit detection stopped. Success rate: {success_rate:.1f}%, Avg processing time: {avg_time*1000:.1f}ms")
        else:
            print("Slit detection stopped (no frames processed)")

    def smooth_bbox(self, new_bbox, old_bbox):
        if len(new_bbox) == 5:
            return (
                int(self.alpha * new_bbox[0] + (1 - self.alpha) * old_bbox[0]),
                int(self.alpha * new_bbox[1] + (1 - self.alpha) * old_bbox[1]),
                int(self.alpha * new_bbox[2] + (1 - self.alpha) * old_bbox[2]),
                int(self.alpha * new_bbox[3] + (1 - self.alpha) * old_bbox[3]),
                self.alpha * new_bbox[4] + (1 - self.alpha) * old_bbox[4]
            )
        else:
            return tuple(int(self.alpha * n + (1 - self.alpha) * o) for n, o in zip(new_bbox, old_bbox))

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
        self.final_slit = (avg(x_vals), avg(y_vals), avg(w_vals), avg(h_vals), avg(a_vals))
        self.is_finalized = True
        print(f"Slit detection finalized at {self.final_slit}")

    def detect_slit(self, frame):
        start_time = time.time()
        self.detection_count += 1
        viz_frame = frame.copy() if self.debug else frame

        if self.is_finalized and self.final_slit is not None:
            center, size, angle = (self.final_slit[0:2], (self.final_slit[2], self.final_slit[3]), self.final_slit[4])
            box = cv2.boxPoints((center, size, angle))
            box = np.int0(box)
            cv2.drawContours(frame, [box], 0, (0, 0, 255), 2)
            cv2.putText(frame, "FINALIZED SLIT", (int(center[0]), int(center[1])-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            self.processing_times.append(time.time() - start_time)
            self.success_count += 1
            return self.final_slit, frame

        if not self.is_active:
            self.processing_times.append(time.time() - start_time)
            return self.prev_slit_bbox, frame

        if self.start_time is not None and time.time() - self.start_time >= self.stabilization_time:
            self._finalize_detection()
            return self.detect_slit(frame)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        binary = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 11, 2)
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        edges = cv2.Canny(binary, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80, minLineLength=50, maxLineGap=20)
        

        if lines is None:
            self.processing_times.append(time.time() - start_time)
            return self.prev_slit_bbox, frame

        h, w = frame.shape[:2]
        center_x = w // 2
        best_line = None
        best_score = float('inf')

        for line in lines:
            x1, y1, x2, y2 = line[0]
            dx, dy = x2 - x1, y2 - y1
            if abs(dx) < 1: slope_error = 0
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

        slit_bbox = (center[0], center[1], length, width, angle)  # Updated ordering to match rotated_rect
        self.detected_slits.append(slit_bbox)
        if len(self.detected_slits) > 30:
            self.detected_slits = self.detected_slits[-30:]
        if self.prev_slit_bbox is not None:
            slit_bbox = self.smooth_bbox(slit_bbox, self.prev_slit_bbox)
        self.prev_slit_bbox = slit_bbox
        self.processing_times.append(time.time() - start_time)
        self.success_count += 1
        return slit_bbox, frame

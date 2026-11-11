# # PATCH: Correct the alignment of the rotated slit bounding box
# # Use (length, width) instead of (width, length) so the long edge aligns with the angle.
# 
# # enhanced_slit_detection.py
# import cv2
# import numpy as np
# import time
# import math
# 
# class SlitDetector:
#     def __init__(self, stabilization_time=5.0, debug=False):
#         self.stabilization_time = stabilization_time
#         self.start_time = None
#         self.is_active = False
#         self.is_finalized = False
#         self.final_slit = None
#         self.detected_slits = []
#         self.prev_slit_bbox = None
#         self.alpha = 0.3
#         self.debug = debug
#         self.detection_count = 0
#         self.success_count = 0
#         self.processing_times = []
# 
#     def start_detection(self):
#         self.is_active = True
#         self.is_finalized = False
#         self.start_time = time.time()
#         self.detected_slits = []
#         self.final_slit = None
#         print("Slit detection started")
# 
#     def stop_detection(self):
#         self.is_active = False
#         self.is_finalized = False
#         self.start_time = None
#         if self.detection_count > 0:
#             success_rate = (self.success_count / self.detection_count) * 100
#             avg_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
#             print(f"Slit detection stopped. Success rate: {success_rate:.1f}%, Avg processing time: {avg_time*1000:.1f}ms")
#         else:
#             print("Slit detection stopped (no frames processed)")
# 
#     def smooth_bbox(self, new_bbox, old_bbox):
#         if len(new_bbox) == 5:
#             return (
#                 int(self.alpha * new_bbox[0] + (1 - self.alpha) * old_bbox[0]),
#                 int(self.alpha * new_bbox[1] + (1 - self.alpha) * old_bbox[1]),
#                 int(self.alpha * new_bbox[2] + (1 - self.alpha) * old_bbox[2]),
#                 int(self.alpha * new_bbox[3] + (1 - self.alpha) * old_bbox[3]),
#                 self.alpha * new_bbox[4] + (1 - self.alpha) * old_bbox[4]
#             )
#         else:
#             return tuple(int(self.alpha * n + (1 - self.alpha) * o) for n, o in zip(new_bbox, old_bbox))
# 
#     def _finalize_detection(self):
#         if not self.detected_slits:
#             print("Warning: No slits detected during stabilization period")
#             self.is_finalized = True
#             return
#         x_vals = [b[0] for b in self.detected_slits]
#         y_vals = [b[1] for b in self.detected_slits]
#         w_vals = [b[2] for b in self.detected_slits]
#         h_vals = [b[3] for b in self.detected_slits]
#         a_vals = [b[4] for b in self.detected_slits]
#         avg = lambda vals: sum(vals) / len(vals)
#         self.final_slit = (avg(x_vals), avg(y_vals), avg(w_vals), avg(h_vals), avg(a_vals))
#         self.is_finalized = True
#         print(f"Slit detection finalized at {self.final_slit}")
# 
#     def detect_slit(self, frame):
#         start_time = time.time()
#         self.detection_count += 1
#         viz_frame = frame.copy() if self.debug else frame
# 
#         if self.is_finalized and self.final_slit is not None:
#             center, size, angle = (self.final_slit[0:2], (self.final_slit[2], self.final_slit[3]), self.final_slit[4])
#             box = cv2.boxPoints((center, size, angle))
#             box = np.int0(box)
#             cv2.drawContours(frame, [box], 0, (0, 0, 255), 2)
#             cv2.putText(frame, "FINALIZED SLIT", (int(center[0]), int(center[1])-10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
#             self.processing_times.append(time.time() - start_time)
#             self.success_count += 1
#             return self.final_slit, frame
# 
#         if not self.is_active:
#             self.processing_times.append(time.time() - start_time)
#             return self.prev_slit_bbox, frame
# 
#         if self.start_time is not None and time.time() - self.start_time >= self.stabilization_time:
#             if not self.is_finalized:
#                 self._finalize_detection()
#             self.processing_times.append(time.time() - start_time)
#             return self.final_slit, frame
# 
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         blur = cv2.GaussianBlur(gray, (5, 5), 0)
#         binary = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#                                        cv2.THRESH_BINARY_INV, 11, 2)
#         kernel = np.ones((3, 3), np.uint8)
#         binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
#         edges = cv2.Canny(binary, 50, 150)
#         lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80, minLineLength=50, maxLineGap=20)
# 
#         if lines is None:
#             self.processing_times.append(time.time() - start_time)
#             return self.prev_slit_bbox, frame
# 
#         h, w = frame.shape[:2]
#         center_x = w // 2
#         best_line = None
#         best_score = float('inf')
# 
#         for line in lines:
#             x1, y1, x2, y2 = line[0]
#             dx, dy = x2 - x1, y2 - y1
#             if abs(dx) < 1: slope_error = 0
#             else:
#                 slope = dy / float(dx)
#                 if abs(slope) < 1:
#                     continue
#                 slope_error = 1.0 / abs(slope + 1e-9)
#             mid_x = (x1 + x2) / 2.0
#             center_error = abs(mid_x - center_x)
#             length = np.sqrt(dx * dx + dy * dy)
#             length_bonus = 100.0 / (length + 1e-9)
#             score = slope_error + 0.01 * center_error + length_bonus
#             if score < best_score:
#                 best_score = score
#                 best_line = (x1, y1, x2, y2)
# 
#         if best_line is None:
#             self.processing_times.append(time.time() - start_time)
#             return self.prev_slit_bbox, frame
# 
#         x1, y1, x2, y2 = best_line
#         if y1 > y2:
#             x1, y1, x2, y2 = x2, y2, x1, y1
# 
#         cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
#         center = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
#         length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
#         angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
#         width = 30
#         rotated_rect = (center, (length, width), angle)  # FIXED: swapped length/width
#         box = cv2.boxPoints(rotated_rect)
#         box = np.int0(box)
#         cv2.drawContours(frame, [box], 0, (255, 0, 0), 2)
# 
#         slit_bbox = (center[0], center[1], length, width, angle)  # Updated ordering to match rotated_rect
#         self.detected_slits.append(slit_bbox)
#         if len(self.detected_slits) > 30:
#             self.detected_slits = self.detected_slits[-30:]
#         if self.prev_slit_bbox is not None:
#             slit_bbox = self.smooth_bbox(slit_bbox, self.prev_slit_bbox)
#         self.prev_slit_bbox = slit_bbox
#         self.processing_times.append(time.time() - start_time)
#         self.success_count += 1
#         return slit_bbox, frame





# enhanced_slit_detection.py
#
# Finds the blade slit (kerf) as a vertical dark groove and locks a danger box on
# it. For a full, diagram-driven explanation of how this works (pipeline, the
# groove-ratio scoring, clustering + medoid finalize, and the fail-safe) see
# HOW_SLIT_DETECTION_WORKS.md. Design rules to keep in mind while editing:
#   1. No absolute pixel positions or brightness thresholds -- every cue is
#      relative (a contrast ratio / a fraction of frame width or height) so the
#      detector ports across bandsaws, cameras, and lighting.
#   2. Loud failure beats a confident wrong box: when unsure, final_slit = None
#      and is_slit_missing() is True (caller drives the red LED).
import cv2
import numpy as np
import time
import math

class SlitDetector:
    def __init__(self, stabilization_time=5.0, debug=False):
        """
        Initialize slit detector
        
        Args:
            stabilization_time: Time in seconds to finalize slit detection
            debug: Enable debug output and visualization
        """
        self.stabilization_time = stabilization_time
        self.start_time = None
        self.is_active = False
        self.is_finalized = False
        self.final_slit = None
        self.calibration_cx = None
        self.detected_slits = []
        self.prev_slit_data = None
        self.alpha = 0.3  # Smoothing factor
        self.debug = debug
        # Fail-safe: minimum fraction of calibration frames that must yield a
        # groove-like slit, else we report "slit not found" rather than locking
        # a low-confidence box. Relative (a fraction), so it is machine-agnostic.
        self.min_hit_frac = 0.35
        self.win_attempts = 0
        self.win_hits = 0
        self.frame_w = None   # set per frame; used for the relative cluster gap
        # Live-fps guard: the calibration window is wall-clock based, but on the
        # live Pi the main loop shares the CPU with MediaPipe, recording and the
        # GUI, so 5 s can mean only a handful of frames -- and a consensus vote
        # over so few samples is hostage to one blurry/sawdust frame (recordings
        # replay much faster, which is why clips looked fine but live didn't).
        # Require a minimum number of groove votes before locking; if votes are
        # short when time is up, keep collecting up to max_calib_factor x
        # stabilization_time, then finalize anyway and let the fail-safe judge
        # the (weak) evidence.
        self.min_calib_hits = 20
        self.max_calib_factor = 3.0
        # Speed: run the heavy threshold/morph/Canny/Hough stage on a frame
        # downscaled by this factor (line coords are scaled back afterwards;
        # groove scoring stays FULL-RES, see detect_slit). More live fps ->
        # more votes in the calibration window.
        self.proc_scale = 0.5
        
        # Performance tracking
        self.detection_count = 0
        self.success_count = 0
        self.processing_times = []
    
    def start_detection(self):
        """Start slit detection process"""
        self.is_active = True
        self.is_finalized = False
        self.start_time = time.time()
        self.calibration_cx = None
        self.detected_slits = []
        self.final_slit = None
        # Fail-safe consistency tracking over the stabilization window.
        self.win_attempts = 0   # frames processed during calibration
        self.win_hits = 0       # frames that yielded a groove-like slit
        print("Slit detection started")
    
    def stop_detection(self):
        """Stop slit detection process"""
        self.is_active = False
        self.is_finalized = False
        self.start_time = None
        
        # Show performance stats if we've processed frames
        if self.detection_count > 0:
            success_rate = (self.success_count / self.detection_count) * 100
            avg_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
            print(f"Slit detection stopped. Success rate: {success_rate:.1f}%, Avg processing time: {avg_time*1000:.1f}ms")
        else:
            print("Slit detection stopped (no frames processed)")
    
    def smooth_data(self, new_data, old_data):
        """Smooths the new slit data with the previous one"""
        # For rotated rect (center_x, center_y, width, height, angle)
        if len(new_data) == 5 and len(old_data) == 5:
            # For the angle, we need special handling to avoid jumps between -90 and 90 degrees
            cx, cy, w, h, new_angle = new_data
            ocx, ocy, ow, oh, old_angle = old_data
            
            # Smooth center, width, height
            smoothed_cx = self.alpha * cx + (1 - self.alpha) * ocx
            smoothed_cy = self.alpha * cy + (1 - self.alpha) * ocy
            smoothed_w = self.alpha * w + (1 - self.alpha) * ow
            smoothed_h = self.alpha * h + (1 - self.alpha) * oh
            
            # Smooth angle (accounting for wraparound between -90 and 90)
            angle_diff = new_angle - old_angle
            # Handle wraparound (e.g., -85 to 85 degrees should be treated as 10 degrees difference)
            if angle_diff > 90:
                angle_diff -= 180
            elif angle_diff < -90:
                angle_diff += 180
                
            smoothed_angle = old_angle + self.alpha * angle_diff
            # Keep angle within [-90, 90] range
            if smoothed_angle > 90:
                smoothed_angle -= 180
            elif smoothed_angle < -90:
                smoothed_angle += 180
                
            return (smoothed_cx, smoothed_cy, smoothed_w, smoothed_h, smoothed_angle)
        
        # For extended data with line endpoints (cx, cy, w, h, angle, x1, x2, y1, y2)
        if len(new_data) >= 7 and len(old_data) >= 7:
            # Extract basic components
            if len(new_data) == 9 and len(old_data) == 9:
                cx, cy, w, h, new_angle, x1, x2, y1, y2 = new_data
                ocx, ocy, ow, oh, old_angle, ox1, ox2, oy1, oy2 = old_data
            else:
                # Handle the older tuple-based format
                cx, cy, w, h, new_angle, new_endpoints, new_y_endpoints = new_data
                ocx, ocy, ow, oh, old_angle, old_endpoints, old_y_endpoints = old_data
                
                # Extract endpoints
                x1, x2 = new_endpoints
                y1, y2 = new_y_endpoints
                ox1, ox2 = old_endpoints
                oy1, oy2 = old_y_endpoints
            
            # Smooth center, width, height
            smoothed_cx = self.alpha * cx + (1 - self.alpha) * ocx
            smoothed_cy = self.alpha * cy + (1 - self.alpha) * ocy
            smoothed_w = self.alpha * w + (1 - self.alpha) * ow
            smoothed_h = self.alpha * h + (1 - self.alpha) * oh
            
            # Smooth angle
            angle_diff = new_angle - old_angle
            if angle_diff > 90:
                angle_diff -= 180
            elif angle_diff < -90:
                angle_diff += 180
            smoothed_angle = old_angle + self.alpha * angle_diff
            if smoothed_angle > 90:
                smoothed_angle -= 180
            elif smoothed_angle < -90:
                smoothed_angle += 180
                
            # Smooth endpoints
            smoothed_x1 = self.alpha * x1 + (1 - self.alpha) * ox1
            smoothed_x2 = self.alpha * x2 + (1 - self.alpha) * ox2
            smoothed_y1 = self.alpha * y1 + (1 - self.alpha) * oy1
            smoothed_y2 = self.alpha * y2 + (1 - self.alpha) * oy2
            
            # Use the new flat format (better for serialization)
            return (smoothed_cx, smoothed_cy, smoothed_w, smoothed_h, smoothed_angle, 
                   smoothed_x1, smoothed_x2, smoothed_y1, smoothed_y2)
            
        # Default fallback - just return new data
        return new_data
    
    def _cluster_by_cx(self, slits, gap):
        """Group detections whose center-x are within `gap` px into clusters.
        Vertical-line candidates differ mainly in horizontal position, so a real
        kerf and a competing seam land in separate clusters."""
        items = sorted(slits, key=lambda s: s[0])
        clusters = [[items[0]]]
        for s in items[1:]:
            if s[0] - clusters[-1][-1][0] <= gap:
                clusters[-1].append(s)
            else:
                clusters.append([s])
        return clusters

    def _cluster_medoid(self, cluster):
        """Return the cluster member closest to the cluster's component-wise
        median over the geometric coords (cx, cy, x1, x2, y1, y2). This is a
        REAL observed detection, never a synthesized average -- so the locked
        box can't land between two candidate slits, and the angle stays
        consistent with its own endpoints (no wraparound averaging)."""
        idx = [0, 1, 5, 6, 7, 8]   # cx, cy, x1, x2, y1, y2 in the 9-tuple
        med = [float(np.median([s[i] for s in cluster])) for i in idx]
        return min(cluster, key=lambda s: sum((s[i] - m) ** 2
                                               for i, m in zip(idx, med)))

    def _finalize_detection(self):
        """Lock the consensus detection over the calibration window.

        Robust aggregation: cluster the per-frame detections by horizontal
        position, take the dominant cluster, and lock its MEDOID (the single
        actually-observed detection nearest the cluster centre). We never average
        across clusters, so the box cannot land *between* a real kerf and a
        competing seam -- it snaps to whichever slit the majority of frames saw.

        Fail-safe (red 'slit not found') fires when: no groove was found, it was
        found in too few frames, or the window is split between candidates with
        no clear winner (the detector genuinely cannot decide -- better loud than
        a confident wrong box)."""
        hit_frac = (self.win_hits / self.win_attempts) if self.win_attempts else 0.0
        slits = [s for s in self.detected_slits if len(s) >= 9]
        if not slits or hit_frac < self.min_hit_frac:
            print(f"Fail-safe: no confident slit (hits {self.win_hits}/"
                  f"{self.win_attempts} = {hit_frac:.0%}) -> SLIT NOT FOUND")
            self.final_slit = None
            self.is_finalized = True
            return

        # Cluster by center-x (relative gap -> machine-agnostic).
        gap = max(40.0, 0.06 * (self.frame_w or 1280))
        clusters = sorted(self._cluster_by_cx(slits, gap), key=len, reverse=True)
        dom = clusters[0]
        second = len(clusters[1]) if len(clusters) > 1 else 0
        n = len(slits)

        # Ambiguity guard: the winner must be a clear majority OR clearly larger
        # than the runner-up; otherwise the frames disagree about WHICH slit.
        if len(dom) <= 0.5 * n and len(dom) < 1.5 * max(1, second):
            print(f"Fail-safe: calibration split across candidates "
                  f"(dominant {len(dom)}/{n}, runner-up {second}) -> SLIT NOT FOUND")
            self.final_slit = None
            self.is_finalized = True
            return

        # Lock the medoid of the dominant cluster (a real observed box).
        self.final_slit = self._cluster_medoid(dom)
        self.is_finalized = True
        print(f"Slit detection finalized (medoid of {len(dom)}/{n} agreeing "
              f"frames) at cx={self.final_slit[0]:.0f}")

    def is_slit_missing(self):
        """True once calibration finished but no confident slit was located --
        the fail-safe state. The caller should drive a red alert: the system
        cannot protect what it cannot find."""
        return self.is_finalized and self.final_slit is None

    def _draw_no_slit_warning(self, frame):
        """Prominent fail-safe overlay when no slit was located."""
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0, 0), (w, 74), (0, 0, 180), -1)
        cv2.putText(frame, "SLIT NOT FOUND - CHECK CAMERA MOUNT", (18, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    def _groove_ratio(self, gray, x1, y1, x2, y2):
        """Relative (lighting-independent) groove strength of a near-vertical
        candidate line: how much darker the line is than the table on BOTH
        flanks. This is the one universal physical property of a slit (a thin
        gap is darker than the material flanking it), so it must NOT use an
        absolute gray threshold -- it returns a contrast RATIO.

        For each sample point along the line we compare the line's gray value to
        the gray value `flank` px to the left and right (flanks are horizontal
        for a vertical line). A real groove is darker than the SHALLOWER flank;
        a step-edge (machine fence/body) is darker than only one side and scores
        near zero. Returns mean( (min_flank - center) / (min_flank + eps) ),
        clipped at 0; range ~0 (no groove) .. ~0.5 (deep clean groove)."""
        gh, gw = gray.shape[:2]
        flank = max(4, int(round(0.012 * gw)))  # ~15px @1280; relative to width
        n = 15
        total, used = 0.0, 0
        for i in range(n):
            t = (i + 0.5) / n
            px = int(round(x1 + (x2 - x1) * t))
            py = int(round(y1 + (y2 - y1) * t))
            lx, rx = px - flank, px + flank
            if lx < 0 or rx >= gw or py < 0 or py >= gh:
                continue
            center = float(gray[py, px])
            left = float(gray[py, lx])
            right = float(gray[py, rx])
            min_flank = min(left, right)       # darker of the two flanks
            if min_flank <= center:            # not darker than both flanks
                continue
            total += (min_flank - center) / (min_flank + 1e-6)
            used += 1
        if used < n * 0.4:                     # groove must be consistent along the run
            return 0.0
        return total / used

    def _select_slit_line(self, gray, vertical_lines):
        """Pick the candidate that best matches a real blade kerf, instead of
        just the longest vertical line (which grabs the machine fence / frame
        border). Scoring is deliberately machine-agnostic:
          * groove ratio (PRIMARY, universal physical cue, relative/contrast)
          * length (mild boost)                     -- relative to frame height
          * center bias (SOFT mount convention)     -- relative to frame width
          * frame-edge reject (HARD mount convention) -- relative to width
        No absolute pixel positions or gray thresholds, so it ports across
        bandsaws / camera distances (see CLAUDE.md mounting guideline)."""
        h, w = gray.shape[:2]
        cx = w / 2.0
        edge_margin = max(8, int(round(0.03 * w)))   # reject lines hugging the border
        len_weight, center_weight, min_groove = 0.5, 0.5, 0.05

        best, best_score = None, -1.0
        edge_candidate, edge_score = None, -1.0
        scored = []
        for (x1, y1, x2, y2, angle) in vertical_lines:
            mid_x = (x1 + x2) / 2.0
            groove = self._groove_ratio(gray, x1, y1, x2, y2)
            if groove < min_groove:              # PRIMARY gate: must be a groove
                continue
            length = math.hypot(x2 - x1, y2 - y1)
            len_norm = min(1.0, length / float(h))
            center_pen = abs(mid_x - cx) / (w / 2.0)          # 0 center .. 1 edge
            center_factor = 1.0 - center_weight * center_pen  # SOFT multiplier
            score = groove * (1.0 + len_weight * len_norm) * center_factor
            scored.append((score, groove, (x1, y1, x2, y2, angle)))
            # Keep edge grooves as camera guidance only; they remain ineligible
            # for selection as the safety slit.
            if mid_x < edge_margin or mid_x > w - edge_margin:
                if score > edge_score:
                    edge_score, edge_candidate = score, mid_x
                continue
            if score > best_score:
                best_score, best = score, (x1, y1, x2, y2, angle)

        if best is not None:
            self.calibration_cx = (best[0] + best[2]) / 2.0
        else:
            self.calibration_cx = edge_candidate

        if self.debug and scored:
            scored.sort(reverse=True)
            for s, g, ln in scored[:3]:
                print(f"  cand mid_x={(ln[0]+ln[2])//2} groove={g:.3f} score={s:.3f}")
        return best

    def detect_slit(self, frame):
        """
        Detect slits in the video frame
        
        Args:
            frame: The video frame to analyze
            
        Returns:
            The detected slit data and the processed frame
        """
        start_process_time = time.time()
        self.detection_count += 1
        self.calibration_cx = None
        
        # Create a copy of the frame for visualization
        viz_frame = frame.copy() if self.debug else frame
        
        # If detection is finalized, return the final slit
        if self.is_finalized:
            # Fail-safe: calibration finished but no confident slit was found.
            # Do NOT lock a wrong box -- warn loudly and return None so the
            # caller can drive a red alert (we cannot protect what we cannot
            # locate). Handling it here also avoids re-triggering finalize.
            if self.final_slit is None:
                self._draw_no_slit_warning(frame)
                self.processing_times.append(time.time() - start_process_time)
                return None, frame
            # Check what kind of data we have
            if len(self.final_slit) >= 7:  # Extended format with endpoints
                # Extract data based on format
                if len(self.final_slit) == 9:
                    cx, cy, width, height, angle, x1, x2, y1, y2 = self.final_slit
                else:
                    # Handle older tuple format
                    cx, cy, width, height, angle, endpoints, y_endpoints = self.final_slit
                    x1, x2 = endpoints
                    y1, y2 = y_endpoints
                
                # Draw the endpoints
                cv2.circle(frame, (int(x1), int(y1)), 3, (0, 0, 255), -1)  # Left endpoint
                cv2.circle(frame, (int(x2), int(y2)), 3, (0, 0, 255), -1)  # Right endpoint
                
                # Draw a line connecting the endpoints
                cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
                
                # Draw a rotated rectangle that covers the entire slit
                rect = ((cx, cy), (width, height), angle)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                cv2.drawContours(frame, [box], 0, (0, 255, 0), 2)  # Green for "DESIRED SLIT"
                
                # Add angle info
                cv2.putText(frame, f"ANGLE: {angle:.1f}°", (int(cx), int(cy) - 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Changed text to "DESIRED SLIT"
                cv2.putText(frame, "DESIRED SLIT", (int(cx), int(cy) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
            elif len(self.final_slit) == 5:  # Standard rotated rectangle
                center_x, center_y, width, height, angle = self.final_slit
                
                # Create the rotated rectangle
                rect = ((center_x, center_y), (width, height), angle)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                cv2.drawContours(frame, [box], 0, (0, 255, 0), 2)  # Green for "DESIRED SLIT"
                
                # Add angle info
                cv2.putText(frame, f"ANGLE: {angle:.1f}°", (int(center_x), int(center_y) - 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Changed text to "DESIRED SLIT"
                cv2.putText(frame, "DESIRED SLIT", (int(center_x), int(center_y) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
            else:  # Standard bbox (x, y, w, h)
                bx, by, bw, bh = self.final_slit
                cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, 255, 0), 2)  # Green for "DESIRED SLIT"
                cv2.putText(frame, "DESIRED SLIT", (bx, by - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            self.processing_times.append(time.time() - start_process_time)
            self.success_count += 1
            return self.final_slit, frame
        
        # If detection is not active, return previous slit if available
        if not self.is_active:
            if self.prev_slit_data is not None:
                # Display previous detection based on format
                if len(self.prev_slit_data) >= 7:
                    if len(self.prev_slit_data) == 9:
                        cx, cy, width, height, angle, x1, x2, y1, y2 = self.prev_slit_data
                    else:
                        # Handle older tuple format
                        cx, cy, width, height, angle, endpoints, y_endpoints = self.prev_slit_data
                        x1, x2 = endpoints
                        y1, y2 = y_endpoints
                    
                    # Draw the endpoints and connecting line
                    cv2.circle(frame, (int(x1), int(y1)), 3, (255, 0, 0), -1)
                    cv2.circle(frame, (int(x2), int(y2)), 3, (255, 0, 0), -1)
                    cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
                    
                    # Draw the rotated rectangle
                    rect = ((cx, cy), (width, height), angle)
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)
                    cv2.drawContours(frame, [box], 0, (255, 0, 0), 2)
                    
                elif len(self.prev_slit_data) == 5:  # Rotated bbox
                    center_x, center_y, width, height, angle = self.prev_slit_data
                    rect = ((center_x, center_y), (width, height), angle)
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)
                    cv2.drawContours(frame, [box], 0, (255, 0, 0), 2)
                    
                else:  # Standard bbox
                    bx, by, bw, bh = self.prev_slit_data
                    cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (255, 0, 0), 2)
                
                self.processing_times.append(time.time() - start_process_time)
                return self.prev_slit_data, frame
            else:
                self.processing_times.append(time.time() - start_process_time)
                return None, frame
        
        # Check if it's time to finalize detection. Time elapsing is necessary
        # but not sufficient: we also need enough groove votes (min_calib_hits)
        # for the consensus to mean anything at low live fps. If votes are
        # still short, keep collecting -- up to max_calib_factor x the window,
        # after which we finalize regardless and the fail-safe (min_hit_frac /
        # ambiguity guard) judges whatever evidence there is.
        current_time = time.time()
        if self.start_time is not None:
            elapsed = current_time - self.start_time
            if elapsed >= self.stabilization_time and (
                    self.win_hits >= self.min_calib_hits or
                    elapsed >= self.stabilization_time * self.max_calib_factor):
                self._finalize_detection()
                return self.detect_slit(frame)  # Re-run with finalized state

        # We are processing a calibration frame; count it for the fail-safe
        # consistency check (win_hits is incremented once a groove is chosen).
        self.win_attempts += 1

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Speed (live fps): run the heavy threshold/morph/Canny/Hough stage on a
        # DOWNSCALED copy, then scale the detected line coordinates back up.
        # Everything that decides which candidate wins -- groove-ratio scoring,
        # selection, the segment-extension steps -- still runs on the full-res
        # `gray`, so detection *quality* is unchanged; we only pay less for the
        # candidate search. The spatial params below are scaled with the image
        # so candidates are equivalent to what full-res processing would find.
        s = self.proc_scale
        if s < 1.0:
            proc = cv2.resize(gray, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        else:
            proc = gray

        # Apply Gaussian blur
        gray_blur = cv2.GaussianBlur(proc, (5, 5), 0)

        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray_blur, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11, 2
        )

        # Apply morphological operations to enhance vertical features
        # Use a taller vertical kernel to enhance vertical lines (the blade slit
        # runs roughly top-to-bottom in our camera mounts)
        v_kernel = np.ones((max(3, int(round(25 * s))), 1), np.uint8)  # Tall vertical kernel
        binary = cv2.erode(binary, v_kernel, iterations=1)
        binary = cv2.dilate(binary, v_kernel, iterations=2)  # Extra dilation to connect gaps
        
        # Show preprocessing steps if in debug mode
        if self.debug:
            debug_display = np.hstack([gray_blur, binary])
            debug_display = cv2.resize(debug_display, (frame.shape[1], frame.shape[0]//3))
            cv2.putText(debug_display, "Blur | Binary", (10, 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 1)
            
            # Display in bottom part of the frame
            frame_bottom = frame.shape[0] - debug_display.shape[0]
            frame[frame_bottom:, :debug_display.shape[1]] = debug_display
        
        # Detect edges
        edges = cv2.Canny(binary, 50, 150, apertureSize=3)
        
        # Use HoughLinesP to detect lines with parameters adjusted for vertical
        # lines. Vote threshold / lengths / gaps are in pixels of the processed
        # image, so they scale with proc_scale to stay equivalent to full-res.
        lines = cv2.HoughLinesP(edges,
                                rho=1,
                                theta=np.pi/180,
                                threshold=max(10, int(round(40 * s))),  # Even lower threshold to detect more candidate lines
                                minLineLength=max(10, int(round(40 * s))),  # Reduced to catch shorter segments
                                maxLineGap=max(10, int(round(50 * s))))  # Increased to bridge larger gaps

        if lines is None:
            if self.debug:
                print("No lines detected")
            self.processing_times.append(time.time() - start_process_time)
            return self.prev_slit_data, frame

        # Scale line coordinates back up to full-res so every downstream step
        # (groove scoring on full-res gray, selection, extension, drawing)
        # works in real frame pixels.
        if s < 1.0:
            inv = 1.0 / s
            lines = [[[int(round(v * inv)) for v in ln[0]]] for ln in lines]
        
        h, w = frame.shape[:2]
        center_x = w // 2
        self.frame_w = w   # remembered for the relative cluster gap at finalize

        # Step 1: Collect all valid vertical line segments
        vertical_lines = []

        for line in lines:
            x1, y1, x2, y2 = line[0]

            # Draw all detected lines in debug mode
            if self.debug:
                cv2.line(viz_frame, (x1, y1), (x2, y2), (0, 255, 255), 1)

            dx = abs(x2 - x1)  # Use absolute difference
            dy = abs(y2 - y1)  # Use absolute difference

            # Skip if not primarily vertical (strong vertical bias)
            if dy < 1.5*dx:  # Relaxed vertical bias a bit
                continue

            # Calculate angle (vertical lines are close to +/-90 degrees)
            angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
            # Normalize angle to be between -90 and 90
            if angle > 90:
                angle -= 180
            elif angle < -90:
                angle += 180

            # Skip very non-vertical lines (vertical => |angle| near 90)
            if abs(angle) < 45:
                continue

            # Ensure the line is oriented from top to bottom
            if y1 > y2:
                x1, y1, x2, y2 = x2, y2, x1, y1

            # Add the line to our collection
            vertical_lines.append((x1, y1, x2, y2, angle))

        if not vertical_lines:
            if self.debug:
                print("No vertical lines detected")
            self.processing_times.append(time.time() - start_process_time)
            return self.prev_slit_data, frame

        # Step 2: Choose the candidate that best matches a real blade kerf
        # (groove appearance + center/edge mount conventions), NOT just the
        # longest vertical line -- which grabs the machine fence / frame border.
        best_line = self._select_slit_line(gray, vertical_lines)
        if best_line is None:
            # No candidate looks like a dark groove away from the frame edge.
            # Fail safe: don't lock onto a non-groove line.
            if self.debug:
                print("No groove-like vertical slit candidate")
            self.processing_times.append(time.time() - start_process_time)
            return self.prev_slit_data, frame
        self.win_hits += 1  # a groove-like candidate was found this frame
        x1, y1, x2, y2, angle = best_line

        # Step 3: Find additional line segments that could extend the slit
        # Look for line segments that could extend the detected line
        # This helps capture the full length of a slit that might be broken into segments
        for line in vertical_lines:
            lx1, ly1, lx2, ly2, _ = line

            # Skip the line if it's the best line itself
            if (lx1, ly1, lx2, ly2) == (x1, y1, x2, y2):
                continue

            # Check if the line is roughly at the same horizontal position (x-coordinate)
            width_diff = abs(((lx1 + lx2) / 2) - ((x1 + x2) / 2))
            if width_diff > 20:  # Tolerance for horizontal offset
                continue

            # Check if this line extends our current line upward
            if ly1 < y1 and abs(ly2 - y1) < 40:  # The bottom of this line is near the top of best line
                # Extend best line upward
                y1 = ly1

            # Check if this line extends our current line downward
            if ly2 > y2 and abs(ly1 - y2) < 40:  # The top of this line is near the bottom of best line
                # Extend best line downward
                y2 = ly2

        # Step 4: Special check for intersection with horizontal component
        # Look for any horizontal lines that might indicate the top boundary of the slit
        # This helps ensure we capture the entire slit including where it meets a horizontal component
        horizontal_lines = []
        for line in lines:
            hx1, hy1, hx2, hy2 = line[0]

            dx = abs(hx2 - hx1)
            dy = abs(hy2 - hy1)

            # Only consider horizontal-ish lines
            if dy > dx / 1.5:
                continue

            # Calculate angle
            h_angle = math.degrees(math.atan2(hy2 - hy1, hx2 - hx1))
            if h_angle > 90:
                h_angle -= 180
            elif h_angle < -90:
                h_angle += 180

            # Must be near-horizontal
            if abs(h_angle) > 45:
                continue

            # Ensure left-to-right orientation
            if hx1 > hx2:
                hx1, hy1, hx2, hy2 = hx2, hy2, hx1, hy1

            horizontal_lines.append((hx1, hy1, hx2, hy2))

        # Find horizontal lines that could intersect with our vertical line
        for hline in horizontal_lines:
            hx1, hy1, hx2, hy2 = hline

            # Check if this horizontal line is near the top end of our vertical line
            if abs(hy1 - y1) < 30 and abs(hy2 - y1) < 30:
                # Find the x value where this horizontal line intersects the x-level of our vertical line
                x_avg = (x1 + x2) / 2
                if min(hx1, hx2) <= x_avg <= max(hx1, hx2):
                    # This horizontal line intersects with our vertical line's top end
                    # Adjust the top y-coordinate of our vertical line to include this intersection
                    y1 = min(y1, hy1, hy2)
        
        # Draw the identified slit line
        cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        
        # Mark the endpoints
        cv2.circle(frame, (int(x1), int(y1)), 3, (0, 0, 255), -1)  # Left endpoint
        cv2.circle(frame, (int(x2), int(y2)), 3, (0, 255, 0), -1)  # Right endpoint
        
        # Calculate midpoint of the line
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        # Calculate length of the line
        line_length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        
        # Create a rotated rectangle - slightly thicker than before
        slit_height = 25  # Slightly thicker to ensure full coverage
        slit_width = line_length * 1.1  # Add 10% to length to ensure full coverage
        
        # Adjust midpoint to account for the added length
        mid_x = (x1 + x2) / 2
        
        # Create the rotated rectangle data with endpoints
        # Using a flat structure instead of nested tuples for better serialization
        slit_data = (mid_x, mid_y, slit_width, slit_height, angle, x1, x2, y1, y2)
        
        # Add to detected slits for stabilization
        self.detected_slits.append(slit_data)
        
        # Limit the number of stored detections
        if len(self.detected_slits) > 30:
            self.detected_slits = self.detected_slits[-30:]
        
        # Apply smoothing if we have previous data
        if self.prev_slit_data is not None and len(self.prev_slit_data) >= 5:
            slit_data = self.smooth_data(slit_data, self.prev_slit_data)
        
        # Draw the rotated bounding box
        cx, cy, width, height, bbox_angle = slit_data[:5]
        rect = ((cx, cy), (width, height), bbox_angle)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        cv2.drawContours(frame, [box], 0, (255, 0, 0), 2)
        
        # Add angle information
        cv2.putText(frame, f"ANGLE: {bbox_angle:.1f}°", (int(cx), int(cy) - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        
        cv2.putText(frame, "DETECTED SLIT", (int(cx), int(cy) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        
        # Update previous data
        self.prev_slit_data = slit_data
        
        # Track processing time
        self.processing_times.append(time.time() - start_process_time)
        self.success_count += 1
        
        return slit_data, frame

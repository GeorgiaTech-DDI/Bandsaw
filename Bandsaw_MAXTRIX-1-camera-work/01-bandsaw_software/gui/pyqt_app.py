import sys
import time
import threading
import cv2
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

try:
    # Try to import Pi camera wrapper (Raspberry Pi)
    from bandsaw.video_capture import PiCameraCapture, VideoRecorder
except Exception:
    PiCameraCapture = None
    VideoRecorder = None

try:
    from bandsaw.hand_detection import detect_hands
except Exception:
    def detect_hands(frame):
        return [], frame

try:
    from bandsaw.slit_detection import SlitDetector
except Exception:
    SlitDetector = None


class CameraHandler:
    def __init__(self, source=0):
        self.source = source
        self.is_pi = False
        self.pi_cam = None
        self.cap = None

    def open(self):
        if PiCameraCapture is not None:
            try:
                self.pi_cam = PiCameraCapture()
                self.is_pi = True
                return True
            except Exception:
                self.pi_cam = None

        # Fallback to OpenCV VideoCapture
        self.cap = cv2.VideoCapture(self.source)
        return self.cap.isOpened()

    def get_frame(self):
        if self.is_pi and self.pi_cam:
            ok, frame = self.pi_cam.get_frame()
            return ok, frame
        if self.cap:
            ok, frame = self.cap.read()
            return ok, frame
        return False, None

    def release(self):
        if self.is_pi and self.pi_cam:
            try:
                self.pi_cam.release()
            except Exception:
                pass
            self.pi_cam = None
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None


class SimpleVideoRecorder:
    def __init__(self, output_dir="recordings", fps=20.0, codec="mp4v"):
        self.writer = None
        self.output_dir = output_dir
        self.fps = fps
        self.fourcc = cv2.VideoWriter_fourcc(*codec)
        self.recording = False

    def start(self, frame, prefix="recording"):
        import os

        if self.recording:
            self.stop()
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        ts = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{ts}.mp4"
        path = os.path.join(self.output_dir, filename)
        h, w = frame.shape[:2]
        self.writer = cv2.VideoWriter(path, self.fourcc, self.fps, (w, h))
        if self.writer.isOpened():
            self.recording = True
            self.frame_count = 0
            self.path = path
            return path
        else:
            self.writer = None
            return None

    def write(self, frame):
        if not self.recording or self.writer is None:
            return False
        try:
            self.writer.write(frame)
            self.frame_count += 1
            return True
        except Exception:
            return False

    def stop(self):
        if self.writer:
            try:
                self.writer.release()
            except Exception:
                pass
        self.writer = None
        self.recording = False

    def is_recording(self):
        return self.recording


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bandsaw Monitor - PyQt")
        self.resize(900, 600)

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QtWidgets.QVBoxLayout(self.central_widget)

        self.video_label = QtWidgets.QLabel()
        self.video_label.setFixedSize(800, 480)
        self.video_label.setStyleSheet("background: black")
        layout.addWidget(self.video_label, alignment=QtCore.Qt.AlignCenter)

        btn_layout = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("Start")
        self.stop_btn = QtWidgets.QPushButton("Stop")
        self.record_btn = QtWidgets.QPushButton("Record")
        self.fullscreen_btn = QtWidgets.QPushButton("Fullscreen")
        self.quit_btn = QtWidgets.QPushButton("Quit")
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.record_btn)
        btn_layout.addWidget(self.fullscreen_btn)
        btn_layout.addWidget(self.quit_btn)
        layout.addLayout(btn_layout)

        self.status_label = QtWidgets.QLabel("Status: Stopped")
        layout.addWidget(self.status_label)

        # Auto record option (integrate with MPU monitor if available)
        self.autorec_checkbox = QtWidgets.QCheckBox("Auto-record on activity")
        layout.addWidget(self.autorec_checkbox)

        # Preview toggle: when unchecked, frames are not shown (but detection still runs)
        self.preview_checkbox = QtWidgets.QCheckBox("Show Preview")
        # start with preview hidden by default
        self.preview_checkbox.setChecked(False)
        layout.addWidget(self.preview_checkbox)

        # Mini preview option: show a small preview overlay
        self.mini_checkbox = QtWidgets.QCheckBox("Mini Preview")
        self.mini_checkbox.setChecked(False)
        layout.addWidget(self.mini_checkbox)

        # Handlers
        self.camera = CameraHandler()
        self.recorder = None
        if VideoRecorder is not None:
            try:
                self.recorder = VideoRecorder()
            except Exception:
                self.recorder = SimpleVideoRecorder()
        else:
            self.recorder = SimpleVideoRecorder()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)

        # Connections
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.record_btn.clicked.connect(self.toggle_record)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.quit_btn.clicked.connect(self.close)

        self.running = False

        # track fullscreen state
        self._is_fullscreen = False
        # original video label size
        self._default_video_size = (800, 480)
        self._mini_video_size = (16, 12)

        # Try to import bandsaw activity sensor
        try:
            from bandsaw.mpu_camera import bandsaw_active

            self._bandsaw_active_fn = bandsaw_active
        except Exception:
            self._bandsaw_active_fn = None
        # Slit detector
        if SlitDetector is not None:
            try:
                self.slit_detector = SlitDetector(stabilization_time=1.0, debug=False)
                self.slit_detector.start_detection()
            except Exception:
                self.slit_detector = None
        else:
            self.slit_detector = None

    def start(self):
        ok = self.camera.open()
        if not ok:
            self.status_label.setText("Status: Failed to open camera")
            return
        self.status_label.setText("Status: Running")
        self.running = True
        # Hide or show preview according to checkbox
        if self.mini_checkbox.isChecked():
            w, h = self._mini_video_size
            self.video_label.setFixedSize(w, h)
            self.video_label.show()
        elif not self.preview_checkbox.isChecked():
            self.video_label.hide()
        else:
            w, h = self._default_video_size
            self.video_label.setFixedSize(w, h)
            self.video_label.show()
        self.timer.start(30)

    def stop(self):
        self.running = False
        self.timer.stop()
        if self.camera:
            self.camera.release()
        if self.recorder and self.recorder.is_recording():
            self.recorder.stop()
        self.status_label.setText("Status: Stopped")

    def toggle_record(self):
        if not self.running:
            return
        if self.recorder.is_recording():
            self.recorder.stop()
            self.record_btn.setText("Record")
            self.status_label.setText("Status: Running (not recording)")
        else:
            # capture current frame to determine size
            ok, frame = self.camera.get_frame()
            if not ok:
                self.status_label.setText("Status: Failed to capture for recording")
                return
            path = self.recorder.start(frame, "bandsaw_gui")
            if path:
                self.record_btn.setText("Stop Rec")
                self.status_label.setText(f"Recording to: {path}")

    def toggle_fullscreen(self):
        if not self._is_fullscreen:
            self.showFullScreen()
            self.fullscreen_btn.setText("Exit Fullscreen")
            self._is_fullscreen = True
        else:
            self.showNormal()
            self.fullscreen_btn.setText("Fullscreen")
            self._is_fullscreen = False

    def _check_auto_record(self):
        if not self.autorec_checkbox.isChecked() or not self._bandsaw_active_fn:
            return
        try:
            active = self._bandsaw_active_fn()
        except Exception:
            active = False

        if active and not self.recorder.is_recording():
            ok, frame = self.camera.get_frame()
            if ok and frame is not None:
                path = self.recorder.start(frame, "bandsaw_auto")
                if path:
                    self.record_btn.setText("Stop Rec")
                    self.status_label.setText(f"Recording to: {path}")
        elif not active and self.recorder.is_recording():
            self.recorder.stop()
            self.record_btn.setText("Record")
            self.status_label.setText("Status: Running (not recording)")

    def update_frame(self):
        if not self.running:
            return
        ok, frame = self.camera.get_frame()
        if not ok or frame is None:
            return

        if self.recorder and self.recorder.is_recording():
            try:
                self.recorder.write(frame)
            except Exception:
                pass

        # Run slit detection and hand detection for safety overlay
        slit_bbox = None
        try:
            if self.slit_detector is not None:
                slit_bbox, frame = self.slit_detector.detect_slit(frame)
        except Exception:
            slit_bbox = None

        hand_bboxes = []
        try:
            hand_bboxes, frame = detect_hands(frame)
        except Exception:
            hand_bboxes = []

        # Determine if any hand is too close to slit
        def _hand_near_slit(hand_bbox, slit_bbox):
            if hand_bbox is None or slit_bbox is None:
                return False
            try:
                hx, hy, hw, hh = hand_bbox
                hand_rect = np.array([[hx, hy], [hx + hw, hy], [hx + hw, hy + hh], [hx, hy + hh]])

                sx, sy, sw, sh, angle = slit_bbox
                slit_center = (sx, sy)
                slit_size = (sw, sh)
                slit_box = cv2.boxPoints((slit_center, slit_size, angle))
                slit_box = np.intp(slit_box)

                hand_poly = cv2.convexHull(hand_rect)
                slit_poly = cv2.convexHull(slit_box)

                intersection = cv2.intersectConvexConvex(hand_poly, slit_poly)
                return intersection[0] > 0
            except Exception:
                return False

        any_too_close = False
        for hb in hand_bboxes:
            if _hand_near_slit(hb, slit_bbox):
                any_too_close = True
                break

        # Update visual background: green safe, red alert (covers whole window)
        if any_too_close:
            bg_css = "background-color: rgb(200,0,0);"
            self.status_label.setText("ALERT: Hand Too Close to Slit")
        else:
            bg_css = "background-color: rgb(0,180,0);"
            self.status_label.setText("Status: Running")
        # keep the video label black so video remains visible over the background
        self.central_widget.setStyleSheet(bg_css)

        # Convert frame (BGR -> RGB) if needed
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            rgb = frame

        # Only render and show preview if user enabled it
        show_preview = self.preview_checkbox.isChecked() or self.mini_checkbox.isChecked()
        if show_preview:
            if self.video_label.isHidden():
                self.video_label.show()
            # adjust size if mini preview toggled
            if self.mini_checkbox.isChecked():
                w, h = self._mini_video_size
                self.video_label.setFixedSize(w, h)
            else:
                w, h = self._default_video_size
                self.video_label.setFixedSize(w, h)

            h_img, w_img = rgb.shape[:2]
            qt_img = QtGui.QImage(rgb.data, w_img, h_img, 3 * w_img, QtGui.QImage.Format_RGB888)
            pix = QtGui.QPixmap.fromImage(qt_img).scaled(
                self.video_label.width(), self.video_label.height(), QtCore.Qt.KeepAspectRatio
            )
            self.video_label.setPixmap(pix)
        else:
            if not self.video_label.isHidden():
                self.video_label.hide()


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

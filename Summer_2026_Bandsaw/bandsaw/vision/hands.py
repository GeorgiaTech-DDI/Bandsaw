"""MediaPipe hand detection, initialized only when a detector is requested."""

import cv2
import numpy as np

hands_detector = None
mp_hands = None
mp_draw = None


def _load_mediapipe():
    try:
        import mediapipe as mp
    except ImportError as error:
        raise RuntimeError("Hand detection requires mediapipe") from error
    return mp


class HandDetector:
    """Independent hand detector; an existing MediaPipe model can be injected."""

    def __init__(self, model=None, drawing_utils=None, hand_connections=None):
        if model is None:
            mp = _load_mediapipe()
            model = mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.7,
            )
            drawing_utils = drawing_utils or mp.solutions.drawing_utils
            hand_connections = hand_connections or mp.solutions.hands.HAND_CONNECTIONS
        self.model = model
        self.drawing_utils = drawing_utils
        self.hand_connections = hand_connections

    def detect(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.model.process(rgb_frame)

        hand_bboxes = []
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                if self.drawing_utils is not None:
                    self.drawing_utils.draw_landmarks(
                        frame, hand_landmarks, self.hand_connections
                    )
                height, width, _ = frame.shape
                landmark_points = [
                    (int(landmark.x * width), int(landmark.y * height))
                    for landmark in hand_landmarks.landmark
                ]
                if landmark_points:
                    landmark_array = np.array(landmark_points)
                    x, y, box_width, box_height = cv2.boundingRect(landmark_array)
                    box = expand_bounding_box(
                        x, y, box_width, box_height, scale=1.2,
                        frame_shape=frame.shape,
                    )
                    hand_bboxes.append(box)
                    x, y, box_width, box_height = box
                    cv2.rectangle(
                        frame, (x, y), (x + box_width, y + box_height),
                        (0, 255, 0), 2,
                    )
        else:
            print("No hands detected by MediaPipe in this frame.")

        return hand_bboxes, frame

def expand_bounding_box(x, y, w, h, scale=1.5, frame_shape=None):
    cx, cy = x + w // 2, y + h // 2
    new_w = int(w * scale)
    new_h = int(h * scale)
    new_x = max(cx - new_w // 2, 0)
    new_y = max(cy - new_h // 2, 0)
    if frame_shape is not None:
        new_w = min(new_w, frame_shape[1] - new_x)
        new_h = min(new_h, frame_shape[0] - new_y)
    return new_x, new_y, new_w, new_h

def detect_hands(frame, detector=None):
    """Detect hands in a BGR frame, using an injected or shared detector."""
    global hands_detector, mp_hands, mp_draw
    if detector is not None:
        return detector.detect(frame)
    if hands_detector is None:
        mp = _load_mediapipe()
        mp_hands = mp.solutions.hands
        mp_draw = mp.solutions.drawing_utils
        hands_detector = HandDetector(
            model=mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.7,
            ),
            drawing_utils=mp_draw,
            hand_connections=mp_hands.HAND_CONNECTIONS,
        )
    return hands_detector.detect(frame)




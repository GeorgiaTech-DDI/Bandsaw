# hand_detection.py 
import cv2 
import numpy as np 
import mediapipe as mp 
 
# Initialize MediaPipe Hands 
mp_hands = mp.solutions.hands 
mp_draw = mp.solutions.drawing_utils 
hands_detector = mp_hands.Hands( 
    static_image_mode=False, 
    max_num_hands=2, 
    min_detection_confidence=0.7, 
    min_tracking_confidence=0.7 
) 
 
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
 
def detect_hands(frame): 
    """ 
    Detects hands in the given frame using MediaPipe. 
    :param frame: BGR frame from the camera. 
    :return: Tuple (hand_bboxes, annotated_frame) where hand_bboxes is a list of  
             bounding boxes [(x, y, w, h), ...] for each detected hand, and  
             annotated_frame is the frame with hand landmarks drawn. 
    """ 
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
    results = hands_detector.process(rgb_frame) 
 
    hand_bboxes = [] 
    if results.multi_hand_landmarks: 
        for hand_landmarks in results.multi_hand_landmarks: 
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS) 
            h, w, _ = frame.shape 
            landmark_points = [] 
            for landmark in hand_landmarks.landmark: 
                x = int(landmark.x * w) 
                y = int(landmark.y * h) 
                landmark_points.append((x, y)) 
            if landmark_points: 
                landmark_array = np.array(landmark_points) 
                x, y, w_box, h_box = cv2.boundingRect(landmark_array) 
                x, y, w_box, h_box = expand_bounding_box(x, y, w_box, h_box, scale=1.2, 
frame_shape=frame.shape) 
                hand_bboxes.append((x, y, w_box, h_box)) 
                cv2.rectangle(frame, (x, y), (x + w_box, y + h_box), (0, 255, 0), 2) 
    else: 
        print("No hands detected by MediaPipe in this frame.") 
 
    return hand_bboxes, frame 

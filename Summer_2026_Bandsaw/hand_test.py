# (Not stable, need modification) Worked code for hand detection    
import cv2
import mediapipe as mp
import numpy as np
from picamera2 import Picamera2

# Initialize MediaPipe hand detection
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.2,  # Lower confidence for better detection
    min_tracking_confidence=0.5    # Lower tracking confidence to improve responsiveness
)

# Initialize the Raspberry Pi Camera
picam2 = Picamera2()
preview_config = picam2.create_preview_configuration()
picam2.configure(preview_config)
picam2.start()

def get_hand_landmarks(frame):
    """Detects hand landmarks and returns their coordinates as a NumPy array."""
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert to RGB for MediaPipe
    result = hands.process(rgb_frame)

    all_points = []
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            points = []
            h, w, _ = frame.shape
            for landmark in hand_landmarks.landmark:
                x, y = int(landmark.x * w), int(landmark.y * h)
                points.append([x, y])
            all_points.append(np.array(points, dtype=np.int32))

    return all_points, result

def expand_convex_hull(points, scale_factor=1.5):
    """Expands the convex hull around the hand to create a larger boundary."""
    if len(points) == 0:
        return None

    hull = cv2.convexHull(points)
    center_x, center_y = np.mean(points, axis=0)

    expanded_hull = []
    for point in hull:
        px, py = point[0]
        new_x = int(center_x + (px - center_x) * scale_factor)
        new_y = int(center_y + (py - center_y) * scale_factor)
        expanded_hull.append([new_x, new_y])

    return np.array(expanded_hull, dtype=np.int32)

try:
    while True:
        # Capture frame from the Raspberry Pi Camera
        frame = picam2.capture_array()
        frame = cv2.flip(frame, 1)  # Mirror the frame

        # Get hand landmarks
        hands_points, result = get_hand_landmarks(frame)

        # Debugging: print if hands are detected
        if result.multi_hand_landmarks:
            print("Hands Detected!")
        else:
            print("No Hands Detected!")

        # Draw expanded convex hull around detected hands
        for points in hands_points:
            expanded_hull = expand_convex_hull(points, scale_factor=1.5)
            if expanded_hull is not None:
                cv2.polylines(frame, [expanded_hull], True, (0, 255, 0), 2)

        # Convert back to BGR for OpenCV display
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Display the frame with hand detection
        cv2.imshow("RPi Hand Detection with Expanded Boundary", frame_bgr)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    picam2.stop()
    cv2.destroyAllWindows()


# import cv2
# import mediapipe as mp
# import numpy as np
# from picamera2 import Picamera2
# 
# # Initialize MediaPipe hand detection
# mp_hands = mp.solutions.hands
# hands = mp_hands.Hands(
#     max_num_hands=2,
#     min_detection_confidence=0.5,  # Lower confidence for detecting closed hands
#     min_tracking_confidence=0.5    # Lower tracking confidence to improve responsiveness
# )
# 
# # Initialize the Raspberry Pi Camera
# picam2 = Picamera2()
# preview_config = picam2.create_preview_configuration()
# picam2.configure(preview_config)
# picam2.start()
# 
# def get_hand_landmarks(frame):
#     """Detects hand landmarks and returns their coordinates as a NumPy array."""
#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert to RGB for MediaPipe
#     result = hands.process(rgb_frame)
# 
#     all_points = []
#     if result.multi_hand_landmarks:
#         for hand_landmarks in result.multi_hand_landmarks:
#             points = []
#             h, w, _ = frame.shape
#             for landmark in hand_landmarks.landmark:
#                 x, y = int(landmark.x * w), int(landmark.y * h)
#                 points.append([x, y])
#             all_points.append(np.array(points, dtype=np.int32))
# 
#     return all_points, result
# 
# def expand_convex_hull(points, scale_factor=1.3):
#     """Expands the convex hull around the hand to create a larger boundary."""
#     if len(points) == 0:
#         return None
# 
#     hull = cv2.convexHull(points)
#     center_x, center_y = np.mean(points, axis=0)
# 
#     expanded_hull = []
#     for point in hull:
#         px, py = point[0]
#         new_x = int(center_x + (px - center_x) * scale_factor)
#         new_y = int(center_y + (py - center_y) * scale_factor)
#         expanded_hull.append([new_x, new_y])
# 
#     return np.array(expanded_hull, dtype=np.int32)
# 
# try:
#     while True:
#         # Capture frame from the Raspberry Pi Camera
#         frame = picam2.capture_array()
#         frame = cv2.flip(frame, 1)  # Mirror the frame
# 
#         # Get hand landmarks
#         hands_points, result = get_hand_landmarks(frame)
# 
#         # Debugging: print if hands are detected
#         if result.multi_hand_landmarks:
#             print("Hands Detected!")
#         else:
#             print("No Hands Detected!")
# 
#         # Draw expanded convex hull around detected hands
#         for points in hands_points:
#             expanded_hull = expand_convex_hull(points, scale_factor=1.3)
#             if expanded_hull is not None:
#                 cv2.polylines(frame, [expanded_hull], True, (0, 255, 0), 2)
# 
#         # Convert back to BGR for OpenCV display
#         frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
# 
#         # Display the frame with hand detection
#         cv2.imshow("RPi Hand Detection with Expanded Boundary", frame_bgr)
# 
#         if cv2.waitKey(1) & 0xFF == ord("q"):
#             break
# 
# finally:
#     picam2.stop()
#     cv2.destroyAllWindows()

    
    
    

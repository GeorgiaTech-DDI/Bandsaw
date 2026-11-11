import cv2
import mediapipe as mp
import numpy as np
from picamera2 import Picamera2

# Initialize MediaPipe hand detection
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.3,  # Lower detection confidence for better detection with closed hands
    min_tracking_confidence=0.5    # Slightly lower tracking confidence for more stability
)

# Initialize the Raspberry Pi Camera
picam2 = Picamera2()
preview_config = picam2.create_preview_configuration()
picam2.configure(preview_config)
picam2.start()

# Square size factor (1/10th of the frame)
SQUARE_SIZE_FACTOR = 0.1

def get_hand_landmarks(frame):
    """Detects hand landmarks and returns their coordinates as a NumPy array."""
    # Convert frame to grayscale to potentially help detection in different lighting
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Convert to RGB for MediaPipe (since it expects RGB input)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  
    
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

def expand_convex_hull(points, scale_factor=1.3):
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

def is_hand_in_square(hand_points, square_coords):
    """Checks if any of the hand points overlap with the square's boundaries."""
    x1, y1, x2, y2 = square_coords
    for point in hand_points:
        x, y = point
        if x1 <= x <= x2 and y1 <= y <= y2:
            return True
    return False

try:
    while True:
        # Capture frame from the Raspberry Pi Camera
        frame = picam2.capture_array()
        frame = cv2.flip(frame, 1)  # Mirror the frame

        # Get the frame dimensions
        h, w, _ = frame.shape

        # Define the square in the center of the frame (1/10th of the frame size)
        square_size = int(min(h, w) * SQUARE_SIZE_FACTOR)
        square_x1 = (w - square_size) // 2
        square_y1 = (h - square_size) // 2
        square_x2 = square_x1 + square_size
        square_y2 = square_y1 + square_size

        # Draw the square in the middle
        cv2.rectangle(frame, (square_x1, square_y1), (square_x2, square_y2), (0, 0, 255), 2)

        # Get hand landmarks
        hands_points, result = get_hand_landmarks(frame)

        # Debugging: print if hands are detected
        if result.multi_hand_landmarks:
            print("Hands Detected!")
        else:
            print("No Hands Detected!")

        # Check if any hand overlaps with the square and print "Too close!" if true
        for points in hands_points:
            if is_hand_in_square(points, (square_x1, square_y1, square_x2, square_y2)):
                print("Too close!")

        # Draw expanded convex hull around detected hands
        for points in hands_points:
            expanded_hull = expand_convex_hull(points, scale_factor=1.3)
            if expanded_hull is not None:
                cv2.polylines(frame, [expanded_hull], True, (0, 255, 0), 2)

        # Convert back to BGR for OpenCV display
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Display the frame with hand detection
        cv2.imshow("RPi Hand Detection with Square", frame_bgr)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    picam2.stop()
    cv2.destroyAllWindows()


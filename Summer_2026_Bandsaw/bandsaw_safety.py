# bandsaw_safety.py

import cv2          # OpenCV for capturing video and processing images.
import numpy as np  # NumPy for numerical operations on arrays.
import time         # For creating delays (used in alert simulation).
import threading    # For running alert triggers without blocking the main loop.

######################################
# Video Capture Module Functions
######################################

def open_video_source(source=0):
    """
    Opens the video source.
    :param source: Specifies the video source (0 for default webcam).
    :return: An OpenCV VideoCapture object.
    """
    cap = cv2.VideoCapture(source)  # Open the default webcam.
    if not cap.isOpened():
        print("Error: Unable to open video source.")
    return cap

def get_frame(cap):
    """
    Reads a frame from the video source.
    :param cap: The VideoCapture object.
    :return: A tuple (ret, frame) where ret is True if a frame was successfully read.
    """
    ret, frame = cap.read()  # Read one frame from the video feed.
    return ret, frame

def release_video(cap):
    """
    Releases the video source and closes all OpenCV windows.
    :param cap: The VideoCapture object.
    """
    cap.release()               # Release the camera.
    cv2.destroyAllWindows()     # Close any OpenCV windows.

######################################
# Hand Detection Module Function
######################################

def detect_hand(frame):
    """
    Detects a hand in the frame using skin-color segmentation.
    :param frame: The current video frame.
    :return: A tuple (hand_bbox, mask) where hand_bbox is (x, y, w, h) if a hand is detected, otherwise None,
             and mask is the binary image after thresholding.
    """
    # Convert the frame from BGR (default color space) to HSV for better color segmentation.
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Define HSV thresholds for skin color. You may need to adjust these values based on lighting.
    lower_skin = np.array([0, 40, 80], dtype=np.uint8)
    upper_skin = np.array([20, 180, 255], dtype=np.uint8)
    
    # Create a binary mask: pixels within the skin range are white (255), others black (0).
    mask = cv2.inRange(hsv, lower_skin, upper_skin)
    
    # Use morphological operations to remove noise from the mask.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.erode(mask, kernel, iterations=2)
    mask = cv2.dilate(mask, kernel, iterations=2)
    
    # Find contours in the binary mask.
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    hand_bbox = None  # This will store the bounding box of the detected hand.
    max_area = 0      # Track the largest contour area found.
    
    # Loop over each contour.
    for cnt in contours:
        area = cv2.contourArea(cnt)  # Compute area of the contour.
        # If the area is large enough (threshold lowered to 3000) and is the largest seen so far:
        if area > 3000 and area > max_area:
            #max_area = 
            max_area = 100000
            hand_bbox = cv2.boundingRect(cnt)  # Get the bounding box (x, y, w, h).
    
    # Debug print to show detection details.
    if hand_bbox:
        print("Detected hand bbox:", hand_bbox, "with area:", max_area)
    else:
        print("No hand detected in this frame.")
    
    return hand_bbox, mask

######################################
# Alert System Module Functions (Simulated)
######################################

class SimulatedGPIO:
    """
    A simple class to simulate Raspberry Pi GPIO functionality.
    """
    def __init__(self):
        self.pins = {}  # Dictionary to store pin states.
    
    def setup(self, pin, mode):
        """
        Simulates setting up a GPIO pin.
        :param pin: Pin number.
        :param mode: Mode of the pin (e.g., "OUT").
        """
        self.pins[pin] = 0  # Initialize the pin to LOW.
        print(f"Pin {pin} set up as {mode}.")
    
    def output(self, pin, state):
        """
        Simulates writing a value (HIGH/LOW) to a GPIO pin.
        :param pin: Pin number.
        :param state: 1 for HIGH, 0 for LOW.
        """
        self.pins[pin] = state
        print(f"Pin {pin} set to {'HIGH' if state else 'LOW'}.")
    
    def cleanup(self):
        """
        Cleans up all simulated GPIO pins.
        """
        self.pins = {}
        print("GPIO cleanup done.")

# Create an instance of the simulated GPIO.
GPIO = SimulatedGPIO()
LED_PIN = 18      # Simulated pin for LED.
BUZZER_PIN = 23   # Simulated pin for buzzer.

def initialize_alerts():
    """
    Initializes the simulated GPIO pins for the alert system.
    """
    GPIO.setup(LED_PIN, "OUT")
    GPIO.setup(BUZZER_PIN, "OUT")

def trigger_alert():
    """
    Simulates triggering an alert by turning on an LED and a buzzer for 1 second.
    This function runs in a separate thread to avoid blocking the main video loop.
    """
    GPIO.output(LED_PIN, 1)
    GPIO.output(BUZZER_PIN, 1)
    print("Alert triggered!")
    time.sleep(1)  # Alert is active for 1 second.
    GPIO.output(LED_PIN, 0)
    GPIO.output(BUZZER_PIN, 0)
    print("Alert cleared!")

######################################
# Boundary Check Function
######################################

def check_hand_near_boundary(hand_bbox, boundary_box, margin=20):
    """
    Checks whether the hand's bounding box intersects with or is near the boundary box.
    :param hand_bbox: Tuple (x, y, w, h) for the detected hand.
    :param boundary_box: Tuple (bx, by, bw, bh) defining the danger zone.
    :param margin: Additional pixels to expand the boundary for early warning.
    :return: True if the hand is within the expanded boundary; False otherwise.
    """
    if hand_bbox is None:
        return False
    
    # Unpack the hand bounding box.
    hx, hy, hw, hh = hand_bbox
    # Unpack the boundary box.
    bx, by, bw, bh = boundary_box
    
    # Expand the boundary box by the margin on all sides.
    expanded_box = (bx - margin, by - margin, bw + 2 * margin, bh + 2 * margin)
    ex, ey, ew, eh = expanded_box
    
    # Check for intersection between the hand box and the expanded boundary.
    if (hx < ex + ew and hx + hw > ex and
        hy < ey + eh and hy + hh > ey):
        return True
    return False

######################################
# Main Application
######################################

def main():
    # Open the live camera feed (0 indicates the default webcam).
    cap = open_video_source(0)
    if not cap or not cap.isOpened():
        return
    
    # Initialize the alert system (simulate setting up GPIO pins).
    initialize_alerts()
    
    # Read one test frame to determine the frame dimensions.
    ret, test_frame = get_frame(cap)
    if not ret:
        print("Error: Unable to read a frame from the camera.")
        return
    height, width, _ = test_frame.shape
    
    # Define the boundary box (representing the bandsaw blade) near the bottom-center.
    boundary_width = 200    # Width of the boundary box.
    boundary_height = 50    # Height of the boundary box.
    bx = width // 2 - boundary_width // 2
    by = height - 150       # Adjust this value based on your setup.
    boundary_box = (bx, by, boundary_width, boundary_height)
    
    # Variables to prevent continuous alerts.
    last_alert_time = 0
    alert_interval = 2  # In seconds.
    
    # Main loop: process each frame.
    while True:
        ret, frame = get_frame(cap)
        if not ret:
            break
        
        # Detect hand and obtain the binary mask.
        hand_bbox, mask = detect_hand(frame)
        
        # Draw the predefined boundary box in blue (visible and thick).
        cv2.rectangle(frame, (bx, by), (bx + boundary_width, by + boundary_height),
                      (255, 0, 0), 3)
        
        # If a hand is detected...
        if hand_bbox:
            x, y, w, h = hand_bbox
            # Check if the hand is crossing the boundary (with a margin).
            if check_hand_near_boundary(hand_bbox, boundary_box):
                # If true, use red for the hand's bounding box.
                box_color = (0, 0, 255)
                cv2.putText(frame, "ALERT: Hand Too Close!", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, box_color, 2)
                current_time = time.time()
                # Trigger the alert if enough time has passed since the last alert.
                if current_time - last_alert_time > alert_interval:
                    threading.Thread(target=trigger_alert).start()
                    last_alert_time = current_time
            else:
                # If not near, use green for the hand's bounding box.
                box_color = (0, 255, 0)
            # Draw the hand's bounding box with a thick line.
            cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 3)
        
        # Display the live video feed with overlays.
        cv2.imshow("Bandsaw Safety System", frame)
        # Also display the hand detection mask for debugging purposes.
        cv2.imshow("Hand Mask", mask)
        
        # Exit the loop if 'q' is pressed.
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Release the video source and close all windows.
    release_video(cap)

if __name__ == "__main__":
    main()

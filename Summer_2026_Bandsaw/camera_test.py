######################################
# Worked code in virtual environment to open up camera (myenv)
######################################
import cv2
from picamera2 import Picamera2

# Initialize the camera
picam2 = Picamera2()

# Configure the camera for preview
preview_config = picam2.create_preview_configuration()
picam2.configure(preview_config)

# Start the camera
picam2.start()

try:
    while True:
        # Capture a frame from the camera
        frame = picam2.capture_array()

        # Convert the frame from BGR to RGB (OpenCV uses BGR by default)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Display the frame in a window
        cv2.imshow("Raspberry Pi Camera", frame_rgb)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Stop the camera and close the OpenCV window
    picam2.stop()
    cv2.destroyAllWindows()

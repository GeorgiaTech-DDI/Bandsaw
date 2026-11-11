import board
import neopixel_spi
import cv2
import numpy as np

# Configuration
NUM_PIXELS = 8  # Adjust to your strip length
BRIGHTNESS = 0.5

# Initialize NeoPixel strip using SPI (GPIO10 MOSI / Pin 19)
pixels = neopixel_spi.NeoPixel_SPI(board.SPI(), NUM_PIXELS, brightness=BRIGHTNESS, auto_write=True)

# Create a dummy window just for capturing keypress
blank = np.zeros((200, 400, 3), dtype = np.uint8)

print("Press 'r', 'g', 'b', 'o', 'f' to control NeoPixels. Press 'q' to quit.")

try:
    while True:
        cv2.imshow("NeoPixel Control", blank)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('r'):
            pixels.fill((255, 0, 0))
            print("Red")
        elif key == ord('g'):
            pixels.fill((0, 255, 0))
            print("Green")
        elif key == ord('b'):
            pixels.fill((0, 0, 255))
            print("Blue")
        elif key == ord('o'):
            pixels.fill((255, 255, 255))
            print("White (On)")
        elif key == ord('f'):
            pixels.fill((0, 0, 0))
            print("Off")

finally:
    # Always turn off NeoPixels on exit
    pixels.fill((0, 0, 0))
    cv2.destroyAllWindows()
    print("NeoPixel control ended.")



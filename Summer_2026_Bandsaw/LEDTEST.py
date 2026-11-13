import board
import neopixel

# Initialize with 30% brightness
pixels = neopixel.NeoPixel(board.D18, 30, brightness=0.2, auto_write=False)

pixels.fill((255, 0, 0))  # Set all pixels to red
pixels.show()

# Change brightness dynamically later in the script
pixels.brightness = 0.8
pixels.show()
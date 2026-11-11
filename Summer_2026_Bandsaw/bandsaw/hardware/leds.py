"""Pi5Neo LED adapter with lazy hardware initialization."""

import time

# Configuration
NUM_LEDS = 144
SPI_DEVICE = '/dev/spidev0.0'
SPI_SPEED = 800
BRIGHTNESS = 0.2

neo = None


def _get_strip():
    global neo
    if neo is None:
        try:
            from pi5neo import Pi5Neo
        except ImportError as error:
            raise RuntimeError("LED control requires pi5neo on Raspberry Pi") from error
        neo = Pi5Neo(SPI_DEVICE, NUM_LEDS, SPI_SPEED)
    return neo

def set_led_color(r, g, b, count=NUM_LEDS, brightness=BRIGHTNESS):
    """
    Set all or part of the LED strip to a specific color.
    """
    r = int(r * brightness)
    g = int(g * brightness)
    b = int(b * brightness)
    strip = _get_strip()
    for i in range(count):
        strip.set_led_color(i, r, g, b)
    strip.update_strip()

def solid_white():
    # Bandsaw active, no hand
    set_led_color(255, 255, 255)

def solid_yellow():
    # Slit calibration in progress
    set_led_color(255, 255, 0)

def show_calibration_direction(direction):
    """Show the camera movement direction on a horizontally mounted strip."""
    if direction not in ("left", "right", "center"):
        direction = "unknown"

    blink_on = int(time.monotonic() * 2) % 2 == 0
    half = NUM_LEDS // 2
    yellow = int(255 * BRIGHTNESS)

    strip = _get_strip()
    for index in range(NUM_LEDS):
        if direction == "left":
            lit = index < half
        elif direction == "right":
            lit = index >= half
        elif direction == "center":
            lit = True
        else:
            lit = blink_on
        color = (yellow, yellow, 0) if lit else (0, 0, 0)
        strip.set_led_color(index, *color)
    strip.update_strip()

def solid_green():
    # Hand detected, not near slit
    set_led_color(0, 255, 0)

def solid_red():
    # Hand near slit
    set_led_color(255, 0, 0)

def turn_off_leds():
    set_led_color(0, 0, 0)

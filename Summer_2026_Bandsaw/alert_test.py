import time
from strip_test import (
    show_bandsaw_active_no_hands,
    show_hands_detected_not_near_slit,
    show_hand_near_slit,
    turn_off_leds
)

def run_led_test():
    print("Testing: Bandsaw active, no hands (WHITE)")
    show_bandsaw_active_no_hands()
    time.sleep(2)

    print("Testing: Hands detected, not near slit (GREEN)")
    show_hands_detected_not_near_slit()
    time.sleep(2)

    print("Testing: Hand overlapping slit (RED)")
    show_hand_near_slit()
    time.sleep(2)

    print("Testing: Turn off all LEDs")
    turn_off_leds()
    time.sleep(1)

if __name__ == "__main__":
    run_led_test()

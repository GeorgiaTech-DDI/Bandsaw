import gpiod
import time
import cv2
import numpy as np

LED_PIN = 9

chip = gpiod.Chip('gpiochip4')
led_line = chip.get_line(LED_PIN)
led_line.request(consumer='LED', type=gpiod.LINE_REQ_DIR_OUT)

blank = np.zeros((200,400,3),dtype=np.uint8)

try:
    while True:
        cv2.imshow("LED control", blank)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('f'):
            led_line.set_value(1)
            print("Turning on LED")
        elif key == ord('o'):
            led_line.set_value(0)
            print("Turning off LED")


except KeyboardInterrupt:
    led_line.release()
    chip.close()



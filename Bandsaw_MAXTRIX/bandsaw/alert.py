# alert.py 
import time 
import threading 
import board 
import neopixel_spi 
 
NUM_PIXELS = 30 
pixels = neopixel_spi.NeoPixel_SPI(board.SPI(), NUM_PIXELS, brightness=0.5, auto_write=True) 
 
_alert_active = False 
_alert_thread = None 
_lock = threading.Lock() 
 
def _blink_loop(color=(255, 0, 0), interval=0.3): 
    while True: 
        with _lock: 
            if not _alert_active: 
                pixels.fill((0, 0, 0)) 
                break 
        pixels.fill(color) 
        time.sleep(interval) 
        pixels.fill((0, 0, 0)) 
        time.sleep(interval) 
 
def start_alert(color=(255, 0, 0)): 
    global _alert_active, _alert_thread 
    with _lock: 
        if not _alert_active: 
            _alert_active = True 
            _alert_thread = threading.Thread(target=_blink_loop, args=(color,), daemon=True) 
            _alert_thread.start() 
 
def stop_alert(): 
    global _alert_active 
    with _lock: 
        _alert_active = False 
 
def clear_alert(): 
    pixels.fill((0, 0, 0))

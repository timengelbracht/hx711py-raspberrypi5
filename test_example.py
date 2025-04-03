from hx711 import HX711
import time
import gpiod

#plug in the physical pins used on the rpi5
# if u use other phsical pins, just go to hx711.py and add the mapping to the dictionary at top of file :)
dout = 29   # GPIO5 (Pin 29)
sck = 31    # GPIO6 (Pin 31)
chip = gpiod.Chip("gpiochip4") #default for rpi5
hx = HX711(dout, sck, chip=chip)
hx.set_reference_unit(20938)  # use your calibration, loadcell specific
hx.tare()

while True:
    weight = hx.get_weight(3)
    print(f"Weight: {weight:.3f}")
    time.sleep(0.2)

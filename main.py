from machine import Pin
from time import sleep

pin = Pin("LED", Pin.OUT)

print("LED starts flashing...")
while True:
    try:
        pin.toggle()
        sleep(0.5) # sleep 0.5 sec
    except KeyboardInterrupt:
        break
pin.off()
print("Finished.")     

from machine import Pin
from time import sleep

led = Pin("LED", Pin.OUT)
button = Pin(15, Pin.IN, Pin.PULL_UP)  # Button on GP15 (Pin 20)

# Startup indicator - 3 quick flashes to show code is loaded
print("Starting up...")
for _ in range(3):
    led.on()
    sleep(0.15)
    led.off()
    sleep(0.15)
sleep(0.5)

# Track state
running = False
last_button_state = 1

print("Button control ready!")
print("Press button to start/stop LED")

try:
    while True:
        # Read button (0 = pressed, 1 = not pressed due to PULL_UP)
        button_state = button.value()
        
        # Detect button press (transition from 1 to 0)
        if last_button_state == 1 and button_state == 0:
            running = not running  # Toggle state
            if running:
                print("LED started")
            else:
                print("LED stopped")
                led.off()
            sleep(0.3)  # Debounce delay
        
        last_button_state = button_state
        
        # Run LED if active
        if running:
            led.toggle()
            sleep(0.1)  # 5Hz fast blink
        else:
            sleep(0.01)  # Quick check for button press
            
except KeyboardInterrupt:
    led.off()
    print("Script stopped.")     

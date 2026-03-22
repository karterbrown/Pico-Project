from machine import Pin, UART  # type: ignore
from neopixel import NeoPixel  # type: ignore
from time import sleep, ticks_ms, ticks_diff

# Boot delay - gives MicroPico/REPL time to connect and interrupt before the loop starts
sleep(3)

# Onboard LED solid ON = Pico is powered and running
onboard = Pin("LED", Pin.OUT)
onboard.on()

# 5 WS2812B strips, 20 LEDs each on GP0-GP4
NUM_LEDS = 20
strips = [NeoPixel(Pin(i), NUM_LEDS) for i in range(5)]

# ---- SV5W Audio Player Setup ----
# UART1: GP8 TX → SV5W IO1/RXD, GP9 RX ← SV5W IO0/TXD
# Note: GP6/GP7 are CTS/RTS on RP2040 - not valid for UART TX/RX
uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
busy = Pin(5, Pin.IN)  # LOW = playing, HIGH = idle

def sv5w_cmd(cmd, msb=0, lsb=0):
    """Send a command to the SV5W in DFPlayer-style protocol."""
    msg = bytes([0x7E, 0xFF, 0x06, cmd, 0x00, msb, lsb, 0xEF])
    uart.write(msg)
    sleep(0.05)

def player_play():
    sv5w_cmd(0x0D)
    print("[AUDIO] Play / Resume")

def player_pause():
    sv5w_cmd(0x0E)
    print("[AUDIO] Pause")

def player_next():
    sv5w_cmd(0x01)
    print("[AUDIO] Next track")

def player_prev():
    sv5w_cmd(0x02)
    print("[AUDIO] Previous track")

def player_random():
    sv5w_cmd(0x18)
    print("[AUDIO] Random track")

def player_vol_up():
    sv5w_cmd(0x04)
    print("[AUDIO] Volume Up")

def player_vol_down():
    sv5w_cmd(0x05)
    print("[AUDIO] Volume Down")

def player_set_vol(level):
    sv5w_cmd(0x06, 0x00, max(0, min(30, level)))
    print("[AUDIO] Volume set to", level)

# ---- Button Setup (GP16-GP21, active LOW with PULL_UP) ----
BUTTONS = {
    "Random":   Pin(16, Pin.IN, Pin.PULL_UP),
    "Next":     Pin(17, Pin.IN, Pin.PULL_UP),
    "Previous": Pin(18, Pin.IN, Pin.PULL_UP),
    "Pause":    Pin(19, Pin.IN, Pin.PULL_UP),
    "Vol Up":   Pin(20, Pin.IN, Pin.PULL_UP),
    "Vol Down": Pin(21, Pin.IN, Pin.PULL_UP),
}
BUTTON_ACTIONS = {
    "Random":   player_random,
    "Next":     player_next,
    "Previous": player_prev,
    "Pause":    player_pause,
    "Vol Up":   player_vol_up,
    "Vol Down": player_vol_down,
}
_last_press = {name: 0 for name in BUTTONS}
DEBOUNCE_MS = 300

def check_buttons():
    """Check all buttons and fire their action on press. Call inside LED loops."""
    now = ticks_ms()
    for name, pin in BUTTONS.items():
        if pin.value() == 0 and ticks_diff(now, _last_press[name]) > DEBOUNCE_MS:
            _last_press[name] = now
            print(f"[BTN] {name} pressed")
            BUTTON_ACTIONS[name]()

# Each strip gets its own chase color so all LEDs and all colors are tested
STRIP_COLORS = [
    (40, 0,  0),   # GP0 - Red
    (0,  40, 0),   # GP1 - Green
    (0,  0,  40),  # GP2 - Blue
    (40, 20, 0),   # GP3 - Orange
    (20, 0,  40),  # GP4 - Purple
]

def clear_all():
    for s in strips:
        s.fill((0, 0, 0))
        s.write()

def chase_all_forward(delay=0.04):
    for i in range(NUM_LEDS):
        for si, s in enumerate(strips):
            s.fill((0, 0, 0))
            s[i] = STRIP_COLORS[si]
            s.write()
        check_buttons()
        sleep(delay)

def chase_all_reverse(delay=0.04):
    for i in range(NUM_LEDS - 1, -1, -1):
        for si, s in enumerate(strips):
            s.fill((0, 0, 0))
            s[i] = STRIP_COLORS[si]
            s.write()
        check_buttons()
        sleep(delay)

def chase_trail(delay=0.04, trail=5):
    for i in range(NUM_LEDS + trail):
        for si, s in enumerate(strips):
            s.fill((0, 0, 0))
            r, g, b = STRIP_COLORS[si]
            for t in range(trail):
                pos = i - t
                if 0 <= pos < NUM_LEDS:
                    fade = (trail - t) / trail
                    s[pos] = (int(r * fade), int(g * fade), int(b * fade))
            s.write()
        check_buttons()
        sleep(delay)

def chase_bounce(delay=0.04, trail=4):
    for i in list(range(NUM_LEDS)) + list(range(NUM_LEDS - 1, -1, -1)):
        for si, s in enumerate(strips):
            s.fill((0, 0, 0))
            r, g, b = STRIP_COLORS[si]
            s[i] = (r, g, b)
            s.write()
        check_buttons()
        sleep(delay)

def chase_rotating_colors(delay=0.04):
    for offset in range(5):
        for i in range(NUM_LEDS):
            for si, s in enumerate(strips):
                s.fill((0, 0, 0))
                s[i] = STRIP_COLORS[(si + offset) % 5]
                s.write()
            check_buttons()
            sleep(delay)

# ---- Startup ----
print("Chase + Audio Test Ready")
print("GP16=Random  GP17=Next  GP18=Prev  GP19=Pause  GP20=Vol+  GP21=Vol-")

# Set initial volume to mid-level and start playing
player_set_vol(20)
sleep(0.2)
player_random()  # Start a random track on boot

cycle = 0
try:
    while True:
        cycle += 1
        print(f"--- Cycle {cycle} ---")

        print("Forward chase")
        chase_all_forward(0.04)
        clear_all()

        print("Reverse chase")
        chase_all_reverse(0.04)
        clear_all()

        print("Trail chase")
        chase_trail(0.035, trail=6)
        clear_all()

        print("Bounce chase")
        chase_bounce(0.04)
        clear_all()

        print("Rotating colors chase")
        chase_rotating_colors(0.03)
        clear_all()
        sleep(0.3)

except KeyboardInterrupt:
    clear_all()
    player_pause()
    onboard.off()
    print("Stopped.")

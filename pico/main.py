from machine import Pin, UART  # type: ignore
from neopixel import NeoPixel  # type: ignore
from time import sleep, ticks_ms, ticks_diff
import math
import sys
import struct

# Effect index list — must match tools/lights_tool.py EFFECTS order
EFFECTS = ["strobe", "flash", "pulse", "fade", "hold", "wave"]
RECORD_SIZE = 12  # bytes: uint32 time_ms + uint8 strip + uint8 brightness + uint8 effect_idx + uint8 led_pos + uint32 duration_ms

# Strip colors — rotate across strips over time
STRIP_COLORS = [
    (0, 200, 255),   # Electric blue
    (0, 60, 255),    # Blue
    (148, 0, 211),   # Purple
    (255, 200, 0),   # Yellow
    (0, 200, 50),    # Green
]
COLOR_ROTATE_MS = 10000  # Shift color assignment every 10 seconds

# Boot delay - gives MicroPico/REPL time to connect and interrupt before the loop starts
sleep(3)

# Onboard LED solid ON = Pico is powered and running
onboard = Pin("LED", Pin.OUT)
onboard.on()

# 5 WS2812B strips, 20 LEDs each
# Using GP0, GP1, GP2, GP3, GP4 for LED strips
NUM_LEDS = 20
strips = [NeoPixel(Pin(i), NUM_LEDS) for i in range(5)]

# ---- SV5W Audio Player Setup ----
# UART0: GP16 TX → SV5W IO0/RXD, GP17 RX ← SV5W IO1/TXD
uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
busy = Pin(5, Pin.IN)  # LOW = playing, HIGH = idle

# Track current playing song
current_song_number = None
_last_query_time = 0
QUERY_INTERVAL_MS = 500  # Query current track every 500ms

def sv5w_cmd(cmd, msb=0, lsb=0):
    """Send a command to the SV5W in DFPlayer-style protocol."""
    # Checksum includes VER byte: -(VER + LEN + CMD + Feedback + Para1 + Para2)
    checksum = (-(0xFF + 0x06 + cmd + 0x00 + msb + lsb)) & 0xFFFF
    chk_h = (checksum >> 8) & 0xFF
    chk_l = checksum & 0xFF
    msg = bytes([0x7E, 0xFF, 0x06, cmd, 0x00, msb, lsb, chk_h, chk_l, 0xEF])
    uart.write(msg)
    sleep(0.1)

def query_current_track():
    """Query the current playing track number from SV5W."""
    sv5w_cmd(0x4C)  # Query current file in TF card

def parse_uart_response():
    """Parse responses from SV5W player."""
    if uart.any():
        try:
            # Read available bytes
            data = uart.read()
            if data and len(data) >= 8:
                # DFPlayer response format: 0x7E FF 06 [CMD] [FeedBack] [ParaH] [ParaL] 0xEF
                if data[0] == 0x7E and data[1] == 0xFF and len(data) >= 10:
                    cmd = data[3]
                    para_h = data[5]
                    para_l = data[6]
                    
                    # Response to query current track (0x4C)
                    if cmd == 0x4C:
                        track_num = (para_h << 8) | para_l
                        return track_num
        except:
            pass
    return None

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

# ---- Button Setup (GP18-GP22 + GP26, active LOW with PULL_UP) ----
BUTTONS = {
    "Random":   Pin(18, Pin.IN, Pin.PULL_UP),
    "Next":     Pin(19, Pin.IN, Pin.PULL_UP),
    "Previous": Pin(20, Pin.IN, Pin.PULL_UP),
    "Pause":    Pin(21, Pin.IN, Pin.PULL_UP),
    "Vol Up":   Pin(22, Pin.IN, Pin.PULL_UP),
    "Vol Down": Pin(26, Pin.IN, Pin.PULL_UP),
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


# =====================================================================
# LIGHTING EVENT PLAYBACK ENGINE
# =====================================================================

class StripState:
    """Track the state of a single LED strip's current effect"""
    def __init__(self):
        self.effect = None
        self.brightness = 0
        self.color = (255, 255, 255)
        self.led_pos = 255  # 255 = whole strip, 0-19 = specific LED
        self.start_time = 0
        self.duration = 0
        self.active = False

    def start_effect(self, effect, brightness, duration, current_time, color=(255, 255, 255), led_pos=255):
        """Start a new effect on this strip"""
        self.effect = effect
        self.brightness = brightness
        self.color = color
        self.led_pos = led_pos
        self.start_time = current_time
        self.duration = duration
        self.active = True
    
    def update(self, strip, current_time):
        """Update strip LEDs based on current effect state"""
        if not self.active:
            return
        
        elapsed = ticks_diff(current_time, self.start_time)
        
        # Check if effect is done
        if elapsed >= self.duration:
            self.active = False
            strip.fill((0, 0, 0))
            strip.write()
            return
        
        # Calculate progress (0.0 to 1.0)
        progress = elapsed / self.duration if self.duration > 0 else 1.0
        
        # Apply effect
        if self.effect == "strobe":
            self._effect_strobe(strip, elapsed)
        elif self.effect == "flash":
            self._effect_flash(strip, progress)
        elif self.effect == "pulse":
            self._effect_pulse(strip, progress)
        elif self.effect == "fade":
            self._effect_fade(strip, progress)
        elif self.effect == "hold":
            self._effect_hold(strip, progress)
        elif self.effect == "wave":
            self._effect_wave(strip, current_time, elapsed)
        else:
            # Default to flash
            self._effect_flash(strip, progress)
        
        strip.write()
    
    def _scale_color(self, factor):
        """Scale strip color by factor (0.0-1.0) and event brightness"""
        r, g, b = self.color
        f = factor * (self.brightness / 255.0)
        return (int(r * f), int(g * f), int(b * f))

    def _set_leds(self, strip, color):
        """Light specific LED(s) based on led_pos. 255 = fill whole strip."""
        if self.led_pos == 255:
            strip.fill(color)
        else:
            strip.fill((0, 0, 0))
            # Light target LED plus soft neighbors for a natural look
            for offset in range(-2, 3):
                idx = self.led_pos + offset
                if 0 <= idx < NUM_LEDS:
                    fade = 1.0 if offset == 0 else (0.4 if abs(offset) == 1 else 0.1)
                    r, g, b = color
                    strip[idx] = (int(r * fade), int(g * fade), int(b * fade))

    def _effect_strobe(self, strip, elapsed):
        """Rapid on/off — hard cut between full color and black"""
        if (elapsed // 40) % 2 == 0:
            self._set_leds(strip, self._scale_color(1.0))
        else:
            strip.fill((0, 0, 0))

    def _effect_flash(self, strip, progress):
        """Instant peak then sharp decay"""
        fade = max(0, 1.0 - (progress ** 0.5))
        self._set_leds(strip, self._scale_color(fade))

    def _effect_pulse(self, strip, progress):
        """Smooth sine wave in and out"""
        pulse = math.sin(progress * math.pi)
        self._set_leds(strip, self._scale_color(pulse))

    def _effect_fade(self, strip, progress):
        """Linear fade out from full brightness"""
        self._set_leds(strip, self._scale_color(1.0 - progress))

    def _effect_hold(self, strip, progress):
        """Hold at full brightness, then quick fade at the end"""
        if progress < 0.75:
            self._set_leds(strip, self._scale_color(1.0))
        else:
            fade = (1.0 - progress) / 0.25
            self._set_leds(strip, self._scale_color(fade))

    def _effect_wave(self, strip, current_time, elapsed):
        """Color wave chasing across the strip"""
        wave_speed = 0.15
        # Anchor wave around led_pos if set, else free-running
        center = self.led_pos if self.led_pos != 255 else (elapsed * wave_speed) % NUM_LEDS
        wave_pos = (center + elapsed * wave_speed) % NUM_LEDS
        strip.fill((0, 0, 0))
        for i in range(NUM_LEDS):
            dist = abs(i - wave_pos)
            if dist > NUM_LEDS / 2:
                dist = NUM_LEDS - dist
            brightness_factor = max(0, 1.0 - (dist / 4.0))
            strip[i] = self._scale_color(brightness_factor)


class LightingPlayer:
    """Manages playback of lighting events streamed from binary file"""
    def __init__(self, strips):
        self.strips = strips
        self.strip_states = [StripState() for _ in range(len(strips))]
        self._file = None
        self._next_event = None
        self.playing = False
        self.start_time = 0

    def open_file(self, filename):
        """Open a binary events file for streaming playback"""
        if self._file:
            self._file.close()
            self._file = None
        try:
            self._file = open(filename, 'rb')
            self._next_event = self._read_next()
            import os as _os
            count = _os.stat(filename)[6] // RECORD_SIZE
            print(f"[LIGHT] Opened {filename} ({count} events)")
            return True
        except Exception as e:
            print(f"[LIGHT] Error opening {filename}: {e}")
            return False

    def _read_next(self):
        """Read the next event record from the binary file"""
        if not self._file:
            return None
        data = self._file.read(RECORD_SIZE)
        if len(data) < RECORD_SIZE:
            return None
        time_ms, strip_index, brightness, effect_idx, led_pos, duration_ms = struct.unpack('<IBBBBI', data)
        effect = EFFECTS[effect_idx] if effect_idx < len(EFFECTS) else "flash"
        return (time_ms, strip_index, brightness, effect, duration_ms, led_pos)

    def start(self):
        """Start playback from beginning"""
        if self.playing:
            print("[LIGHT] Already playing")
            return
        if not self._file:
            print("[LIGHT] No events file loaded")
            return
        self._file.seek(0)
        self._next_event = self._read_next()
        self.playing = True
        self.start_time = ticks_ms()
        print("[LIGHT] Playback started")
        for strip in self.strips:
            strip.fill((0, 0, 0))
            strip.write()

    def stop(self):
        """Stop playback"""
        self.playing = False
        if self._file:
            self._file.seek(0)
            self._next_event = self._read_next()
        for strip in self.strips:
            strip.fill((0, 0, 0))
            strip.write()
        print("[LIGHT] Playback stopped")

    def update(self):
        """Update all strips - call this in main loop"""
        if not self.playing:
            return

        current_time = ticks_ms()
        playback_time = ticks_diff(current_time, self.start_time)

        # Rotate color assignment across strips over time
        color_offset = (playback_time // COLOR_ROTATE_MS) % len(STRIP_COLORS)

        # Process any events that should trigger now
        while self._next_event is not None:
            event_time, strip_index, brightness, effect, duration, led_pos = self._next_event
            if event_time <= playback_time:
                if 0 <= strip_index < len(self.strip_states):
                    color = STRIP_COLORS[(strip_index + color_offset) % len(STRIP_COLORS)]
                    self.strip_states[strip_index].start_effect(
                        effect, brightness, duration, current_time, color, led_pos
                    )
                self._next_event = self._read_next()
            else:
                break

        # Update all active effects
        for i, state in enumerate(self.strip_states):
            if state.active:
                state.update(self.strips[i], current_time)

        # Check if playback is complete
        if self._next_event is None:
            if not any(state.active for state in self.strip_states):
                print("[LIGHT] Playback complete")
                self.playing = False


# Create lighting player
player = LightingPlayer(strips)

# Load song mapping configuration
try:
    from song_config import get_events_for_song  # type: ignore
    print("[CONFIG] Song mapping loaded")
except ImportError:
    print("[CONFIG] No song_config.py found - using default events")
    def get_events_for_song(song_number):
        return "events"


def load_events_for_song(song_number):
    """
    Open binary events file and start playback for the given song number.
    Binary files are named <number>.bin (e.g. 00001.bin).
    """
    event_module_name = get_events_for_song(song_number)

    if event_module_name is None:
        print(f"[LIGHT] Song {song_number}: No lights configured")
        player.stop()
        return False

    # Derive binary filename: "00001_events" → "00001.bin"
    bin_filename = event_module_name.replace('_events', '') + '.bin'

    if player.open_file(bin_filename):
        player.start()
        return True
    else:
        print(f"[LIGHT] Song {song_number}: Could not load {bin_filename}")
        return False


def check_song_change():
    """
    Monitor current playing song and auto-start lights when song changes
    """
    global current_song_number, _last_query_time
    
    now = ticks_ms()
    
    # Query current track periodically
    if ticks_diff(now, _last_query_time) > QUERY_INTERVAL_MS:
        _last_query_time = now
        query_current_track()
    
    # Check for response
    track_num = parse_uart_response()
    
    if track_num is not None and track_num > 0:
        # Song change detected
        if track_num != current_song_number:
            print(f"\n[AUDIO] Track changed: {current_song_number} → {track_num}")
            current_song_number = track_num
            
            # Stop current light show
            player.stop()
            
            # Load and start new light show for this song
            load_events_for_song(current_song_number)


# =====================================================================
# TEST MODE - Demonstrates all effects on all strips
# =====================================================================

def test_mode():
    """Run test mode showing all effects on all strips"""
    print("\n=== TEST MODE ===")
    print("Demonstrating all effects on all strips\n")
    
    effects = ["strobe", "flash", "pulse", "fade", "hold", "wave"]
    test_brightness = 200
    
    for effect in effects:
        print(f"Testing: {effect}")
        
        # Show effect on all strips simultaneously
        for i in range(5):
            player.strip_states[i].start_effect(effect, test_brightness, 2000, ticks_ms())
        
        # Run for 2 seconds
        start = ticks_ms()
        while ticks_diff(ticks_ms(), start) < 2000:
            current_time = ticks_ms()
            for i, state in enumerate(player.strip_states):
                state.update(strips[i], current_time)
            check_buttons()
            sleep(0.01)
        
        # Clear
        for strip in strips:
            strip.fill((0, 0, 0))
            strip.write()
        
        sleep(0.3)
    
    # Individual strip test
    print("\nTesting individual strips")
    for i in range(5):
        print(f"Strip {i} (GP{i})")
        strips[i].fill((100, 100, 100))
        strips[i].write()
        sleep(0.5)
        strips[i].fill((0, 0, 0))
        strips[i].write()
        sleep(0.2)
    
    print("\n=== TEST MODE COMPLETE ===\n")


# =====================================================================
# LEGACY CHASE EFFECTS (for testing/demo)
# =====================================================================

def clear_all():
    for s in strips:
        s.fill((0, 0, 0))
        s.write()


# ---- Startup ----
print("\n" + "="*50)
print("Auto-Sync MIDI Lighting Controller")
print("="*50)
print("\nControls:")
print("  GP18 = Random track")
print("  GP19 = Next track")
print("  GP20 = Previous track")
print("  GP21 = Pause/Play")
print("  GP22 = Volume Up")
print("  GP26 = Volume Down")
print("\nLED Strips: GP0, GP1, GP2, GP3, GP4")
print("\nLights auto-start when songs change!")
print("Configure mappings in song_config.py")
print("="*50 + "\n")

# Uncomment to run test mode on startup:
# test_mode()

# Init SV5W: reset, wait for it to boot, then set volume and play track 1
print("[AUDIO] Initialising SV5W...")
sv5w_cmd(0x0C)          # Reset
sleep(3)                # Wait for module to fully boot and read SD card
player_set_vol(25)
sleep(0.2)
sv5w_cmd(0x03, 0x00, 1) # Play track 1 explicitly
sleep(0.2)
# Read any response to confirm
if uart.any():
    resp = uart.read()
    print(f"[AUDIO] SV5W response: {list(resp) if resp else 'empty'}")
else:
    print("[AUDIO] No response from SV5W — check wiring/power")

print("[AUDIO] Starting playback...")
print("[LIGHT] Monitoring for song changes...\n")

# Auto-start song 1 light show immediately (SV5W will sync once connected)
load_events_for_song(1)

# Main loop
try:
    while True:
        # Monitor for song changes and auto-start lights
        check_song_change()
        
        # Check audio control buttons
        check_buttons()
        
        # Update lighting player
        player.update()
        
        # Small delay to prevent CPU spinning
        sleep(0.01)

except KeyboardInterrupt:
    clear_all()
    player.stop()
    player_pause()
    onboard.off()
    print("\nStopped.")

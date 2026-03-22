from machine import Pin, UART  # type: ignore
from neopixel import NeoPixel  # type: ignore
from time import sleep, ticks_ms, ticks_diff
import math
import sys

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
# UART1: GP8 TX → SV5W IO1/RXD, GP9 RX ← SV5W IO0/TXD
# Note: GP6/GP7 are CTS/RTS on RP2040 - not valid for UART TX/RX
uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
busy = Pin(5, Pin.IN)  # LOW = playing, HIGH = idle

# Track current playing song
current_song_number = None
_last_query_time = 0
QUERY_INTERVAL_MS = 500  # Query current track every 500ms

def sv5w_cmd(cmd, msb=0, lsb=0):
    """Send a command to the SV5W in DFPlayer-style protocol."""
    msg = bytes([0x7E, 0xFF, 0x06, cmd, 0x00, msb, lsb, 0xEF])
    uart.write(msg)
    sleep(0.05)

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


# =====================================================================
# LIGHTING EVENT PLAYBACK ENGINE
# =====================================================================

class StripState:
    """Track the state of a single LED strip's current effect"""
    def __init__(self):
        self.effect = None
        self.brightness = 0
        self.start_time = 0
        self.duration = 0
        self.active = False
    
    def start_effect(self, effect, brightness, duration, current_time):
        """Start a new effect on this strip"""
        self.effect = effect
        self.brightness = brightness
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
    
    def _scale_brightness(self, base_value):
        """Scale a base brightness value (0-255) by the event brightness"""
        return int((base_value / 255.0) * self.brightness)
    
    def _effect_strobe(self, strip, elapsed):
        """Rapid on/off flashing"""
        # Strobe at ~20Hz
        if (elapsed // 50) % 2 == 0:
            strip.fill((self.brightness, self.brightness, self.brightness))
        else:
            strip.fill((0, 0, 0))
    
    def _effect_flash(self, strip, progress):
        """Quick flash with fast fade out"""
        fade = max(0, 1.0 - progress)
        bright = int(self.brightness * fade)
        strip.fill((bright, bright, bright))
    
    def _effect_pulse(self, strip, progress):
        """Smooth pulse in and out"""
        # Sine wave for smooth pulse
        pulse = math.sin(progress * math.pi)
        bright = int(self.brightness * pulse)
        strip.fill((bright, bright, bright))
    
    def _effect_fade(self, strip, progress):
        """Linear fade out"""
        fade = 1.0 - progress
        bright = int(self.brightness * fade)
        strip.fill((bright, bright, bright))
    
    def _effect_hold(self, strip, progress):
        """Hold brightness then fade out at the end"""
        if progress < 0.7:
            # Hold steady
            strip.fill((self.brightness, self.brightness, self.brightness))
        else:
            # Fade out in last 30%
            fade = (1.0 - progress) / 0.3
            bright = int(self.brightness * fade)
            strip.fill((bright, bright, bright))
    
    def _effect_wave(self, strip, current_time, elapsed):
        """Moving wave/chase effect"""
        # Calculate wave position
        wave_speed = 0.1  # Wave cycles per ms
        wave_pos = (elapsed * wave_speed) % NUM_LEDS
        
        for i in range(NUM_LEDS):
            # Distance from wave peak
            dist = abs(i - wave_pos)
            if dist > NUM_LEDS / 2:
                dist = NUM_LEDS - dist
            
            # Brightness based on distance (gaussian-like)
            brightness_factor = max(0, 1.0 - (dist / 5.0))
            bright = int(self.brightness * brightness_factor)
            strip[i] = (bright, bright, bright)


class LightingPlayer:
    """Manages playback of lighting events"""
    def __init__(self, strips):
        self.strips = strips
        self.strip_states = [StripState() for _ in range(len(strips))]
        self.events = []
        self.event_index = 0
        self.playing = False
        self.start_time = 0
    
    def load_events(self, events):
        """Load events list: (time_ms, strip_index, brightness, effect, duration_ms)"""
        self.events = sorted(events, key=lambda x: x[0])
        print(f"[LIGHT] Loaded {len(self.events)} events")
    
    def start(self):
        """Start playback from beginning"""
        if self.playing:
            print("[LIGHT] Already playing")
            return
        
        if not self.events:
            print("[LIGHT] No events loaded")
            return
        
        self.playing = True
        self.event_index = 0
        self.start_time = ticks_ms()
        print("[LIGHT] Playback started")
        
        # Clear all strips
        for strip in self.strips:
            strip.fill((0, 0, 0))
            strip.write()
    
    def stop(self):
        """Stop playback"""
        self.playing = False
        self.event_index = 0
        
        # Clear all strips
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
        
        # Process any events that should trigger now
        while self.event_index < len(self.events):
            event_time, strip_index, brightness, effect, duration = self.events[self.event_index]
            
            if event_time <= playback_time:
                # Trigger this event
                if 0 <= strip_index < len(self.strip_states):
                    self.strip_states[strip_index].start_effect(
                        effect, brightness, duration, current_time
                    )
                self.event_index += 1
            else:
                break
        
        # Update all active effects
        for i, state in enumerate(self.strip_states):
            if state.active:
                state.update(self.strips[i], current_time)
        
        # Check if playback is complete
        if self.event_index >= len(self.events):
            # Check if all effects are done
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
    Dynamically load and start events for a specific song
    
    Args:
        song_number: Track number from SV5W player
    """
    # Get the event module name for this song
    event_module_name = get_events_for_song(song_number)
    
    if event_module_name is None:
        print(f"[LIGHT] Song {song_number}: No lights configured")
        player.stop()
        return False
    
    try:
        # Remove old module if it exists
        if event_module_name in sys.modules:
            del sys.modules[event_module_name]
        
        # Dynamically import the event module
        event_module = __import__(event_module_name)
        
        if hasattr(event_module, 'events'):
            events = event_module.events
            player.load_events(events)
            player.start()
            print(f"[LIGHT] Song {song_number}: Loaded {len(events)} events from {event_module_name}.py")
            return True
        else:
            print(f"[LIGHT] Song {song_number}: No 'events' list in {event_module_name}.py")
            return False
            
    except ImportError:
        print(f"[LIGHT] Song {song_number}: Event file {event_module_name}.py not found")
        return False
    except Exception as e:
        print(f"[LIGHT] Song {song_number}: Error loading events: {e}")
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
print("  GP16 = Random track")
print("  GP17 = Next track")
print("  GP18 = Previous track")
print("  GP19 = Pause/Play")
print("  GP20 = Volume Up")
print("  GP21 = Volume Down")
print("\nLED Strips: GP0, GP1, GP2, GP3, GP4")
print("\nLights auto-start when songs change!")
print("Configure mappings in song_config.py")
print("="*50 + "\n")

# Uncomment to run test mode on startup:
# test_mode()

# Set initial volume and start playing
player_set_vol(20)
sleep(0.2)
player_random()  # Start with a random track

print("[AUDIO] Starting playback...")
print("[LIGHT] Monitoring for song changes...\n")

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

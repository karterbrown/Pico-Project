# 🎮 CONTROL BUTTON LAYOUT

## 6-Button Full Control System

### Button Functions:

| Button | GPIO Pin | Physical Pin | Function | Description |
|--------|----------|--------------|----------|-------------|
| **BTN 1** | GP15 | Pin 20 | **Play Random** | Picks random track from choreography library |
| **BTN 2** | GP16 | Pin 21 | **Next Track** | Play next track sequentially |
| **BTN 3** | GP17 | Pin 22 | **Previous** | Play previous track |
| **BTN 4** | GP18 | Pin 24 | **Pause/Resume** | Pause current track or resume playback |
| **BTN 5** | GP19 | Pin 25 | **Volume Up** | Increase speaker volume |
| **BTN 6** | GP20 | Pin 26 | **Volume Down** | Decrease speaker volume |

---

## Wiring Configuration:

Each button has 2 terminals:
- **Terminal 1:** Connect to GPIO pin (see table above)
- **Terminal 2:** Connect to GND rail (common ground for all buttons)

**Example for Button 1:**
```
Button 1 Terminal 1 → GP15 (Pin 20)
Button 1 Terminal 2 → GND Rail on PCB
```

**All buttons share the same GND connection** (connect all Terminal 2 wires together to GND rail)

---

## Physical Layout Suggestion:

```
┌─────────────────────────────────┐
│                                 │
│   [BTN 1]        [BTN 2]        │  Row 1: Random, Next
│   Random         Next           │
│                                 │
│   [BTN 3]        [BTN 4]        │  Row 2: Previous, Pause
│   Previous       Pause          │
│                                 │
│   [BTN 5]        [BTN 6]        │  Row 3: Volume controls
│   Vol Up         Vol Down       │
│                                 │
└─────────────────────────────────┘
```

**Recommended:** Use different colored buttons for different functions:
- **Green:** Play Random (BTN 1)
- **Blue:** Next/Previous (BTN 2/3)
- **Yellow:** Pause (BTN 4)
- **Red:** Volume (BTN 5/6)

---

## Usage Examples:

### Play Random Light Show:
1. Press **BTN 1** (Random)
2. Pico picks random track from library
3. Music plays with synchronized light show

### Browse Tracks Sequentially:
1. Press **BTN 2** (Next) to move forward through tracks
2. Press **BTN 3** (Previous) to go back
3. Each track plays with its matching choreography

### Control During Playback:
1. **BTN 4** to pause/resume
2. **BTN 5/6** to adjust volume
3. Lights pause/dim when music pauses

---

## Button Types:

**Use momentary push buttons:**
- SPST (Single Pole Single Throw)
- Normally Open (NO)
- Tactile or arcade-style buttons
- No special features needed (Pico handles debouncing)

**Do NOT use:**
- Toggle switches
- Latching buttons
- Light-up buttons requiring extra power

---

## Available GPIO Pins (Still Free):

After using 6 buttons + 5 LED strips + UART + Busy pin:

**Still available:** GP6, GP7, GP8, GP9, GP12, GP13, GP14, GP21, GP22, GP26, GP27, GP28

You could add:
- More buttons for advanced features
- Status LEDs
- Display module
- Sensors
- Additional control interfaces

---

## Power Consideration:

**Buttons use NO additional power** - they're just switches!
- All 6 buttons: ~0mA draw
- Total system: Still 6.6A max (LEDs + audio + Pico)
- Your 10A supply handles it easily ✅

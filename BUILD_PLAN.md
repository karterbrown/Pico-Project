# 🎯 PROJECT BUILD PLAN

## Phase 1: Hardware Build ⚡

### Materials Checklist
- [ ] Raspberry Pi Pico
- [ ] BTF-LIGHTING 5V 10A Power Supply
- [ ] 5× WS2812B LED strips (20 LEDs each = 100 total)
- [ ] SV5W MP3 Module + SD card + Speaker
- [ ] 6× Buttons (momentary push buttons)
- [ ] SPST Power Switch (10A+ rated)
- [ ] Central Distribution Board (terminal block PCB or breadboard)
- [ ] Wire: 18 AWG (power), 22-24 AWG (signals)
- [ ] Wire connectors/terminal blocks
- [ ] Tools: Soldering iron, wire strippers, multimeter

### Build Steps
1. **Set up central PCB distribution board**
   - Create +5V bus bar
   - Create GND bus bar

2. **Wire power system** (PSU OFF, unplugged!)
   - PSU +5V → Power Switch → PCB +5V rail
   - PSU GND → PCB GND rail (direct, no switch)

3. **Connect Pico to PCB**
   - VBUS (Pin 40) → +5V rail
   - GND (Pin 38) → GND rail
   - ⚠️ **Do NOT connect USB to the Pico at the same time the PSU is live.** Powering VBUS from the rail and having USB plugged in simultaneously can backfeed voltage — check your board behaviour before doing both.

4. **Connect LED strips to PCB power**
   - All 5× strip 5V wires → +5V rail
   - All 5× strip GND wires → GND rail
   - ⚠️ **Use adequate wire gauge.** 5 strips at full white can draw 3–5A+. Do not rely on thin hookup wire or a single narrow PCB trace for the shared power rail. Use a star or bus-bar distribution layout rated for the full load.

5. **Connect LED data lines (Pico to strips)**
   - GP0 (Pin 1) → 330Ω resistor → Strip 1 DIN
   - GP1 (Pin 2) → 330Ω resistor → Strip 2 DIN
   - GP2 (Pin 4) → 330Ω resistor → Strip 3 DIN
   - GP3 (Pin 5) → 330Ω resistor → Strip 4 DIN
   - GP4 (Pin 6) → 330Ω resistor → Strip 5 DIN
   - 🔌 **Add a 1000µF electrolytic capacitor across the +5V/GND rail at the distribution board entry (after the power switch), positive leg to +5V rail, negative leg to GND rail.** This suppresses power-on surge and protects the first LED in each strip.
   - ⚠️ **Level shifter strongly recommended for permanent build:** WS2812B VIH = 0.7×VDD = 3.5V minimum at 5V supply. Pico GPIO is 3.3V — below spec. A 74AHCT125 or 74HCT14 between Pico GPIOs and the 330Ω resistors ensures reliable signalling. Direct 3.3V connection often works for testing but should not be relied on for a finished build.

6. **Connect SV5W to PCB**
   - VCC → +5V rail
   - GND → GND rail
   - Speaker → SPK+/SPK-

7. **Connect SV5W UART (Pico ↔ SV5W)**
   - GP6 (Pin 9) **TX out** → **IO1 / RXD** (SV5W serial receive input)
   - GP7 (Pin 10) **RX in** ← **IO0 / TXD** (SV5W serial transmit output)
   - GP5 (Pin 7) **input** ← **BUSY** (high while playing)
   - ⚠️ TX and RX **must be crossed** — Pico TX → SV5W RX, SV5W TX → Pico RX.
   - ⚠️ At least one seller has noted the SV5W datasheet has **VCC and GND reversed**. Trust the **PCB silkscreen** for power pin orientation, not the datasheet.
   - Default UART baud rate: **9600**.

8. **Connect Control Buttons (6 total)**
   - Button 1 (Random): Terminal 1 → GP16 (Pin 21), Terminal 2 → GND rail
   - Button 2 (Next): Terminal 1 → GP17 (Pin 22), Terminal 2 → GND rail
   - Button 3 (Previous): Terminal 1 → GP18 (Pin 24), Terminal 2 → GND rail
   - Button 4 (Pause): Terminal 1 → GP19 (Pin 25), Terminal 2 → GND rail
   - Button 5 (Vol Up): Terminal 1 → GP20 (Pin 26), Terminal 2 → GND rail
   - Button 6 (Vol Down): Terminal 1 → GP21 (Pin 27), Terminal 2 → GND rail

9. **Configure SV5W DIP Switches for UART Mode**
   - See DIP_SWITCH_CONFIG.md for full details.
   - Set SW1: ON (enables UART control)
   - Set SW2: OFF (disables trigger pin mode)
   - Set SW3: OFF (normal playback mode)
   - **Note:** This module has 3 DIP switches (not 8)
   - **Critical:** Wrong DIP switch = module won't respond to UART commands!

10. **Pre-power checklist ✅**
   - [ ] All power connections secure
   - [ ] No loose wire strands
   - [ ] No shorts between +5V and GND
   - [ ] All 5 LED data connections correct
   - [ ] All 6 buttons wired
   - [ ] SV5W UART connections (GP6 TX→IO1/RXD, GP7 RX←IO0/TXD, GP5←BUSY)
   - [ ] SV5W DIP switches set for UART mode
   - [ ] SD card inserted in SV5W
   - [ ] Power switch in OFF position

---

## Phase 2: Initial Testing 🧪

### Test 1: Basic Power
1. Connect Pico to computer via USB (PSU still OFF)
2. Upload basic LED test code
3. Disconnect USB
4. Turn ON PSU power switch
5. **Expected:** Pico LED should blink, some LED activity

### Test 2: LED Strips
1. Test each strip individually
2. Check all 100 LEDs light up
3. Test colors: red, green, blue, white
4. **Expected:** All LEDs working, correct colors

### Test 3: Buttons
1. Test each button individually (6 buttons)
2. Button 1: Random track selection
3. Button 2: Next track sequential
4. Button 3: Previous track
5. Button 4: Pause/resume
6. Button 5/6: Volume control
7. **Expected:** Each button performs its function

### Test 4: Audio
1. Trigger track from button
2. **Expected:** SV5W plays audio from speaker

### Debug if needed
- Use multimeter to check voltages
- Verify connections against your wiring diagram
- Check for loose wires

---

## Phase 3: Music Preparation 🎵

### Choose Your Tracks
- [ ] Select songs for light show (as many as you want!)
- [ ] Load into Pro Tools (or your DAW)
- [ ] Convert to MP3 format
- [ ] Name sequentially: `0001.mp3`, `0002.mp3`, `0003.mp3`, etc.
- [ ] Copy all to SV5W SD card root directory

**Note:** With UART mode, you can have dozens or hundreds of tracks! Each can have its own choreographed light show.

### Mark Events (For Each Track)
Open your DAW and mark significant events:
- Intro/starts
- Beat drops
- Verse/chorus sections
- Build-ups
- Breaks/quiet parts
- Ending

**Repeat this process for each song you want to choreograph!**

### Export Timecode List
For each marked event, note:
```
Sample Location → Convert to Seconds (÷ 44100)

Example:
132,300 samples ÷ 44,100 = 3.000 seconds
```

### Create Event Lists
Format for each track:
```
=== TRACK 1: "Funky Beat.mp3" ===
0.000 - Track starts (fade in, soft blue)
2.456 - First beat (flash white)
5.123 - Verse starts (gentle pulse red)
8.789 - Build up (intensity increases)
12.345 - Drop (strobe + rainbow)
...etc

=== TRACK 2: "Chill Vibes.mp3" ===
0.000 - Intro (slow rainbow)
3.210 - Melody enters (wave effect)
...etc

=== TRACK 3: "Epic Drop.mp3" ===
0.000 - Build tension (pulse increasing)
12.345 - Massive drop (full strobe)
...etc
```

Send all your track lists = Ready for programming! 📝

---

## Phase 4: Programming Light Show 💻

### What I'll Build For You:
1. **SV5W UART Library** - Serial communication for full player control
2. **Cue Engine** - Reads your timecode lists, triggers effects at exact moments
3. **Effect Library** - Pre-made effects:
   - Solid colors
   - Pulse/fade
   - Flash/strobe
   - Chase/wave
   - Rainbow
   - Custom combinations
4. **Track Manager** - Handles multiple songs with different cue lists
5. **6-Button Control System:**
   - Button 1: Play random track from library
   - Button 2: Next track (sequential)
   - Button 3: Previous track
   - Button 4: Pause/Resume
   - Button 5: Volume Up
   - Button 6: Volume Down
6. **Choreography Mapper** - Links each track number to its light show

### Your Part:
- Provide timecode lists with descriptions for each track
- Test and give feedback
- Request adjustments

### How It Works:
- Press button → Random track chosen (e.g., track 47)
- Pico sends UART command: "Play track 47"
- Pico looks up choreography for track 47
- Perfect sync! Audio + lights matched! 🎵💡

---

## Phase 5: Final Integration & Testing 🎉

### Upload & Test Cycle:
1. PSU OFF
2. Connect USB
3. Upload code
4. Disconnect USB
5. PSU ON
6. Test show
7. Take notes on timing/effects
8. Repeat until perfect!

### Fine-Tuning:
- Adjust timings (add/subtract milliseconds)
- Change colors
- Modify effect speeds
- Add/remove cues

### Final Show:
- [ ] All cues trigger at correct times
- [ ] Effects look good
- [ ] Audio synced perfectly
- [ ] Button controls working
- [ ] Ready for performance! 🎊

---

## Safety Reminders ⚠️

**NEVER:**
- Have USB and PSU connected simultaneously
- Touch wiring while powered
- Exceed 10A draw

**ALWAYS:**
- Turn off PSU before connecting USB
- Disconnect USB before turning on PSU
- Check for shorts before powering on

---

## Quick Reference

**Upload Code:** PSU OFF → USB connected
**Test Circuit:** USB disconnected → PSU ON
**Scripts:**
- `./check-deploy.sh` - Check repo status
- `./deploy.sh "message"` - Commit & push changes

**Diagrams:**
- WIRING_BUILD_DIAGRAM.drawio - Build reference diagram

---

## Current Status: 📍

- [x] Planning complete
- [x] Wiring diagrams created
- [x] Safety review passed
- [ ] **→ NEXT: Build hardware (follow Phase 1 steps above)**
- [ ] Initial testing
- [ ] Music preparation
- [ ] Program light show
- [ ] Final testing & launch!

---

**Build plan is ready. Follow Phase 1 step-by-step, then move to Phase 2 testing.** 🚀

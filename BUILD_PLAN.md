# 🎯 PROJECT BUILD PLAN

## Phase 1: Hardware Build ⚡

### Materials Checklist
- [ ] Raspberry Pi Pico
- [ ] BTF-LIGHTING 5V 10A Power Supply
- [ ] 5× WS2812B LED strips (20 LEDs each = 100 total)
- [ ] SV5W MP3 Module + SD card + Speaker
- [ ] Button (momentary push button)
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

4. **Connect LED strips to PCB power**
   - All 5× strip 5V wires → +5V rail
   - All 5× strip GND wires → GND rail

5. **Connect LED data lines (Pico to strips)**
   - Strip 1 DIN → GP0 (Pin 1)
   - Strip 2 DIN → GP1 (Pin 2)
   - Strip 3 DIN → GP2 (Pin 4)
   - Strip 4 DIN → GP3 (Pin 5)
   - Strip 5 DIN → GP11 (Pin 15)

6. **Connect SV5W to PCB**
   - VCC → +5V rail
   - GND → GND rail
   - Speaker → SPK+/SPK-

7. **Connect SV5W triggers (Pico to SV5W)**
   - GP6 (Pin 9) → I02
   - GP7 (Pin 10) → I03
   - GP8 (Pin 11) → I04
   - GP9 (Pin 12) → I05
   - GP10 (Pin 14) → Busy (optional but recommended)

8. **Connect Button**
   - Terminal 1 → GP15 (Pin 20)
   - Terminal 2 → GND rail

9. **Pre-power checklist ✅**
   - [ ] All power connections secure
   - [ ] No loose wire strands
   - [ ] No shorts between +5V and GND
   - [ ] All 5 LED data connections correct
   - [ ] Button wired
   - [ ] SV5W triggers connected
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

### Test 3: Button
1. Press button during test pattern
2. **Expected:** Pattern changes

### Test 4: Audio
1. Trigger track from button
2. **Expected:** SV5W plays audio from speaker

### Debug if needed
- Use multimeter to check voltages
- Verify connections against WIRING_BUILD_DIAGRAM.drawio
- Check for loose wires

---

## Phase 3: Music Preparation 🎵

### Choose Your Track
- [ ] Select song for light show
- [ ] Load into Pro Tools (or your DAW)
- [ ] Convert to MP3 and name: `0001.mp3`
- [ ] Copy to SV5W SD card

### Mark Events
Open your DAW and mark significant events:
- Intro/starts
- Beat drops
- Verse/chorus sections
- Build-ups
- Breaks/quiet parts
- Ending

### Export Timecode List
For each marked event, note:
```
Sample Location → Convert to Seconds (÷ 44100)

Example:
132,300 samples ÷ 44,100 = 3.000 seconds
```

### Create Event List
Format:
```
0.000 - Track starts (fade in, soft blue)
2.456 - First beat (flash white)
5.123 - Verse starts (gentle pulse red)
8.789 - Build up (intensity increases)
12.345 - Drop (strobe + rainbow)
...etc
```

Send this list = Ready for programming! 📝

---

## Phase 4: Programming Light Show 💻

### What I'll Build For You:
1. **Cue Engine** - Reads your timecode list, triggers effects at exact moments
2. **Effect Library** - Pre-made effects:
   - Solid colors
   - Pulse/fade
   - Flash/strobe
   - Chase/wave
   - Rainbow
   - Custom combinations
3. **Track Manager** - Handles multiple songs with different cue lists
4. **Button Control** - Start/stop, track selection

### Your Part:
- Provide timecode list with descriptions
- Test and give feedback
- Request adjustments

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
- WIRING_BUILD_DIAGRAM.drawio - Main build reference
- WIRING_DIAGRAM.drawio - Detailed connections

---

## Current Status: 📍

- [x] Planning complete
- [x] Wiring diagrams created
- [x] Safety review passed
- [ ] **→ NEXT: Order/receive LED strips**
- [ ] Build hardware
- [ ] Initial testing
- [ ] Music preparation
- [ ] Program light show
- [ ] Final testing & launch!

---

**You're on Phase 1 - Waiting for LEDs to arrive. When ready, start building with WIRING_BUILD_DIAGRAM.drawio!** 🚀

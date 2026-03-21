# ⚙️ SV5W DIP SWITCH CONFIGURATION

## UART Mode Setup (Required for Unlimited Tracks)

### DIP Switch Location:
The SV5W module has a bank of **3 DIP switches** (SW1-SW3) on the board. They control the operating mode and settings.

---

## Configuration for UART Control Mode:

### Basic UART Setup:

| Switch | Position | Function |
|--------|----------|----------|
| **SW1** | **ON** | **Enable UART serial control (REQUIRED)** |
| **SW2** | **OFF** | Disable trigger pin mode |
| SW3 | OFF | Normal playback mode (consult manual if issues) |

### Critical Settings:
- ✅ **SW1 MUST be ON** - This enables UART mode
- ✅ **SW2 MUST be OFF** - This disables trigger pin mode (I02-I07)
- ⚠️ **If SW1 is OFF:** Module will NOT respond to serial commands!
- ⚠️ **If SW2 is ON:** Module may respond to trigger pins instead of UART

---

## Common Configuration Patterns:

### Most Common (Standard UART):
```
SW1: ON   ← Enable UART
SW2: OFF  ← Disable triggers
SW3: OFF  ← Normal playback
```

### With Repeat/Loop:
```
SW1: ON   ← Enable UART
SW2: OFF  ← Disable triggers
SW3: OFF
```

---

## Visual Reference:

```
┌─────────────────────────────────┐
│  SV5W MP3 MODULE                │
│                                 │
│   [DIP SWITCH BANK]             │
│   ┌─┬─┬─┐                       │
│   │1│2│3│                       │
│   └─┴─┴─┘                       │
│    ↑ ↑ ↑                        │
│    │ │ └── SW3: OFF             │
│    │ └──── SW2: OFF (no triggers)│
│    └────── SW1: ON (UART enabled)│
│                                 │
│   [VCC] [GND] [I00/TX] [I01/RX] │
│                                 │
└─────────────────────────────────┘
```

**Remember:** 
- ON = Switch pushed toward the number
- OFF = Switch pushed away from the number

---

## Testing DIP Switch Configuration:

### After setting DIP switches:

1. **Power cycle the module** (remove and reconnect power)
2. Connect Pico via UART (GP4→I01/RX, GP5→I00/TX)
3. Send test command via serial: `play track 1`
4. **If it works:** DIP switches correct! ✅
5. **If nothing happens:** Check SW1 is ON, SW2 is OFF

### Common Problems:

| Problem | Cause | Solution |
|---------|-------|----------|
| Module doesn't respond to UART | SW1 is OFF | Set SW1 to ON, power cycle |
| Only trigger pins work | SW2 is ON | Set SW2 to OFF, power cycle |
| Random playback issues | Wrong SW3 configuration | Reset SW3 to OFF, test |
| Module plays but Pico can't control | UART wires wrong | Check GP4→RX, GP5→TX |

---

## Module Variations:

**Different SV5W versions may have different switch meanings!**

### Common Variants:

#### **Version A (Most Common):**
- SW1: UART enable
- SW2: Trigger mode
- SW3: Playback mode

#### **Version B:**
- SW1-2: Mode selection (both ON = UART)
- SW3: Settings

#### **Version C (Rare):**
- All settings via serial commands
- DIP switches ignored

**Always check your module's manual or markings!**

---

## What Each Mode Does:

### Trigger Pin Mode (SW1: OFF, SW2: ON):
- I02-I07 pins trigger tracks 1-6
- Pull pin LOW = play that track
- Limited to 6-8 tracks total
- Simple but inflexible

### UART Serial Mode (SW1: ON, SW2: OFF):
- Full control via serial commands
- Unlimited tracks (99-512 depending on model)
- Volume control
- Pause/resume/stop
- Query status
- **This is what we're using!** ✅

### Hybrid Mode (Some Models):
- Both UART and triggers work
- Not recommended (can cause conflicts)

---

## Verification Checklist:

Before building your circuit:

- [ ] Locate DIP switches on SV5W module
- [ ] Set SW1 to ON (UART enable)
- [ ] Set SW2 to OFF (trigger disable)
- [ ] Set SW3 per manual (or OFF to start)
- [ ] Power cycle module
- [ ] Test with simple UART commands
- [ ] Confirm module responds before final assembly

---

## Pro Tips:

1. **Take a photo** of DIP switch settings before changing them
2. **Label your module** with correct settings for your project
3. **Test UART control** before wiring entire system
4. **Use tweezers or small screwdriver** to flip tiny switches
5. **Power cycle after ANY switch change** - settings load at boot

---

## UART Commands Reference (Quick Test):

Once DIP switches are correct, test with these commands:

```python
# From MicroPython REPL (USB connected):
from machine import UART, Pin
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

# Play track 1
uart.write(b'\x7E\xFF\x06\x03\x00\x00\x01\xEF')

# If you hear audio = SUCCESS! DIP switches correct!
```

---

## Resources:

- Check module packaging for DIP switch documentation
- Search "SV5W UART mode DIP switches" online
- Test each setting systematically
- Post on forums with your module version for help

**Remember:** DIP switches configure the module at boot - always power cycle after changes!

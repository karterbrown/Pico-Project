# Auto-Sync MIDI Lighting System 🎵💡

Automatically sync LED light shows to songs playing from your Raspberry Pi Pico / SV5W audio player. Each song gets its own custom lighting that starts automatically when the song plays!

## What It Does

- 🎵 Songs play randomly from your SV5W audio player
- 💡 Pico detects which song is playing
- ✨ Automatically loads and plays the matching light show
- 🔄 Lights update automatically when you change tracks
- 🎨 Each song can have unique lighting or share patterns

## Quick Example

```bash
# On your Mac: Convert MIDI to light shows
python lights_tool.py cue song1.mid -o song001_events.py
python lights_tool.py cue song2.mid -o song002_events.py

# Configure which songs use which lights
# In song_config.py:
SONG_MAPPING = {
    1: "song001_events",  # Track 1
    2: "song002_events",  # Track 2
}

# Copy to Pico: main.py + song_config.py + all event files
# Done! Lights auto-sync to songs!
```

## Hardware

- Raspberry Pi Pico with MicroPython
- 5 × WS2812B LED strips (20 LEDs each)
- Connected to: GP0, GP1, GP2, GP3, GP4
- SV5W audio player (UART on GP8/GP9)
- Control buttons on GP16-GP21

## Setup

### 1. Mac Side - Install Tools

```bash
pip install -r requirements.txt
```

### 2. Create Light Shows in Logic Pro

1. Import your song
2. Create MIDI track "LIGHTING CUES"
3. Use notes to control strips:
   - C1 = Strip 0 (GP0)
   - D1 = Strip 1 (GP1)
   - E1 = Strip 2 (GP2)
   - F1 = Strip 3 (GP3)
   - G1 = Strip 4 (GP4)
4. Export MIDI from same markers as audio

### 3. Convert MIDI to Events

```bash
# Name files by track number
python lights_tool.py cue mysong.mid -o song001_events.py
python lights_tool.py cue another.mid -o song002_events.py
```

### 4. Configure Song Mapping

Edit `song_config.py`:

```python
SONG_MAPPING = {
    1: "song001_events",  # SD card track 1
    2: "song002_events",  # SD card track 2
    3: "song003_events",  # SD card track 3
    # Add all your songs...
}
```

### 5. Copy to Pico

Copy to your Pico:
- `main.py`
- `song_config.py`
- All `songXXX_events.py` files

### 6. Play!

Reset your Pico. Songs play, lights sync automatically! 🎉

## Note Length = Effect Type

In Logic, use note length to choose visual effects:

| Length | Effect | Look |
|--------|--------|------|
| Tiny | Strobe | ⚡ Rapid flash |
| 16th note | Flash | 💫 Quick hit |
| 8th note | Pulse | 🌊 Breathing |
| Quarter | Fade | 🌅 Smooth decay |
| Half note | Hold | 🔦 Sustained |
| Whole+ | Wave | 🌀 Chase motion |

**Velocity** controls brightness (harder = brighter)

## Advanced Features

### Share Patterns Across Songs

```python
SONG_MAPPING = {
    1: "high_energy",
    2: "chill_vibes",
    3: "high_energy",  # Reuse same pattern
    4: "high_energy",  # Reuse again
    5: "chill_vibes",  # Reuse this one
}
```

### Disable Lights for Some Songs

```python
SONG_MAPPING = {
    1: "song001_events",
    2: None,  # No lights for track 2
    3: "song003_events",
}
```

### Auto-Generate from Existing MIDI

Don't want to create custom tracks? Auto-generate:

```bash
python lights_tool.py interpret song.mid -o song005_events.py
```

This analyzes the music and creates lights automatically.

## Files

- `lights_tool.py` - Mac converter (MIDI → events)
- `main.py` - Pico player (auto-syncs lights)
- `song_config.py` - Song-to-lightshow mapping
- `song001_events.py`, `song002_events.py`, etc. - Light show data

## Controls

| Button | Function |
|--------|----------|
| GP16 | Random track |
| GP17 | Next track |
| GP18 | Previous track |
| GP19 | Pause/Play |
| GP20 | Volume up |
| GP21 | Volume down |

*No manual button needed - lights auto-start!*

## Troubleshooting

**Lights don't change when songs change**
- Wait ~500ms after pressing next/prev
- Check UART wiring (GP8 → SV5W RX, GP9 → SV5W TX)

**Event file not found**
- Verify files are copied to Pico
- Check `song_config.py` spelling (no .py extension in mapping)

**Lights don't match music timing**
- Export audio and MIDI from exact same range in Logic
- Check tempo detection in converter output

## Documentation

- **QUICKSTART.md** - Fast tutorial
- **LIGHTING_SYSTEM.md** - Complete documentation
- **song_config_example.py** - Configuration examples

## Tips

1. **Name files systematically**: `song001_events.py`, `song002_events.py`, etc.
2. **Test one song first** before building a full playlist
3. **Use interpret mode** for quick auto-generated shows
4. **Use cue mode** for precise, choreographed lighting
5. **Share patterns** to save time on similar songs
6. **Match note lengths** to your song's feel (short notes for energy, long for ambience)

## Example Workflow

```bash
# Convert 10 songs
for i in {1..10}; do
    python lights_tool.py cue track${i}.mid -o song$(printf "%03d" $i)_events.py
done

# Edit song_config.py with all mappings
# Copy everything to Pico
# Enjoy your automated light show system!
```

Built for music lovers who want their lights to be part of the performance. 🎸✨

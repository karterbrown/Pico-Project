# MIDI-to-LED Auto-Sync Lighting System for Raspberry Pi Pico

A complete lighting control system that automatically syncs WS2812 LED strips to songs playing from your SV5W audio player. Each song can have its own custom light show that starts automatically when the song plays.

## Overview

This system has two parts:

1. **Mac-side converter** (`lights_tool.py`) - Converts MIDI files to lighting events
2. **Pico-side player** (`main.py`) - Automatically plays the right light show for each song

## How It Works

1. Songs play randomly from your SV5W audio player
2. The Pico monitors which song is currently playing
3. When a new song starts, it automatically loads and plays the matching light show
4. Each song can have its own unique lighting or share patterns with other songs

## Hardware Setup

### LED Strips
- 5 WS2812B LED strips (20 LEDs each)
- Connected to GPIO pins: **GP0, GP1, GP2, GP3, GP4**

### Buttons
- **GP16** - Random track
- **GP17** - Next track
- **GP18** - Previous track
- **GP19** - Pause/Play audio
- **GP20** - Volume Up
- **GP21** - Volume Down

*Note: Lights start automatically when songs play - no manual button needed!*

### Audio
- SV5W audio player connected via UART1 (GP8/GP9)

## Quick Start

### 1. Install Dependencies (Mac)

```bash
pip install mido
```

### 2. Create MIDI Lighting Cue Track in Logic Pro

1. Import your song into Logic Pro
2. Create a new MIDI track named "LIGHTING CUES"
3. Use these notes to control specific strips:
   - **C1** → Strip 0 (GP0)
   - **D1** → Strip 1 (GP1)
   - **E1** → Strip 2 (GP2)
   - **F1** → Strip 3 (GP3)
   - **G1** → Strip 4 (GP4)
4. Use **velocity** to control brightness (0-127)
5. Use **note length** to choose effects:
   - Very short (< 0.25 beat) → **strobe**
   - Short (< 0.5 beat) → **flash**
   - Medium (< 1 beat) → **pulse**
   - Long (< 2 beats) → **fade**
   - Longer (< 4 beats) → **hold**
   - Very long (≥ 4 beats) → **wave**

### 3. Export MIDI from Logic Pro

**Important:** Export both your audio AND MIDI from the **exact same start/end markers**

1. Set your cycle locators around the section you want
2. Export audio: `File → Export → Audio`
3. Export MIDI: `File → Export → Selection as MIDI File`

### 4. Convert MIDI to Events

Name your event files by song/track number:

For custom lighting tracks (recommended):
```bash
python lights_tool.py cue my_song_lights.mid -o song001_events.py
python lights_tool.py cue another_song.mid -o song002_events.py
```

For auto-generated light show from existing MIDI:
```bash
python lights_tool.py interpret song.mid -o song003_events.py
```

Each track on your SV5W player gets its own event file.

### 5. Configure Song Mapping

Edit `song_config.py` to map track numbers to event files:

```python
SONG_MAPPING = {
    1: "song001_events",  # Track 1 uses song001_events.py
    2: "song002_events",  # Track 2 uses song002_events.py
    3: "song003_events",  # Track 3 uses song003_events.py
    4: "song001_events",  # Track 4 reuses song001's lights
    # Add more mappings...
}
```

Songs can share the same light show or each have unique ones.

### 6. Copy to Pico

Copy these files to your Pico:
- `main.py`
- `song_config.py`
- All your event files (`song001_events.py`, `song002_events.py`, etc.)

### 7. Play Music!

1. Reset your Pico
2. Music plays randomly from SV5W player
3. **Lights automatically sync to each song!**
4. Change tracks with buttons - lights update automatically

## Usage Details

### Converter Modes

#### Cue Mode (Custom Tracks)
Use when you want **precise control** over lighting:

```bash
python lights_tool.py cue my_lights.mid -o my_song_events.py
```

- Requires specific note mapping (C1-G1)
- Each note directly controls a specific strip
- Full creative control
- Best for intentional, choreographed shows

#### Interpret Mode (Auto-Generated)
Use when you want **automatic** light show from existing MIDI:

```bash
python lights_tool.py interpret song.mid -o song_events.py
```

- Works with any MIDI file
- Distributes notes across strips by pitch range
- Low notes → Strip 0, High notes → Strip 4
- Quick way to add lights to existing songs

### Effects Reference

| Effect | Description | Visual |
|--------|-------------|--------|
| **strobe** | Rapid on/off flashing (~20Hz) | ⚡ High energy |
| **flash** | Quick flash with fast fade | 💫 Impact hit |
| **pulse** | Smooth sine wave in/out | 🌊 Breathing |
| **fade** | Linear fade to black | 🌅 Soft decay |
| **hold** | Hold steady, fade at end | 🔦 Sustained |
| **wave** | Moving chase effect | 🌀 Motion |

### Note Length Guide

In Logic Pro, match your note lengths to the effect you want:

| Musical Length | Beats | Effect |
|----------------|-------|--------|
| 32nd note | ~0.125 | strobe |
| 16th note | 0.25 | flash |
| 8th note | 0.5 | pulse |
| Quarter note | 1.0 | fade |
| Half note | 2.0 | hold |
| Whole note+ | 4.0+ | wave |

## Workflow Examples

### Building Your Complete Playlist

**Step 1: Organize your music**
- Load all your MP3s onto the SV5W player's SD card
- Note which track number each song is

**Step 2: Create light shows**

For each song:
1. Import song into Logic Pro
2. Create MIDI "LIGHTING CUES" track
3. Drop in C1-G1 notes where you want lights
4. Vary velocity for brightness changes
5. Vary note length for different effects
6. Export MIDI (same range as audio)
7. Run: `python lights_tool.py cue song_lights.mid -o song00X_events.py`
   (where X is the track number)

**Step 3: Map everything**

Edit `song_config.py`:
```python
SONG_MAPPING = {
    1: "song001_events",
    2: "song002_events",
    3: "song003_events",
    # ... etc
}
```

**Step 4: Deploy to Pico**
- Copy `main.py`, `song_config.py`, and all event files to Pico
- Reset and enjoy!

### Quick Light Show from Existing MIDI

1. Have existing MIDI file of song
2. Run: `python lights_tool.py interpret song.mid -o song005_events.py`
3. Add to `song_config.py`: `5: "song005_events"`
4. Copy to Pico

### Reusing Patterns Across Songs

Want multiple songs to use the same lighting pattern?

1. Create one "master" lighting MIDI pattern
2. Convert it: `python lights_tool.py cue pattern.mid -o dance_pattern.py`
3. In `song_config.py`, assign multiple songs to it:
```python
SONG_MAPPING = {
    1: "dance_pattern",
    3: "dance_pattern",
    7: "dance_pattern",
    10: "dance_pattern",
}
```

### Disabling Lights for Certain Songs

Some songs shouldn't have lights? No problem:

```python
SONG_MAPPING = {
    1: "song001_events",
    2: None,  # Track 2: no lights
    3: "song003_events",
    4: None,  # Track 4: no lights
}
```

## Test Mode

To verify wiring and effects without MIDI files:

In `main.py`, uncomment this line in the startup section:
```python
test_mode()
```

This will cycle through all effects on all strips on boot.

## Troubleshooting

### "No song_config.py found"
- The system will fall back to using `events.py` for all songs
- Create `song_config.py` to map specific songs to specific light shows

### "Event file not found" 
- Make sure you've copied all event files to the Pico
- Check that filenames in `song_config.py` match actual files (without .py extension)
- Verify the event files are in the root directory with `main.py`

### Lights not changing when I press Next/Previous
- The Pico queries the current track from SV5W via UART
- Wait ~500ms after changing songs for detection
- Check UART connections (GP8 TX → SV5W RX, GP9 RX → SV5W TX)

### Lights not syncing to audio timing
- Make sure you exported audio and MIDI from the **same start/end markers** in Logic
- The timing is preserved from export start, not from first note
- Don't normalize MIDI timing unless you also trimmed the audio

### Some notes ignored in cue mode
- Only C1, D1, E1, F1, G1 are mapped in cue mode
- Other notes are ignored with a warning
- Use interpret mode if you want all notes to trigger lights

### Events fire too early/late
- Check your MIDI export settings
- Verify tempo is correctly detected (shown in converter output)
- Make sure you're not using tempo changes mid-song (or handle them manually)

### Lights look wrong/choppy
- Increase LED strip update rate if needed
- Check power supply for LED strips
- Verify GPIO pin connections match code

## File Reference

### `lights_tool.py`
Mac-side MIDI converter
- Reads MIDI files
- Extracts timing, notes, tempo
- Generates event files (e.g., `song001_events.py`)

### `main.py`
Pico-side auto-sync lighting player
- Monitors current playing song from SV5W
- Dynamically loads correct event file for each song
- Controls 5 LED strips
- Non-blocking playback
- Auto-starts lights when songs change

### `song_config.py`
Song-to-lightshow mapping
- Maps track numbers to event files
- `SONG_MAPPING` dictionary
- Allows sharing patterns across songs
- Can disable lights for specific tracks

### Event Files (`song001_events.py`, `song002_events.py`, etc.)
Lighting event data for specific songs
- Generated by `lights_tool.py`
- Format: `(time_ms, strip_index, brightness, effect, duration_ms)`
- Dynamically loaded by `main.py` when song plays

## Advanced Tips

### Managing Large Playlists

For many songs:

```bash
# Convert each song with numbered output
python lights_tool.py cue song1.mid -o song001_events.py
python lights_tool.py cue song2.mid -o song002_events.py
python lights_tool.py cue song3.mid -o song003_events.py
# ... etc

# Use a shell loop for batch conversion
for i in {1..20}; do
    python lights_tool.py interpret song$i.mid -o song$(printf "%03d" $i)_events.py
done
```

Then map them all in `song_config.py`.

### Color Variations
Current implementation uses white LEDs. To add color:

1. Modify effect methods in `StripState` class
2. Instead of `(brightness, brightness, brightness)`
3. Use `(red, green, blue)` tuples
4. You can map velocity or pitch to color

### Dynamic Brightness
Velocity already controls brightness. In Logic:

- Soft notes (velocity 30-60) → dim
- Medium notes (velocity 70-100) → normal
- Hard notes (velocity 110-127) → bright

### Complex Patterns
For intricate patterns:

1. Create multiple overlapping notes in Logic
2. Different strips can run different effects simultaneously
3. Use note length variety for visual interest
4. Layer strobe/flash over longer fade/hold effects

## System Requirements

### Mac Side
- Python 3.7+
- mido library (`pip install mido`)
- Logic Pro (or any DAW that exports MIDI)

### Pico Side
- Raspberry Pi Pico
- MicroPython firmware
- WS2812B LED strips
- Adequate power supply for LEDs

## Credits

System designed for syncing LED lighting to music using MIDI as the timing source. Perfect for live performance, installation art, or just making your music player look awesome.

## License

Use freely for personal and commercial projects.

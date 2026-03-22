# Quick Start Guide - Auto-Sync MIDI Lighting System

## First Time Setup

### 1. Install Mac Dependencies
```bash
cd /Users/karterbrown/Desktop/Pico-Project
pip install -r requirements.txt
```

### 2. Test the Converter
```bash
python lights_tool.py --help
```

## Creating Your First Light Show

### Step 1: Make MIDI Lighting Track in Logic Pro

1. Open Logic Pro
2. Import your song audio
3. Create new MIDI track called "LIGHTING CUES"
4. Add notes using this mapping:
   - **C1** = Strip 0 (GP0)
   - **D1** = Strip 1 (GP1)
   - **E1** = Strip 2 (GP2)
   - **F1** = Strip 3 (GP3)
   - **G1** = Strip 4 (GP4)
5. Set locators around your section
6. Export Selection as MIDI

### Step 2: Convert to Events

Name your files by track number:

```bash
python lights_tool.py cue your_song.mid -o song001_events.py
```

### Step 3: Configure Song Mapping

Edit `song_config.py`:

```python
SONG_MAPPING = {
    1: "song001_events",  # Track 1 on your player
    2: "song001_events",  # Track 2 also uses same lights
    # Add more...
}
```

### Step 4: Copy to Pico

Copy these files to your Pico:
- `main.py`
- `song_config.py`
- `song001_events.py` (and any other event files)

### Step 5: Play Music!

1. Reset Pico
2. Music plays from SV5W player
3. **Lights automatically sync!**
4. Change songs - lights update automatically

## Effect Cheat Sheet

| Note Length | Effect |
|-------------|--------|
| Super short | strobe |
| 16th note   | flash  |
| 8th note    | pulse  |
| Quarter     | fade   |
| Half note   | hold   |
| Whole+      | wave   |

## Tips

- **Velocity** controls brightness (harder = brighter)
- Export audio and MIDI from **same markers**
- Use `interpret` mode for quick auto shows
- Multiple notes can overlap for complexity

## Troubleshooting

**"ModuleNotFoundError: No module named 'mido'"**
```bash
pip install mido
```

**"Event file not found"**
- Make sure event files are copied to Pico
- Check `song_config.py` has correct mappings

**Lights don't change with songs**
- Wait ~500ms after changing tracks
- Check UART connections (GP8/GP9)
- Verify song mapping in `song_config.py`

**Lights don't sync to music**
- Export audio and MIDI from same position in Logic
- Verify tempo in converter output

## Examples

### Custom show:
```bash
python lights_tool.py cue my_lights.mid -o song001_events.py
```

### Auto show from existing MIDI:
```bash
python lights_tool.py interpret song.mid -o song002_events.py
```

### Multiple songs:
```bash
python lights_tool.py cue track1.mid -o song001_events.py
python lights_tool.py cue track2.mid -o song002_events.py
python lights_tool.py cue track3.mid -o song003_events.py
```

Then edit `song_config.py`:
```python
SONG_MAPPING = {
    1: "song001_events",
    2: "song002_events",
    3: "song003_events",
}
```

## Next Steps

See **LIGHTING_SYSTEM.md** for full documentation.

Happy lighting! 🎵💡

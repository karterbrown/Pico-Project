# Conversion Tools

Mac-side tools for converting MIDI files to LED events.

## Setup (One-Time)

Install required Python library:

```bash
pip install -r requirements.txt
```

This installs `mido` for reading MIDI files.

## Usage

### Convert Custom Lighting Track (Recommended)

When you've created a lighting cue track in Logic Pro:

```bash
python lights_tool.py cue ../midi_sources/00001.mid -o ../pico/00001_events.py
```

**What it does:**
- Reads C1-G1 notes as strip commands
- Converts note length to visual effects
- Uses velocity for brightness
- Preserves musical timing

### Auto-Generate Light Show

When you have existing MIDI and want automatic lighting:

```bash
python lights_tool.py interpret ../midi_sources/00002.mid -o ../pico/00002_events.py
```

**What it does:**
- Analyzes all notes in MIDI
- Spreads notes across strips by pitch
- Auto-assigns effects by note length
- Quick way to add lights to any song

## Command Reference

```bash
# Basic conversion
python lights_tool.py cue input.mid

# Specify output file
python lights_tool.py cue input.mid -o custom_name.py

# Auto-generate mode
python lights_tool.py interpret input.mid -o output.py

# Get help
python lights_tool.py --help
```

## File Naming Convention

Use track numbers in output names for easy organization:

Name your MIDI source files with 5 digits matching the song number on the SD card:

```
00001.mid  →  song for track 00001.mp3
00002.mid  →  song for track 00002.mp3
```

Convert them:
```bash
python lights_tool.py cue 00001.mid -o ../pico/00001_events.py
python lights_tool.py cue 00002.mid -o ../pico/00002_events.py
python lights_tool.py cue 00003.mid -o ../pico/00003_events.py
```

Then in `song_config.py`:
```python
SONG_MAPPING = {
    1: "00001_events",  # Track 00001
    2: "00002_events",  # Track 00002
    3: "00003_events",  # Track 00003
}
```

## Batch Conversion

Convert multiple files at once:

```bash
# Convert tracks 1-10
for i in {1..10}; do
    python lights_tool.py cue $(printf "%05d" $i).mid \
        -o ../pico/$(printf "%05d" $i)_events.py
done
```

## Output

Generated files go to `../pico/` folder and are ready to upload to your Pico!

The converter shows you:
- ✓ Number of events created
- ✓ Detected tempo (BPM)
- ✓ Total duration
- ✓ Events per strip

## Troubleshooting

**"No module named 'mido'"**
```bash
pip install -r requirements.txt
```

**"No notes found"**
- Check your MIDI file has notes
- For cue mode: Make sure you used C1-G1

**"Tempo not detected"**
- Most MIDI files include tempo
- Script uses 120 BPM as default if missing

## Tips

- Always export MIDI from the same cycle region as your audio
- Use descriptive names: `track01_high_energy.mid`
- Test with one song before batch converting
- Re-run converter to update existing light shows

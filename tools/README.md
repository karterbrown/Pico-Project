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
python lights_tool.py cue ../midi_sources/my_song.mid -o ../pico/song001_events.py
```

**What it does:**
- Reads C1-G1 notes as strip commands
- Converts note length to visual effects
- Uses velocity for brightness
- Preserves musical timing

### Auto-Generate Light Show

When you have existing MIDI and want automatic lighting:

```bash
python lights_tool.py interpret ../midi_sources/song.mid -o ../pico/song002_events.py
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

```bash
python lights_tool.py cue track1.mid -o ../pico/song001_events.py
python lights_tool.py cue track2.mid -o ../pico/song002_events.py
python lights_tool.py cue track3.mid -o ../pico/song003_events.py
```

Then in `song_config.py`:
```python
SONG_MAPPING = {
    1: "song001_events",  # Track 1
    2: "song002_events",  # Track 2
    3: "song003_events",  # Track 3
}
```

## Batch Conversion

Convert multiple files at once:

```bash
# Convert tracks 1-10
for i in {1..10}; do
    python lights_tool.py cue ../midi_sources/track${i}.mid \
        -o ../pico/song$(printf "%03d" $i)_events.py
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

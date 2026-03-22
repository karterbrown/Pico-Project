# MIDI Sources Folder

Put your exported MIDI files from Logic Pro here.

## How to Export from Logic Pro

1. Set your cycle region (locators) around your song section
2. **File → Export → Selection as MIDI File**
3. Save here with descriptive names like:
   - `track01_upbeat_dance.mid`
   - `track02_chill_vibes.mid`
   - `track03_rock_anthem.mid`

## Then Convert Them

From the `tools` folder:

```bash
cd ../tools

# Convert custom lighting track
python lights_tool.py cue ../midi_sources/track01_upbeat_dance.mid -o ../pico/song001_events.py

# Or auto-generate from existing MIDI
python lights_tool.py interpret ../midi_sources/song.mid -o ../pico/song002_events.py
```

## Organization Tips

Name your files to match your SD card track order:
- `track01_xxx.mid` → converts to → `song001_events.py`
- `track02_xxx.mid` → converts to → `song002_events.py`
- etc.

This makes it easy to remember which MIDI belongs to which track!

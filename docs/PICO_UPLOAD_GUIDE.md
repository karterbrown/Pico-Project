# Pico Upload Folder

These files get uploaded to your Raspberry Pi Pico.

## Files in This Folder

### Core Files (Always upload)
- **main.py** - Main lighting controller program
- **song_config.py** - Maps track numbers to light shows

### Event Files (Upload as you create them)
- **events.py** - Demo light show (works with any song)
- **song001_events.py** - Light show for track 1
- **song002_events.py** - Light show for track 2
- **song003_events.py** - Light show for track 3
- (add more as you create them)

### Example Files (Reference only)
- **song_config_example.py** - Example configurations (don't upload)

## How to Upload

### Using VS Code + MicroPico

**Option 1: Select Multiple**
1. Cmd+Click (Mac) or Ctrl+Click (Windows) to select:
   - main.py
   - song_config.py
   - events.py
   - any songXXX_events.py files
2. Right-click → "Upload to Pico"

**Option 2: Upload All**
1. Right-click on the `pico` folder
2. "Upload project to Pico"
3. Only .py files upload

### Using Thonny
1. View → Files
2. Drag files from left (Mac) to right (Pico)

## After Uploading

1. Reset your Pico
2. Play music from SV5W player
3. Lights automatically sync to each song!

## Adding New Songs

When you create a new light show:

1. Convert MIDI: `python lights_tool.py cue file.mid -o songXXX_events.py`
2. File appears here in `/pico/` folder
3. Add to `song_config.py`:
   ```python
   SONG_MAPPING = {
       1: "song001_events",
       2: "song002_events",
       3: "songXXX_events",  # Your new one
   }
   ```
4. Upload the new `songXXX_events.py` to Pico
5. Done!

## Tips

- Start with just `main.py`, `song_config.py`, and `events.py` to test
- Add your custom event files one at a time
- Keep file names organized: song001, song002, song003, etc.
- If you update a light show, just re-upload that one event file

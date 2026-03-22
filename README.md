# Pico Auto-Sync Lighting System

Auto-sync LED light shows to songs playing from your Raspberry Pi Pico music player.

## 📁 Project Structure

```
Pico-Project/
├── pico/                     # ⚡ UPLOAD THIS FOLDER TO PICO
│   ├── main.py              # Main lighting controller
│   ├── song_config.py       # Song-to-lightshow mapping
│   ├── events.py            # Demo light show
│   └── song0XX_events.py    # Your custom light shows (add as created)
│
├── tools/                    # Mac-side conversion tools
│   ├── lights_tool.py       # MIDI → events converter
│   └── requirements.txt     # Python dependencies
│
├── midi_sources/             # Your MIDI exports from Logic Pro
│   └── (put your .mid files here)
│
├── docs/                     # Documentation & guides
│   ├── PICO_UPLOAD_GUIDE.md
│   ├── SONG_CONFIG_EXAMPLES.md
│   ├── AUTO_SYNC_README.md
│   ├── LIGHTING_SYSTEM.md
│   └── QUICKSTART.md
│
└── (project files)           # Build diagrams, deploy scripts, etc.
```

## 🚀 Quick Start

### 1. Install Tools (Mac)
```bash
cd tools
pip install -r requirements.txt
```

### 2. Create Light Show in Logic Pro
1. Open Logic Pro
2. Import song
3. Create MIDI track "LIGHTING CUES"
4. Use C1-G1 notes for strips 0-4
5. Export MIDI to `midi_sources/`

### 3. Convert MIDI
```bash
cd tools
python lights_tool.py cue ../midi_sources/my_song.mid -o ../pico/song001_events.py
```

### 4. Configure Mapping
Edit `pico/song_config.py`:
```python
SONG_MAPPING = {
    1: "song001_events",  # Track 1 on SD card
    2: "song002_events",  # Track 2 on SD card
}
```

### 5. Upload to Pico

**Upload the entire `pico/` folder:**
- Everything in that folder goes to your Pico
- No other files needed!

**VS Code Method:**
1. Right-click on `pico/` folder
2. "Upload project to Pico"

**Or select individual files:**
1. Cmd+Click all .py files in `pico/`
2. Right-click → "Upload to Pico"

### 6. Enjoy!
Play music → Lights auto-sync! 🎉

## 📖 Documentation

See the [docs folder](docs/) for complete guides:

- **[QUICKSTART.md](docs/QUICKSTART.md)** - Get started fast
- **[AUTO_SYNC_README.md](docs/AUTO_SYNC_README.md)** - Complete system guide  
- **[LIGHTING_SYSTEM.md](docs/LIGHTING_SYSTEM.md)** - In-depth documentation
- **[PICO_UPLOAD_GUIDE.md](docs/PICO_UPLOAD_GUIDE.md)** - Upload instructions
- **[SONG_CONFIG_EXAMPLES.md](docs/SONG_CONFIG_EXAMPLES.md)** - Configuration examples

## 🎮 Hardware

- Raspberry Pi Pico
- 5 × WS2812B LED strips (GP0-GP4)
- SV5W audio player (UART GP8/GP9)
- Control buttons (GP16-GP21)

## 💡 Workflow

```
Logic Pro → Export MIDI → Convert → Upload to Pico → Auto-Sync!
```

---

**Need help?** Check the [docs folder](docs/) for detailed guides!

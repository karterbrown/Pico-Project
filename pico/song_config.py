# Song to Light Show Mapping Configuration
# 
# Maps song track numbers to their corresponding event files
# 
# Format: song_number: "event_filename" (without .py extension)
# 
# Example:
#   1: "song001_events"    # Track 1 uses song001_events.py
#   2: "song002_events"    # Track 2 uses song002_events.py
#   3: "default_events"    # Track 3 uses default_events.py
#
# You can use the same event file for multiple songs:
#   4: "default_events"
#   5: "default_events"
#
# Or use None for songs that should have no lights:
#   6: None

SONG_MAPPING = {
    # Default mapping - all songs use the demo events
    # Add your custom mappings here after generating event files
    1: "events",      # Track 1 → events.py (demo)
    2: "events",      # Track 2 → events.py (demo)
    3: "events",      # Track 3 → events.py (demo)
    4: "events",      # Track 4 → events.py (demo)
    5: "events",      # Track 5 → events.py (demo)
    # Add more mappings as needed
}

# Default event file to use if song number not found in mapping
# Set to None to disable lights for unmapped songs
DEFAULT_EVENTS = "events"


def get_events_for_song(song_number):
    """
    Get the event module name for a given song number
    
    Args:
        song_number: Track number from SV5W player
        
    Returns:
        String module name (without .py), or None if no lights for this song
    """
    if song_number in SONG_MAPPING:
        return SONG_MAPPING[song_number]
    return DEFAULT_EVENTS

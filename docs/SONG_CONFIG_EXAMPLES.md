# Example Song Configuration
# Copy this to song_config.py and customize for your playlist

# Basic mapping - each track has its own light show
SONG_MAPPING = {
    1: "song001_events",   # Track 1: Custom light show
    2: "song002_events",   # Track 2: Different light show
    3: "song003_events",   # Track 3: Another unique show
}

# Sharing patterns - multiple songs use same lights
# SONG_MAPPING = {
#     1: "upbeat_pattern",
#     2: "upbeat_pattern",
#     3: "slow_pattern",
#     4: "slow_pattern",
#     5: "upbeat_pattern",
# }

# Mixed approach - some unique, some shared, some none
# SONG_MAPPING = {
#     1: "song001_events",  # Unique light show
#     2: "default_pattern", # Shares with others
#     3: "default_pattern", # Shares with others
#     4: None,              # No lights for this song
#     5: "song005_events",  # Unique light show
#     6: "default_pattern", # Shares with others
# }

# Default for unmapped songs
DEFAULT_EVENTS = "events"

def get_events_for_song(song_number):
    """Get the event module name for a given song number"""
    if song_number in SONG_MAPPING:
        return SONG_MAPPING[song_number]
    return DEFAULT_EVENTS

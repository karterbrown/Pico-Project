#!/usr/bin/env python3
"""
MIDI to LED Lighting Events Converter
Converts MIDI files to lighting event data for Raspberry Pi Pico LED controller

Two modes:
1. cue: Convert custom MIDI lighting tracks (C1-G1 mapping)
2. interpret: Auto-generate light show from existing MIDI note data
"""

import sys
import argparse
import os
import struct
from mido import MidiFile, tempo2bpm
from typing import List, Tuple, Optional

# Effect index mapping (must match pico/main.py EFFECTS list)
EFFECTS = ["strobe", "flash", "pulse", "fade", "hold", "wave"]
RECORD_SIZE = 12  # bytes per event: uint32 time_ms + uint8 strip + uint8 brightness + uint8 effect_idx + uint8 led_pos + uint32 duration_ms

# Paths relative to the project root (one level up from tools/)
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TOOLS_DIR)
MIDI_SOURCES_DIR = os.path.join(PROJECT_ROOT, "midi_sources")
PICO_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "pico")


def determine_effect(duration_beats: float) -> str:
    """
    Determine effect type based on note duration in beats
    
    Args:
        duration_beats: Note duration in beats
        
    Returns:
        Effect name (strobe, flash, pulse, fade, hold, wave)
    """
    if duration_beats < 0.25:
        return "strobe"
    elif duration_beats < 0.5:
        return "flash"
    elif duration_beats < 1.0:
        return "pulse"
    elif duration_beats < 2.0:
        return "fade"
    elif duration_beats < 4.0:
        return "hold"
    else:
        return "wave"


def velocity_to_brightness(velocity: int) -> int:
    """Convert MIDI velocity (0-127) to LED brightness (0-255)"""
    return int((velocity / 127.0) * 255)


def convert_cue_mode(midi_file: MidiFile) -> List[Tuple[int, int, int, str, int]]:
    """
    Convert custom MIDI lighting cue track to events
    
    Maps specific notes (C1-G1) to LED strips with intended effects
    
    Args:
        midi_file: Loaded MIDI file
        
    Returns:
        List of events: (time_ms, strip_index, brightness, effect, duration_ms)
    """
    # Note name to strip mapping (MIDI note numbers for C1-G1)
    NOTE_TO_STRIP = {
        24: 0,  # C1 -> Strip 0
        26: 1,  # D1 -> Strip 1
        28: 2,  # E1 -> Strip 2
        29: 3,  # F1 -> Strip 3
        31: 4,  # G1 -> Strip 4
    }
    
    events = []
    active_notes = {}  # Track note_on events waiting for note_off
    
    # Get tempo and ticks per beat
    ticks_per_beat = midi_file.ticks_per_beat
    current_tempo = 500000  # Default: 120 BPM
    
    # Process all tracks
    current_tick = 0
    
    for track in midi_file.tracks:
        current_tick = 0
        
        for msg in track:
            current_tick += msg.time
            
            # Update tempo if tempo change message
            if msg.type == 'set_tempo':
                current_tempo = msg.tempo
                
            # Handle note_on events
            elif msg.type == 'note_on' and msg.velocity > 0:
                if msg.note in NOTE_TO_STRIP:
                    # Store note_on info
                    key = (msg.note, msg.channel)
                    active_notes[key] = {
                        'tick': current_tick,
                        'velocity': msg.velocity
                    }
                    
            # Handle note_off events (or note_on with velocity 0)
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if msg.note in NOTE_TO_STRIP:
                    key = (msg.note, msg.channel)
                    
                    if key in active_notes:
                        note_start = active_notes[key]
                        
                        # Calculate timing
                        start_tick = note_start['tick']
                        end_tick = current_tick
                        duration_ticks = end_tick - start_tick
                        
                        # Convert to milliseconds
                        ms_per_tick = (current_tempo / 1000000.0) / ticks_per_beat
                        start_ms = int(start_tick * ms_per_tick * 1000)
                        duration_ms = int(duration_ticks * ms_per_tick * 1000)
                        
                        # Calculate duration in beats for effect selection
                        duration_beats = duration_ticks / ticks_per_beat
                        
                        # Determine effect
                        effect = determine_effect(duration_beats)
                        
                        # Get strip and brightness
                        strip_index = NOTE_TO_STRIP[msg.note]
                        brightness = velocity_to_brightness(note_start['velocity'])
                        
                        # Add event
                        events.append((start_ms, strip_index, brightness, effect, duration_ms))
                        
                        # Remove from active notes
                        del active_notes[key]
    
    # Sort events by time
    events.sort(key=lambda x: x[0])
    
    return events


def convert_interpret_mode(midi_file: MidiFile) -> List[Tuple[int, int, int, str, int]]:
    """
    Interpret existing MIDI song data to auto-generate light show
    
    Distributes notes across strips based on pitch range
    
    Args:
        midi_file: Loaded MIDI file
        
    Returns:
        List of events: (time_ms, strip_index, brightness, effect, duration_ms)
    """
    events = []
    active_notes = {}
    
    # Get tempo and ticks per beat
    ticks_per_beat = midi_file.ticks_per_beat
    current_tempo = 500000  # Default: 120 BPM
    
    # First pass: find note range for pitch mapping
    all_note_numbers = []
    
    for track in midi_file.tracks:
        for msg in track:
            if msg.type == 'note_on' and msg.velocity > 0:
                all_note_numbers.append(msg.note)
    
    if not all_note_numbers:
        print("Warning: No notes found in MIDI file")
        return events
    
    min_note = min(all_note_numbers)
    max_note = max(all_note_numbers)
    note_range = max_note - min_note if max_note > min_note else 1

    # Round-robin strip counter — guarantees equal event counts across all 5 strips
    _strip_counter = [0]

    def note_to_strip() -> int:
        """Assign strips round-robin by event order for perfectly even distribution"""
        idx = _strip_counter[0] % 5
        _strip_counter[0] += 1
        return idx

    def note_to_led_pos(note_number: int) -> int:
        """Map note pitch to LED position (0-19) using global note range"""
        pos = (note_number - min_note) / note_range
        return max(0, min(19, int(pos * 19.999)))
    
    # Second pass: process events
    current_tick = 0
    
    for track in midi_file.tracks:
        current_tick = 0
        
        for msg in track:
            current_tick += msg.time
            
            # Update tempo
            if msg.type == 'set_tempo':
                current_tempo = msg.tempo
                
            # Handle note_on
            elif msg.type == 'note_on' and msg.velocity > 0:
                key = (msg.note, msg.channel)
                active_notes[key] = {
                    'tick': current_tick,
                    'velocity': msg.velocity
                }
                
            # Handle note_off
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                key = (msg.note, msg.channel)
                
                if key in active_notes:
                    note_start = active_notes[key]
                    
                    # Calculate timing
                    start_tick = note_start['tick']
                    end_tick = current_tick
                    duration_ticks = end_tick - start_tick
                    
                    # Convert to milliseconds
                    ms_per_tick = (current_tempo / 1000000.0) / ticks_per_beat
                    start_ms = int(start_tick * ms_per_tick * 1000)
                    duration_ms = int(duration_ticks * ms_per_tick * 1000)
                    
                    # Calculate duration in beats
                    duration_beats = duration_ticks / ticks_per_beat
                    
                    # Determine effect
                    effect = determine_effect(duration_beats)
                    
                    # Map note to strip (round-robin) and LED position (pitch-based)
                    strip_index = note_to_strip()
                    led_pos = note_to_led_pos(msg.note)

                    # Get brightness
                    brightness = velocity_to_brightness(note_start['velocity'])

                    # Add event with led_pos
                    events.append((start_ms, strip_index, brightness, effect, duration_ms, led_pos))

                    del active_notes[key]
    
    # Sort events by time
    events.sort(key=lambda x: x[0])
    
    return events


def clean_events(events: List[Tuple[int, int, int, str, int]]) -> List[Tuple[int, int, int, str, int]]:
    """
    Clean and optimize event list
    
    - Clamp brightness values
    - Sort by time
    - Remove duplicates
    
    Args:
        events: Raw event list
        
    Returns:
        Cleaned event list
    """
    cleaned = []
    
    for event in events:
        time_ms, strip_index, brightness, effect, duration_ms = event[:5]
        led_pos = event[5] if len(event) > 5 else 255

        # Clamp brightness
        brightness = max(0, min(255, brightness))

        # Ensure valid strip index
        strip_index = max(0, min(4, strip_index))

        # Ensure positive duration
        duration_ms = max(10, duration_ms)

        cleaned.append((time_ms, strip_index, brightness, effect, duration_ms, led_pos))
    
    # Sort by time
    cleaned.sort(key=lambda x: x[0])
    
    return cleaned


def export_events_binary(events: List[Tuple], output_file: str):
    """
    Export events as compact binary file for memory-efficient Pico streaming.
    Format per record (12 bytes): uint32 time_ms, uint8 strip, uint8 brightness,
                                   uint8 effect_idx, uint8 led_pos, uint32 duration_ms
    """
    with open(output_file, 'wb') as f:
        for event in events:
            time_ms, strip_index, brightness, effect, duration_ms = event[:5]
            led_pos = event[5] if len(event) > 5 else 255  # 255 = fill whole strip
            effect_idx = EFFECTS.index(effect) if effect in EFFECTS else 1
            f.write(struct.pack('<IBBBBI', time_ms, strip_index, brightness, effect_idx, led_pos, duration_ms))

    size_kb = os.path.getsize(output_file) / 1024
    print(f"✓ Exported {len(events)} events to {output_file} ({size_kb:.1f} KB)")


def get_tempo_bpm(midi_file: MidiFile) -> float:
    """Extract tempo from MIDI file"""
    for track in midi_file.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                return tempo2bpm(msg.tempo)
    return 120.0  # Default


def get_duration_ms(midi_file: MidiFile) -> int:
    """Calculate total duration of MIDI file in milliseconds"""
    ticks_per_beat = midi_file.ticks_per_beat
    current_tempo = 500000
    total_ticks = 0
    
    for track in midi_file.tracks:
        current_tick = 0
        for msg in track:
            current_tick += msg.time
            if msg.type == 'set_tempo':
                current_tempo = msg.tempo
        total_ticks = max(total_ticks, current_tick)
    
    ms_per_tick = (current_tempo / 1000000.0) / ticks_per_beat
    return int(total_ticks * ms_per_tick * 1000)


def main():
    parser = argparse.ArgumentParser(
        description='Convert MIDI files to LED lighting events',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s cue my_lights.mid
  %(prog)s interpret song.mid
  %(prog)s cue my_lights.mid --output my_events.py
        '''
    )
    
    parser.add_argument('mode', choices=['cue', 'interpret'],
                        help='cue: custom lighting track | interpret: auto-generate from notes')
    parser.add_argument('input', help='Input MIDI file or 5-digit song number (e.g. 00001)')
    parser.add_argument('--output', '-o', default=None,
                        help='Output .py file (default: pico/<number>_events.py)')
    parser.add_argument('--offset', type=int, default=0,
                        help='Shift all events forward by this many milliseconds (pre-roll buffer)')
    parser.add_argument('--bars', type=float, default=0,
                        help='Shift all events forward by this many bars (calculated from MIDI tempo)')

    args = parser.parse_args()

    # Resolve input path - if just a number, look in midi_sources/
    input_path = args.input
    if not os.path.exists(input_path):
        # Try treating it as a 5-digit number
        padded = args.input.zfill(5)
        candidate = os.path.join(MIDI_SOURCES_DIR, f"{padded}.mid")
        if os.path.exists(candidate):
            input_path = candidate
        else:
            print(f"Error: could not find '{args.input}' or '{candidate}'")
            return 1

    # Resolve output path - default to pico/<number>.bin
    if args.output:
        output_path = args.output
    else:
        basename = os.path.splitext(os.path.basename(input_path))[0].zfill(5)
        output_path = os.path.join(PICO_OUTPUT_DIR, f"{basename}.bin")
        os.makedirs(PICO_OUTPUT_DIR, exist_ok=True)

    # Load MIDI file
    try:
        print(f"Loading MIDI file: {input_path}")
        midi_file = MidiFile(input_path)
    except Exception as e:
        print(f"Error loading MIDI file: {e}")
        return 1

    # Get MIDI info
    tempo_bpm = get_tempo_bpm(midi_file)
    duration_ms = get_duration_ms(midi_file)

    print(f"Tempo: {tempo_bpm:.1f} BPM")
    print(f"Duration: {duration_ms / 1000:.2f} seconds")
    print(f"Mode: {args.mode}")

    # Convert based on mode
    if args.mode == 'cue':
        print("\nConverting custom lighting cue track...")
        print("Note mapping: C1→Strip0, D1→Strip1, E1→Strip2, F1→Strip3, G1→Strip4")
        events = convert_cue_mode(midi_file)
    else:  # interpret
        print("\nInterpreting MIDI notes as auto light show...")
        events = convert_interpret_mode(midi_file)

    # Clean events
    events = clean_events(events)

    # Apply offset (pre-roll buffer)
    offset_ms = args.offset
    if args.bars > 0:
        beats_per_bar = 4  # 4/4 time
        ms_per_beat = (60.0 / tempo_bpm) * 1000
        offset_ms += int(args.bars * beats_per_bar * ms_per_beat)
        print(f"\nBar offset: {args.bars} bars @ {tempo_bpm:.1f} BPM = {offset_ms}ms")

    if offset_ms > 0:
        events = [(e[0] + offset_ms,) + e[1:] for e in events]
        print(f"Applied offset: +{offset_ms}ms to all events")

    # Export as binary
    export_events_binary(events, output_path)

    # Summary
    base = os.path.splitext(os.path.basename(output_path))[0].replace('_events', '')
    print(f"\nSummary:")
    print(f"  Events generated: {len(events)}")
    print(f"  Output file: {output_path}")
    print(f"\nReminder: SD card MP3 should be named {base}.mp3")
    print(f"  5-digit format required: e.g. 00001.mp3, 00002.mp3")

    if events:
        print(f"  First event at: {events[0][0]} ms")
        print(f"  Last event at: {events[-1][0]} ms")
        
        # Count events per strip
        strip_counts = {i: 0 for i in range(5)}
        for event in events:
            strip_counts[event[1]] += 1
        
        print(f"\n  Events per strip:")
        for strip, count in strip_counts.items():
            print(f"    Strip {strip}: {count}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

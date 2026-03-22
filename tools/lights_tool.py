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
from mido import MidiFile, tempo2bpm
from typing import List, Tuple, Optional


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
    
    def note_to_strip(note_number: int) -> int:
        """Map note pitch to strip (0-4) based on range"""
        if note_range == 0:
            return 2  # Middle strip if all notes are same
        
        # Normalize to 0-1, then scale to 0-4
        normalized = (note_number - min_note) / note_range
        strip = int(normalized * 4.999)  # Maps to 0-4
        return max(0, min(4, strip))
    
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
                    
                    # Map note to strip
                    strip_index = note_to_strip(msg.note)
                    
                    # Get brightness
                    brightness = velocity_to_brightness(note_start['velocity'])
                    
                    # Add event
                    events.append((start_ms, strip_index, brightness, effect, duration_ms))
                    
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
    
    for time_ms, strip_index, brightness, effect, duration_ms in events:
        # Clamp brightness
        brightness = max(0, min(255, brightness))
        
        # Ensure valid strip index
        strip_index = max(0, min(4, strip_index))
        
        # Ensure positive duration
        duration_ms = max(10, duration_ms)
        
        cleaned.append((time_ms, strip_index, brightness, effect, duration_ms))
    
    # Sort by time
    cleaned.sort(key=lambda x: x[0])
    
    return cleaned


def export_events(events: List[Tuple[int, int, int, str, int]], output_file: str):
    """
    Export events to Python file for Pico
    
    Args:
        events: Event list
        output_file: Output filename
    """
    with open(output_file, 'w') as f:
        f.write('# LED Lighting Events\n')
        f.write('# Format: (time_ms, strip_index, brightness, effect, duration_ms)\n')
        f.write('# Effects: strobe, flash, pulse, fade, hold, wave\n\n')
        f.write('events = [\n')
        
        for event in events:
            f.write(f'    {event},\n')
        
        f.write(']\n')
    
    print(f"✓ Exported {len(events)} events to {output_file}")


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
    parser.add_argument('input', help='Input MIDI file')
    parser.add_argument('--output', '-o', default='events.py',
                        help='Output Python file (default: events.py)')
    
    args = parser.parse_args()
    
    # Load MIDI file
    try:
        print(f"Loading MIDI file: {args.input}")
        midi_file = MidiFile(args.input)
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
    
    # Export
    export_events(events, args.output)
    
    # Summary
    print(f"\nSummary:")
    print(f"  Events generated: {len(events)}")
    print(f"  Output file: {args.output}")
    
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

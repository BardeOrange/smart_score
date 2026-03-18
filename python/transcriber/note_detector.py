import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


# All musical note names
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# A4 = 440 Hz (standard tuning)
A4_FREQ = 440.0
A4_MIDI = 69


@dataclass
class Note:
    """Represents a detected musical note."""
    name: str          # e.g., "C#4"
    pitch: str         # e.g., "C#"
    octave: int        # e.g., 4
    midi_number: int   # e.g., 61
    frequency: float   # e.g., 277.18 Hz
    start_time: float  # seconds
    duration: float    # seconds
    velocity: int      # 0-127 (loudness)

    def __str__(self):
        return f"{self.name} ({self.frequency:.1f}Hz) [{self.start_time:.2f}s - {self.start_time + self.duration:.2f}s]"


def freq_to_midi(frequency: float) -> int:
    """Convert frequency (Hz) to MIDI note number."""
    if frequency <= 0:
        return 0
    return int(round(69 + 12 * np.log2(frequency / A4_FREQ)))


def midi_to_freq(midi_number: int) -> float:
    """Convert MIDI note number to frequency (Hz)."""
    return A4_FREQ * (2 ** ((midi_number - A4_MIDI) / 12.0))


def midi_to_note_name(midi_number: int) -> Tuple[str, str, int]:
    """
    Convert MIDI number to note name.
    Returns: (full_name, pitch, octave)
    Example: (69) → ("A4", "A", 4)
    """
    if midi_number < 0 or midi_number > 127:
        return ("?", "?", 0)

    octave = (midi_number // 12) - 1
    pitch = NOTE_NAMES[midi_number % 12]
    full_name = f"{pitch}{octave}"
    return full_name, pitch, octave


def freq_to_note_name(frequency: float) -> Tuple[str, str, int]:
    """
    Convert frequency to note name.
    Example: 440.0 → ("A4", "A", 4)
    """
    midi = freq_to_midi(frequency)
    return midi_to_note_name(midi)


class NoteDetector:
    """
    Detects musical notes from audio analysis data.
    Converts raw frequencies and onset times into Note objects.
    """

    def __init__(
        self,
        min_note_duration: float = 0.05,
        min_frequency: float = 50.0,
        max_frequency: float = 4200.0,
        energy_threshold: float = 0.0001
    ):

        """
        Args:
            min_note_duration: Minimum note length in seconds
            min_frequency: Lowest detectable frequency (Hz)
            max_frequency: Highest detectable frequency (Hz)
            energy_threshold: Minimum energy to consider a note
        """
        self.min_note_duration = min_note_duration
        self.min_frequency = min_frequency
        self.max_frequency = max_frequency
        self.energy_threshold = energy_threshold

    def detect_notes(
        self,
        pitches: List[float],
        energies: List[float],
        onset_frames: List[int],
        sample_rate: float,
        hop_size: int
    ) -> List[Note]:
        """
        Detect notes from pitch and onset data.

        Args:
            pitches: Detected frequency at each frame
            energies: Energy/loudness at each frame
            onset_frames: Frame indices where notes start
            sample_rate: Audio sample rate
            hop_size: Spectrogram hop size

        Returns:
            List of detected Note objects
        """
        notes = []
        frame_duration = hop_size / sample_rate

        # If no onsets detected, try to find stable pitch regions
        if not onset_frames:
            onset_frames = self._find_stable_regions(pitches, energies)

        for i, onset in enumerate(onset_frames):
            # Determine note end (next onset or end of audio)
            if i + 1 < len(onset_frames):
                end_frame = onset_frames[i + 1]
            else:
                end_frame = len(pitches)

            # Skip if segment too short
            duration = (end_frame - onset) * frame_duration
            if duration < self.min_note_duration:
                continue

            # Get average pitch and energy for this segment
            segment_pitches = pitches[onset:end_frame]
            segment_energies = energies[onset:end_frame]

            if not segment_pitches:
                continue

            # Filter out silent/invalid frames
            valid = [
                (p, e) for p, e in zip(segment_pitches, segment_energies)
                if self.min_frequency <= p <= self.max_frequency
                and e > self.energy_threshold
            ]

            if not valid:
                continue

            valid_pitches, valid_energies = zip(*valid)

            # Use median pitch (more robust than mean)
            frequency = float(np.median(valid_pitches))
            avg_energy = float(np.mean(valid_energies))

            # Convert to note
            midi_number = freq_to_midi(frequency)
            full_name, pitch, octave = midi_to_note_name(midi_number)

            # Map energy to MIDI velocity (0-127)
            velocity = min(127, max(30, int(avg_energy * 1000)))

            note = Note(
                name=full_name,
                pitch=pitch,
                octave=octave,
                midi_number=midi_number,
                frequency=frequency,
                start_time=onset * frame_duration,
                duration=duration,
                velocity=velocity
            )
            notes.append(note)

        return notes

    def _find_stable_regions(
        self,
        pitches: List[float],
        energies: List[float]
    ) -> List[int]:
        """
        Find regions where pitch is stable (fallback if no onsets detected).
        """
        if len(pitches) < 2:
            return [0] if pitches else []

        onsets = [0]  # Start with first frame

        for i in range(1, len(pitches)):
            # Detect pitch change
            if pitches[i] > 0 and pitches[i - 1] > 0:
                ratio = pitches[i] / pitches[i - 1]
                # More than a semitone change
                if ratio > 1.06 or ratio < 0.94:
                    onsets.append(i)
            # Detect silence to sound transition
            elif pitches[i] > 0 and pitches[i - 1] == 0:
                onsets.append(i)

        return onsets
import numpy as np
from typing import List, Optional, Tuple
from dataclasses import dataclass

from python.transcriber.note_detector import Note


# Standard note durations (in beats)
DURATION_MAP = {
    "whole": 4.0,
    "half": 2.0,
    "quarter": 1.0,
    "eighth": 0.5,
    "sixteenth": 0.25,
    "dotted_half": 3.0,
    "dotted_quarter": 1.5,
    "dotted_eighth": 0.75,
}


@dataclass
class TimedNote:
    """A note with rhythmic information."""
    note: Note
    beat_duration: float     # Duration in beats
    duration_name: str       # e.g., "quarter", "half"
    measure: int             # Which measure (bar) it's in
    beat_position: float     # Position within the measure


class RhythmAnalyzer:
    """
    Analyzes rhythm: tempo detection, beat quantization,
    and note duration assignment.
    """

    def __init__(
        self,
        default_tempo: float = 120.0,
        time_signature: Tuple[int, int] = (4, 4)
    ):
        """
        Args:
            default_tempo: Default BPM if detection fails
            time_signature: (beats_per_measure, beat_unit)
        """
        self.default_tempo = default_tempo
        self.beats_per_measure = time_signature[0]
        self.beat_unit = time_signature[1]

    def estimate_tempo(self, notes: List[Note]) -> float:
        """
        Estimate tempo (BPM) from note onset times.
        Uses inter-onset intervals.
        """
        if len(notes) < 3:
            print(f"⚠️ Too few notes for tempo detection, using default: {self.default_tempo} BPM")
            return self.default_tempo

        # Calculate inter-onset intervals
        intervals = []
        for i in range(1, len(notes)):
            interval = notes[i].start_time - notes[i - 1].start_time
            if 0.1 < interval < 2.0:  # Reasonable range
                intervals.append(interval)

        if not intervals:
            return self.default_tempo

        # Use median interval as the beat duration
        median_interval = float(np.median(intervals))

        # Convert to BPM
        bpm = 60.0 / median_interval

        # Snap to common tempos
        bpm = self._snap_tempo(bpm)

        print(f"🎵 Detected tempo: {bpm:.0f} BPM")
        return bpm

    def _snap_tempo(self, bpm: float) -> float:
        """Snap tempo to nearest common value if close."""
        common_tempos = [60, 72, 80, 90, 100, 108, 112, 120, 132, 140, 160, 180]

        for tempo in common_tempos:
            if abs(bpm - tempo) < 5:
                return float(tempo)

        return round(bpm)

    def quantize_notes(
        self,
        notes: List[Note],
        tempo: Optional[float] = None
    ) -> List[TimedNote]:
        """
        Assign rhythmic values to notes.

        Args:
            notes: Detected notes
            tempo: BPM (auto-detected if None)

        Returns:
            List of TimedNote with rhythm information
        """
        if not notes:
            return []

        if tempo is None:
            tempo = self.estimate_tempo(notes)

        beat_duration = 60.0 / tempo  # Duration of one beat in seconds
        measure_duration = beat_duration * self.beats_per_measure

        timed_notes = []

        for note in notes:
            # Convert duration to beats
            beats = note.duration / beat_duration

            # Quantize to nearest standard duration
            beat_duration_quantized, duration_name = self._quantize_duration(beats)

            # Calculate measure and beat position
            measure = int(note.start_time / measure_duration) + 1
            beat_position = (note.start_time % measure_duration) / beat_duration

            timed_note = TimedNote(
                note=note,
                beat_duration=beat_duration_quantized,
                duration_name=duration_name,
                measure=measure,
                beat_position=round(beat_position, 2)
            )
            timed_notes.append(timed_note)

        return timed_notes

    def _quantize_duration(self, beats: float) -> Tuple[float, str]:
        """
        Snap a duration in beats to the nearest standard note duration.
        Returns: (quantized_beats, duration_name)
        """
        best_name = "quarter"
        best_duration = 1.0
        best_diff = float("inf")

        for name, duration in DURATION_MAP.items():
            diff = abs(beats - duration)
            if diff < best_diff:
                best_diff = diff
                best_name = name
                best_duration = duration

        return best_duration, best_name

    def get_tempo(self, notes: List[Note]) -> float:
        """Get detected tempo."""
        return self.estimate_tempo(notes)

    def print_rhythm_analysis(
        self,
        timed_notes: List[TimedNote],
        tempo: float
    ) -> None:
        """Pretty print the rhythm analysis."""
        print(f"\n{'=' * 60}")
        print(f"  🎵 Rhythm Analysis")
        print(f"  Tempo: {tempo:.0f} BPM")
        print(f"  Time Signature: {self.beats_per_measure}/{self.beat_unit}")
        print(f"{'=' * 60}")

        current_measure = 0
        for tn in timed_notes:
            if tn.measure != current_measure:
                current_measure = tn.measure
                print(f"\n  Measure {current_measure}:")

            print(
                f"    Beat {tn.beat_position:>5.2f}: "
                f"{tn.note.name:<5} "
                f"({tn.duration_name:<16}) "
                f"[{tn.beat_duration:.2f} beats]"
            )
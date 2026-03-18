import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.transcriber.note_detector import Note
from python.transcriber.rhythm import RhythmAnalyzer, TimedNote


# Helper to create test notes
def make_note(start_time: float, duration: float, name: str = "C4") -> Note:
    return Note(
        name=name,
        pitch="C",
        octave=4,
        midi_number=60,
        frequency=261.63,
        start_time=start_time,
        duration=duration,
        velocity=80
    )


class TestTempoEstimation:
    def setup_method(self):
        self.analyzer = RhythmAnalyzer()

    def test_120_bpm(self):
        """Notes every 0.5s = 120 BPM."""
        notes = [make_note(i * 0.5, 0.4) for i in range(8)]
        tempo = self.analyzer.estimate_tempo(notes)
        assert abs(tempo - 120) < 10

    def test_60_bpm(self):
        """Notes every 1.0s = 60 BPM."""
        notes = [make_note(i * 1.0, 0.8) for i in range(8)]
        tempo = self.analyzer.estimate_tempo(notes)
        assert abs(tempo - 60) < 10

    def test_too_few_notes(self):
        """Should use default tempo with < 3 notes."""
        notes = [make_note(0, 1.0)]
        tempo = self.analyzer.estimate_tempo(notes)
        assert tempo == 120.0  # Default

    def test_empty_notes(self):
        """Should use default tempo with empty list."""
        tempo = self.analyzer.estimate_tempo([])
        assert tempo == 120.0


class TestQuantization:
    def setup_method(self):
        self.analyzer = RhythmAnalyzer()

    def test_quarter_note(self):
        """A note lasting one beat at 120 BPM (0.5s)."""
        notes = [make_note(0, 0.5)]
        timed = self.analyzer.quantize_notes(notes, tempo=120)
        assert len(timed) == 1
        assert timed[0].duration_name == "quarter"
        assert timed[0].beat_duration == 1.0

    def test_half_note(self):
        """A note lasting two beats at 120 BPM (1.0s)."""
        notes = [make_note(0, 1.0)]
        timed = self.analyzer.quantize_notes(notes, tempo=120)
        assert timed[0].duration_name == "half"
        assert timed[0].beat_duration == 2.0

    def test_eighth_note(self):
        """A note lasting half a beat at 120 BPM (0.25s)."""
        notes = [make_note(0, 0.25)]
        timed = self.analyzer.quantize_notes(notes, tempo=120)
        assert timed[0].duration_name == "eighth"
        assert timed[0].beat_duration == 0.5

    def test_measure_assignment(self):
        """Notes should be assigned to correct measures."""
        # At 120 BPM, 4/4 time: measure = 2 seconds
        notes = [
            make_note(0.0, 0.5),   # Measure 1
            make_note(0.5, 0.5),   # Measure 1
            make_note(2.0, 0.5),   # Measure 2
            make_note(4.0, 0.5),   # Measure 3
        ]
        timed = self.analyzer.quantize_notes(notes, tempo=120)
        assert timed[0].measure == 1
        assert timed[1].measure == 1
        assert timed[2].measure == 2
        assert timed[3].measure == 3

    def test_empty_notes(self):
        """Should return empty list for empty input."""
        timed = self.analyzer.quantize_notes([], tempo=120)
        assert timed == []
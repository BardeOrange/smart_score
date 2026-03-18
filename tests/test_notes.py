import sys
from pathlib import Path

import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.transcriber.note_detector import (
    Note, NoteDetector,
    freq_to_midi, midi_to_freq,
    freq_to_note_name, midi_to_note_name
)


# ============ FREQUENCY / MIDI CONVERSION ============

class TestFreqToMidi:
    def test_a4(self):
        assert freq_to_midi(440.0) == 69

    def test_c4(self):
        """Middle C = MIDI 60."""
        assert freq_to_midi(261.63) == 60

    def test_a3(self):
        assert freq_to_midi(220.0) == 57

    def test_c5(self):
        assert freq_to_midi(523.25) == 72

    def test_zero_frequency(self):
        assert freq_to_midi(0) == 0

    def test_negative_frequency(self):
        assert freq_to_midi(-100) == 0


class TestMidiToFreq:
    def test_a4(self):
        assert abs(midi_to_freq(69) - 440.0) < 0.01

    def test_c4(self):
        assert abs(midi_to_freq(60) - 261.63) < 0.5

    def test_octave_relation(self):
        """One octave up = double frequency."""
        f1 = midi_to_freq(60)
        f2 = midi_to_freq(72)
        assert abs(f2 / f1 - 2.0) < 0.001


class TestNoteNames:
    def test_a4(self):
        name, pitch, octave = midi_to_note_name(69)
        assert name == "A4"
        assert pitch == "A"
        assert octave == 4

    def test_c4(self):
        name, pitch, octave = midi_to_note_name(60)
        assert name == "C4"
        assert pitch == "C"
        assert octave == 4

    def test_c_sharp(self):
        name, pitch, octave = midi_to_note_name(61)
        assert name == "C#4"
        assert pitch == "C#"

    def test_freq_to_note_name(self):
        name, pitch, octave = freq_to_note_name(440.0)
        assert name == "A4"

    def test_invalid_midi(self):
        name, pitch, octave = midi_to_note_name(-1)
        assert name == "?"


# ============ NOTE DETECTOR ============

class TestNoteDetector:
    def setup_method(self):
        self.detector = NoteDetector()

    def test_detect_single_note(self):
        """Single constant pitch should produce one note."""
        pitches = [440.0] * 20
        energies = [0.5] * 20
        onsets = [0]

        notes = self.detector.detect_notes(
            pitches, energies, onsets,
            sample_rate=22050, hop_size=512
        )
        assert len(notes) == 1
        assert notes[0].name == "A4"

    def test_detect_two_notes(self):
        """Two different pitches with onset should produce two notes."""
        pitches = [261.63] * 20 + [440.0] * 20
        energies = [0.5] * 40
        onsets = [0, 20]

        notes = self.detector.detect_notes(
            pitches, energies, onsets,
            sample_rate=22050, hop_size=512
        )
        assert len(notes) == 2
        assert notes[0].name == "C4"
        assert notes[1].name == "A4"

    def test_detect_no_energy(self):
        """Zero energy frames should not produce notes."""
        pitches = [440.0] * 20
        energies = [0.0] * 20
        onsets = [0]

        notes = self.detector.detect_notes(
            pitches, energies, onsets,
            sample_rate=22050, hop_size=512
        )
        assert len(notes) == 0

    def test_note_duration(self):
        """Note duration should match frame count."""
        pitches = [440.0] * 40
        energies = [0.5] * 40
        onsets = [0]
        hop_size = 512
        sr = 22050

        notes = self.detector.detect_notes(
            pitches, energies, onsets,
            sample_rate=sr, hop_size=hop_size
        )
        expected_duration = 40 * hop_size / sr
        assert abs(notes[0].duration - expected_duration) < 0.01

    def test_note_start_time(self):
        """Note start time should match onset position."""
        pitches = [0.0] * 10 + [440.0] * 20
        energies = [0.0] * 10 + [0.5] * 20
        onsets = [10]
        hop_size = 512
        sr = 22050

        notes = self.detector.detect_notes(
            pitches, energies, onsets,
            sample_rate=sr, hop_size=hop_size
        )
        expected_start = 10 * hop_size / sr
        assert abs(notes[0].start_time - expected_start) < 0.01

    def test_min_duration_filter(self):
        """Very short notes should be filtered out."""
        detector = NoteDetector(min_note_duration=1.0)
        pitches = [440.0] * 5  # Very short
        energies = [0.5] * 5
        onsets = [0]

        notes = detector.detect_notes(
            pitches, energies, onsets,
            sample_rate=22050, hop_size=512
        )
        assert len(notes) == 0

    def test_velocity_range(self):
        """Velocity should be between 0 and 127."""
        pitches = [440.0] * 20
        energies = [0.5] * 20
        onsets = [0]

        notes = self.detector.detect_notes(
            pitches, energies, onsets,
            sample_rate=22050, hop_size=512
        )
        for note in notes:
            assert 0 <= note.velocity <= 127

    def test_auto_detect_first_note(self):
        """Should detect note at start even without onset at frame 0."""
        pitches = [440.0] * 20
        energies = [0.5] * 20
        onsets = []  # No onsets

        notes = self.detector.detect_notes(
            pitches, energies, onsets,
            sample_rate=22050, hop_size=512
        )
        assert len(notes) >= 1
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.transcriber.note_detector import Note
from python.transcriber.instrument import InstrumentTransposer, INSTRUMENTS


def make_note(midi_number: int = 60) -> Note:
    return Note(
        name="C4",
        pitch="C",
        octave=4,
        midi_number=midi_number,
        frequency=261.63,
        start_time=0.0,
        duration=1.0,
        velocity=80
    )


class TestInstrumentTransposer:
    def test_piano_no_transpose(self):
        """Piano should not transpose."""
        notes = [make_note(60)]
        result = InstrumentTransposer.transpose(notes, "piano")
        assert result[0].midi_number == 60

    def test_clarinet_bb_transpose(self):
        """Bb Clarinet transposes +2 semitones."""
        notes = [make_note(60)]  # C4
        result = InstrumentTransposer.transpose(notes, "clarinet_bb")
        assert result[0].midi_number == 62  # D4

    def test_trumpet_bb_transpose(self):
        """Bb Trumpet transposes +2 semitones."""
        notes = [make_note(60)]
        result = InstrumentTransposer.transpose(notes, "trumpet_bb")
        assert result[0].midi_number == 62

    def test_guitar_transpose(self):
        """Guitar transposes +12 semitones (one octave)."""
        notes = [make_note(60)]
        result = InstrumentTransposer.transpose(notes, "guitar")
        assert result[0].midi_number == 72

    def test_range_clamping_high(self):
        """Notes above instrument range should be moved down."""
        notes = [make_note(110)]  # Very high
        result = InstrumentTransposer.transpose(notes, "violin")
        assert result[0].midi_number <= 103  # Violin max

    def test_range_clamping_low(self):
        """Notes below instrument range should be moved up."""
        notes = [make_note(30)]  # Very low
        result = InstrumentTransposer.transpose(notes, "violin")
        assert result[0].midi_number >= 55  # Violin min

    def test_preserves_timing(self):
        """Transposition should not change timing."""
        note = Note(
            name="C4", pitch="C", octave=4,
            midi_number=60, frequency=261.63,
            start_time=1.5, duration=0.8, velocity=80
        )
        result = InstrumentTransposer.transpose([note], "violin")
        assert result[0].start_time == 1.5
        assert result[0].duration == 0.8

    def test_preserves_velocity(self):
        """Transposition should not change velocity."""
        note = make_note(60)
        result = InstrumentTransposer.transpose([note], "violin")
        assert result[0].velocity == 80

    def test_unknown_instrument(self):
        with pytest.raises(ValueError):
            InstrumentTransposer.transpose([], "kazoo")

    def test_get_available_instruments(self):
        instruments = InstrumentTransposer.get_available_instruments()
        assert "piano" in instruments
        assert "violin" in instruments
        assert len(instruments) == len(INSTRUMENTS)

    def test_multiple_notes(self):
        """All notes should be transposed."""
        notes = [make_note(60), make_note(64), make_note(67)]
        result = InstrumentTransposer.transpose(notes, "clarinet_bb")
        assert result[0].midi_number == 62
        assert result[1].midi_number == 66
        assert result[2].midi_number == 69

    def test_original_unchanged(self):
        """Original notes should not be modified."""
        notes = [make_note(60)]
        original_midi = notes[0].midi_number
        InstrumentTransposer.transpose(notes, "clarinet_bb")
        assert notes[0].midi_number == original_midi
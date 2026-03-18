from typing import List, Dict, Tuple
from copy import deepcopy
from dataclasses import dataclass

from python.transcriber.note_detector import Note, freq_to_midi, midi_to_freq, midi_to_note_name


@dataclass
class InstrumentInfo:
    """Information about a musical instrument."""
    name: str
    transpose_semitones: int  # Semitones to transpose from concert pitch
    min_midi: int             # Lowest playable note (MIDI)
    max_midi: int             # Highest playable note (MIDI)
    clef: str                 # "treble" or "bass"


# Common instruments and their ranges
INSTRUMENTS: Dict[str, InstrumentInfo] = {
    "piano": InstrumentInfo(
        name="Piano",
        transpose_semitones=0,
        min_midi=21,   # A0
        max_midi=108,  # C8
        clef="treble"
    ),
    "violin": InstrumentInfo(
        name="Violin",
        transpose_semitones=0,
        min_midi=55,   # G3
        max_midi=103,  # G7
        clef="treble"
    ),
    "viola": InstrumentInfo(
        name="Viola",
        transpose_semitones=0,
        min_midi=48,   # C3
        max_midi=91,   # G6
        clef="treble"
    ),
    "cello": InstrumentInfo(
        name="Cello",
        transpose_semitones=0,
        min_midi=36,   # C2
        max_midi=76,   # E5
        clef="bass"
    ),
    "flute": InstrumentInfo(
        name="Flute",
        transpose_semitones=0,
        min_midi=60,   # C4
        max_midi=96,   # C7
        clef="treble"
    ),
    "clarinet_bb": InstrumentInfo(
        name="Clarinet (Bb)",
        transpose_semitones=2,  # Written 2 semitones higher
        min_midi=50,   # D3
        max_midi=94,   # Bb6
        clef="treble"
    ),
    "trumpet_bb": InstrumentInfo(
        name="Trumpet (Bb)",
        transpose_semitones=2,  # Written 2 semitones higher
        min_midi=55,   # G3
        max_midi=82,   # Bb5
        clef="treble"
    ),
    "alto_sax": InstrumentInfo(
        name="Alto Saxophone (Eb)",
        transpose_semitones=9,  # Written 9 semitones higher
        min_midi=49,   # Db3
        max_midi=80,   # Ab5
        clef="treble"
    ),
    "guitar": InstrumentInfo(
        name="Guitar",
        transpose_semitones=12,  # Written octave higher
        min_midi=40,   # E2
        max_midi=84,   # C6
        clef="treble"
    ),
    "bass_guitar": InstrumentInfo(
        name="Bass Guitar",
        transpose_semitones=12,
        min_midi=28,   # E1
        max_midi=67,   # G4
        clef="bass"
    ),
}


class InstrumentTransposer:
    """Transpose notes for different instruments."""

    @staticmethod
    def get_available_instruments() -> List[str]:
        """Return list of supported instruments."""
        return list(INSTRUMENTS.keys())

    @staticmethod
    def get_instrument_info(instrument: str) -> InstrumentInfo:
        """Get info about an instrument."""
        key = instrument.lower().replace(" ", "_")
        if key not in INSTRUMENTS:
            available = ", ".join(INSTRUMENTS.keys())
            raise ValueError(
                f"Unknown instrument: {instrument}\n"
                f"Available: {available}"
            )
        return INSTRUMENTS[key]

    @staticmethod
    def transpose(
        notes: List[Note],
        target_instrument: str
    ) -> List[Note]:
        """
        Transpose notes for a target instrument.

        Args:
            notes: Original detected notes
            target_instrument: Target instrument name

        Returns:
            New list of transposed notes
        """
        info = InstrumentTransposer.get_instrument_info(target_instrument)
        transposed = []

        for note in notes:
            new_note = deepcopy(note)

            # Apply transposition
            new_midi = note.midi_number + info.transpose_semitones

            # Adjust octave if out of range
            while new_midi < info.min_midi:
                new_midi += 12
            while new_midi > info.max_midi:
                new_midi -= 12

            # Update note info
            full_name, pitch, octave = midi_to_note_name(new_midi)
            new_note.midi_number = new_midi
            new_note.frequency = midi_to_freq(new_midi)
            new_note.name = full_name
            new_note.pitch = pitch
            new_note.octave = octave

            transposed.append(new_note)

        return transposed

    @staticmethod
    def print_transposition(
        original: List[Note],
        transposed: List[Note],
        instrument: str
    ) -> None:
        """Print comparison of original vs transposed notes."""
        info = InstrumentTransposer.get_instrument_info(instrument)

        print(f"\n{'=' * 60}")
        print(f"  🎻 Transposition: {info.name}")
        if info.transpose_semitones != 0:
            print(f"  Transpose: {info.transpose_semitones:+d} semitones")
        print(f"  Range: MIDI {info.min_midi}-{info.max_midi}")
        print(f"  Clef: {info.clef}")
        print(f"{'=' * 60}")
        print(f"  {'#':<4} {'Original':<10} {'→':<3} {info.name:<10}")
        print(f"  {'-' * 30}")

        for i, (orig, trans) in enumerate(zip(original, transposed)):
            print(f"  {i + 1:<4} {orig.name:<10} → {trans.name:<10}")
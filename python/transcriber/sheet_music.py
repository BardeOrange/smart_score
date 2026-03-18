import sys
from pathlib import Path
from typing import List, Optional

from python.transcriber.note_detector import Note
from python.transcriber.rhythm import TimedNote, DURATION_MAP
from python.transcriber.instrument import InstrumentTransposer, INSTRUMENTS


class SheetMusicGenerator:
    """
    Generate sheet music in multiple formats:
    - MIDI (.mid)
    - MusicXML (.xml) — Opens in MuseScore, Finale, etc.
    - Text-based preview
    """

    def __init__(
        self,
        tempo: float = 120.0,
        time_signature: tuple = (4, 4),
        title: str = "Transcribed Music",
        composer: str = "Music Transcriber"
    ):
        self.tempo = tempo
        self.time_signature = time_signature
        self.title = title
        self.composer = composer

    # ============ MIDI OUTPUT ============

    def generate_midi(
        self,
        notes: List[Note],
        output_path: str,
        instrument_program: int = 0
    ) -> None:
        """
        Generate a MIDI file.

        Args:
            notes: List of Note objects
            output_path: Path for .mid file
            instrument_program: MIDI instrument (0=piano, 40=violin, etc.)
        """
        import mido

        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)

        # Set tempo
        tempo_us = mido.bpm2tempo(self.tempo)
        track.append(mido.MetaMessage("set_tempo", tempo=tempo_us))

        # Set time signature
        track.append(mido.MetaMessage(
            "time_signature",
            numerator=self.time_signature[0],
            denominator=self.time_signature[1]
        ))

        # Set track name
        track.append(mido.MetaMessage("track_name", name=self.title))

        # Set instrument
        track.append(mido.Message(
            "program_change", program=instrument_program
        ))

        # Convert notes to MIDI messages
        ticks_per_beat = mid.ticks_per_beat
        current_tick = 0

        for note in notes:
            # Calculate note start in ticks
            note_start_ticks = int(note.start_time * self.tempo / 60 * ticks_per_beat)
            note_duration_ticks = int(note.duration * self.tempo / 60 * ticks_per_beat)

            # Time since last event
            delta = note_start_ticks - current_tick
            if delta < 0:
                delta = 0

            # Note on
            track.append(mido.Message(
                "note_on",
                note=note.midi_number,
                velocity=note.velocity,
                time=delta
            ))

            # Note off
            track.append(mido.Message(
                "note_off",
                note=note.midi_number,
                velocity=0,
                time=note_duration_ticks
            ))

            current_tick = note_start_ticks + note_duration_ticks

        # Save
        mid.save(output_path)
        print(f"MIDI saved: {output_path}")

    # ============ MUSICXML OUTPUT ============

    def generate_musicxml(
        self,
        timed_notes: List[TimedNote],
        output_path: str,
        instrument: str = "piano"
    ) -> None:
        """
        Generate a MusicXML file (opens in MuseScore, Finale, etc.)

        Args:
            timed_notes: Notes with rhythm information
            output_path: Path for .xml file
            instrument: Instrument name
        """
        from music21 import (
            stream, note, meter, tempo,
            metadata, instrument as m21_instrument, key
        )

        # Create score
        score = stream.Score()

        # Metadata
        score.metadata = metadata.Metadata()
        score.metadata.title = self.title
        score.metadata.composer = self.composer

        # Create part
        part = stream.Part()

        # Set instrument
        m21_inst = self._get_music21_instrument(instrument)
        if m21_inst:
            part.insert(0, m21_inst)

        # Time signature
        ts = meter.TimeSignature(
            f"{self.time_signature[0]}/{self.time_signature[1]}"
        )
        part.insert(0, ts)

        # Tempo
        mm = tempo.MetronomeMark(number=self.tempo)
        part.insert(0, mm)

        # Add notes
        for tn in timed_notes:
            n = note.Note(tn.note.midi_number)
            n.quarterLength = tn.beat_duration
            n.volume.velocity = tn.note.velocity
            part.append(n)

        score.append(part)

        # Save
        score.write("musicxml", fp=output_path)
        print(f"✅ MusicXML saved: {output_path}")
        print(f"   Open with MuseScore to see the sheet music!")

    def _get_music21_instrument(self, instrument_name: str):
        """Map instrument name to music21 instrument object."""
        from music21 import instrument as m21_inst

        mapping = {
            "piano": m21_inst.Piano,
            "violin": m21_inst.Violin,
            "viola": m21_inst.Viola,
            "cello": m21_inst.Violoncello,
            "flute": m21_inst.Flute,
            "clarinet_bb": m21_inst.Clarinet,
            "trumpet_bb": m21_inst.Trumpet,
            "alto_sax": m21_inst.AltoSaxophone,
            "guitar": m21_inst.AcousticGuitar,
            "bass_guitar": m21_inst.ElectricBass,
        }

        key = instrument_name.lower().replace(" ", "_")
        if key in mapping:
            return mapping[key]()
        return None

    # ============ TEXT PREVIEW ============

    def generate_text_preview(
        self,
        timed_notes: List[TimedNote],
        instrument: str = "piano"
    ) -> str:
        """
        Generate a text-based preview of the sheet music.
        """
        lines = []
        lines.append(f"╔{'═' * 56}╗")
        lines.append(f"║  🎵 {self.title:<50}║")
        lines.append(f"║  🎼 Instrument: {instrument:<39}║")
        lines.append(f"║  ⏱️  Tempo: {self.tempo:.0f} BPM{' ' * 35}║")
        lines.append(
            f"║  📏 Time Signature: "
            f"{self.time_signature[0]}/{self.time_signature[1]}"
            f"{' ' * 30}║"
        )
        lines.append(f"╠{'═' * 56}╣")

        current_measure = 0
        measure_notes = []

        for tn in timed_notes:
            if tn.measure != current_measure:
                if measure_notes:
                    notes_str = "  ".join(measure_notes)
                    lines.append(
                        f"║  Bar {current_measure:>3}: "
                        f"{notes_str:<45}║"
                    )
                current_measure = tn.measure
                measure_notes = []

            # Format note with duration symbol
            symbol = self._duration_symbol(tn.duration_name)
            measure_notes.append(f"{tn.note.name}{symbol}")

        # Last measure
        if measure_notes:
            notes_str = "  ".join(measure_notes)
            lines.append(
                f"║  Bar {current_measure:>3}: "
                f"{notes_str:<45}║"
            )

        lines.append(f"╚{'═' * 56}╝")
        return "\n".join(lines)

    def _duration_symbol(self, duration_name: str) -> str:
        """Get a text symbol for note duration."""
        symbols = {
            "whole": "𝅝",
            "half": "𝅗𝅥",
            "quarter": "♩",
            "eighth": "♪",
            "sixteenth": "𝅘𝅥𝅯",
            "dotted_half": "𝅗𝅥.",
            "dotted_quarter": "♩.",
            "dotted_eighth": "♪.",
        }
        return symbols.get(duration_name, "♩")

    # ============ MIDI INSTRUMENT PROGRAMS ============

    @staticmethod
    def get_midi_program(instrument: str) -> int:
        """Get MIDI program number for an instrument."""
        programs = {
            "piano": 0,
            "violin": 40,
            "viola": 41,
            "cello": 42,
            "flute": 73,
            "clarinet_bb": 71,
            "trumpet_bb": 56,
            "alto_sax": 65,
            "guitar": 24,
            "bass_guitar": 33,
        }
        key = instrument.lower().replace(" ", "_")
        return programs.get(key, 0)
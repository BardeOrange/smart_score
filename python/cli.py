import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.transcriber import AudioAnalyzer
from python.transcriber.instrument import InstrumentTransposer
from python.transcriber.sheet_music import SheetMusicGenerator


def main():
    parser = argparse.ArgumentParser(
        description="🎵 Music Transcriber — Convert audio to sheet music"
    )
    parser.add_argument(
        "input",
        nargs="?",          # Makes it optional
        default=None,
        help="Input audio/video file"
    )
    parser.add_argument(
        "--instrument", "-i",
        default="piano",
        help="Target instrument (default: piano)"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path (auto-generated if not set)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["midi", "musicxml", "both"],
        default="both",
        help="Output format (default: both)"
    )
    parser.add_argument(
        "--tempo", "-t",
        type=float,
        default=None,
        help="Override tempo (BPM). Auto-detected if not set."
    )
    parser.add_argument(
        "--show-plots",
        action="store_true",
        help="Show spectrogram and piano roll"
    )
    parser.add_argument(
        "--list-instruments",
        action="store_true",
        help="List available instruments"
    )

    args = parser.parse_args()

    # List instruments (no input needed)
    if args.list_instruments:
        print("\n🎻 Available Instruments:")
        print("=" * 40)
        for name in InstrumentTransposer.get_available_instruments():
            info = InstrumentTransposer.get_instrument_info(name)
            print(f"  {name:<15} ({info.name})")
        sys.exit(0)

    # From here, input is required
    if args.input is None:
        parser.error("Please provide an input audio/video file")

    # Validate input
    if not Path(args.input).exists():
        print(f"❌ File not found: {args.input}")
        sys.exit(1)

    # Setup output paths
    input_stem = Path(args.input).stem
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    if args.output:
        output_base = Path(args.output).stem
    else:
        output_base = f"{input_stem}_{args.instrument}"

    # ============ ANALYZE ============

    print(f"\n🎵 Music Transcriber")
    print(f"{'=' * 50}")
    print(f"  Input: {args.input}")
    print(f"  Instrument: {args.instrument}")
    print(f"{'=' * 50}")

    analyzer = AudioAnalyzer()
    analyzer.load(args.input)
    analyzer.analyze()

    # Print detected notes
    analyzer.print_notes()

    # ============ TRANSPOSE ============

    notes = analyzer.notes
    timed_notes = analyzer.timed_notes
    tempo = args.tempo or analyzer.tempo

    if args.instrument != "piano":
        print(f"\n🎻 Transposing for {args.instrument}...")
        transposed_notes = InstrumentTransposer.transpose(notes, args.instrument)
        InstrumentTransposer.print_transposition(
            notes, transposed_notes, args.instrument
        )
        notes = transposed_notes

        # Re-quantize transposed notes
        from python.transcriber.rhythm import RhythmAnalyzer
        rhythm = RhythmAnalyzer()
        timed_notes = rhythm.quantize_notes(notes, tempo)

    # ============ GENERATE OUTPUT ============

    generator = SheetMusicGenerator(
        tempo=tempo,
        title=f"Transcription - {Path(args.input).name}",
        composer="Music Transcriber"
    )

    # Text preview
    preview = generator.generate_text_preview(timed_notes, args.instrument)
    print(f"\n{preview}")

    # MIDI
    if args.format in ("midi", "both"):
        midi_path = str(output_dir / f"{output_base}.mid")
        midi_program = SheetMusicGenerator.get_midi_program(args.instrument)
        generator.generate_midi(notes, midi_path, midi_program)

    # MusicXML
    if args.format in ("musicxml", "both"):
        xml_path = str(output_dir / f"{output_base}.xml")
        generator.generate_musicxml(timed_notes, xml_path, args.instrument)

    # ============ PLOTS ============

    if args.show_plots:
        analyzer.plot_spectrogram()
        analyzer.plot_notes()

    print(f"\n🎉 Done! Check the output/ folder.")


if __name__ == "__main__":
    main()
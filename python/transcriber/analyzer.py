import numpy as np
import matplotlib.pyplot as plt
from typing import List, Optional
import audio_core_cpp

from python.transcriber.audio_loader import AudioLoader
from python.transcriber.note_detector import Note, NoteDetector
from python.transcriber.rhythm import RhythmAnalyzer, TimedNote


class AudioAnalyzer:
    """
    Main analysis class. Connects audio loading, C++ processing,
    note detection, and rhythm analysis.
    """

    def __init__(
        self,
        frame_size: int = 2048,
        hop_size: int = 512,
        min_frequency: float = 50.0,
        max_frequency: float = 4200.0
    ):
        """
        Args:
            frame_size: FFT window size
            hop_size: Hop between frames
            min_frequency: Lowest frequency to detect
            max_frequency: Highest frequency to detect
        """
        self.frame_size = frame_size
        self.hop_size = hop_size
        self.min_frequency = min_frequency
        self.max_frequency = max_frequency

        self.note_detector = NoteDetector(
            min_frequency=min_frequency,
            max_frequency=max_frequency
        )
        self.rhythm_analyzer = RhythmAnalyzer()

        # Internal state
        self._audio: Optional[AudioLoader] = None
        self._spectrogram: Optional[List[float]] = None
        self._num_frames: int = 0
        self._freq_bins: int = 0
        self._pitches: Optional[List[float]] = None
        self._energies: Optional[List[float]] = None
        self._onset_frames: Optional[List[int]] = None
        self._notes: Optional[List[Note]] = None
        self._timed_notes: Optional[List[TimedNote]] = None
        self._tempo: float = 120.0

    def load(self, file_path: str) -> "AudioAnalyzer":
        """Load an audio or video file."""
        self._audio = AudioLoader(file_path)
        return self

    def analyze(self) -> "AudioAnalyzer":
        """Run the full analysis pipeline."""
        if self._audio is None:
            raise RuntimeError("No audio loaded! Call .load() first.")

        print("\n📊 Computing spectrogram (C++)...")
        self._compute_spectrogram()

        print("🎵 Detecting pitches (C++)...")
        self._detect_pitches()

        print("🥁 Detecting onsets (C++)...")
        self._detect_onsets()

        print("🎹 Identifying notes...")
        self._identify_notes()

        print("⏱️ Analyzing rhythm...")
        self._analyze_rhythm()

        return self

    def _compute_spectrogram(self):
        """Compute spectrogram using C++ FFT."""
        samples = self._audio.samples.tolist()

        self._spectrogram = audio_core_cpp.compute_spectrogram(
            samples, self.frame_size, self.hop_size
        )

        # Calculate dimensions
        fft_size = 1
        while fft_size < self.frame_size:
            fft_size <<= 1
        self._freq_bins = fft_size // 2
        self._num_frames = len(self._spectrogram) // self._freq_bins

        print(f"   Frames: {self._num_frames}, Freq bins: {self._freq_bins}")

    def _detect_pitches(self):
        """Detect pitch at each frame using C++."""
        self._pitches = audio_core_cpp.detect_pitches(
            self._spectrogram,
            self._num_frames,
            self._freq_bins,
            self._audio.sample_rate,
            self.min_frequency,
            self.max_frequency
        )

        # Compute frame energies
        self._energies = []
        for i in range(self._num_frames):
            start = i * self._freq_bins
            end = start + self._freq_bins
            energy = sum(self._spectrogram[start:end]) / self._freq_bins
            self._energies.append(energy)

    def _detect_onsets(self):
        """Detect note onsets using C++ spectral flux."""
        flux = audio_core_cpp.spectral_flux(
            self._spectrogram,
            self._num_frames,
            self._freq_bins
        )
        self._onset_frames = audio_core_cpp.find_onsets(flux)
        print(f"   Onsets found: {len(self._onset_frames)}")

    def _identify_notes(self):
        """Convert pitches and onsets to musical notes."""
        # Lower threshold for note detection
        self.note_detector.energy_threshold = max(self._energies) * 0.01

        self._notes = self.note_detector.detect_notes(
            pitches=self._pitches,
            energies=self._energies,
            onset_frames=self._onset_frames,
            sample_rate=self._audio.sample_rate,
            hop_size=self.hop_size
        )
        print(f"   Notes detected: {len(self._notes)}")

    def _analyze_rhythm(self):
        """Analyze tempo and quantize note durations."""
        self._tempo = self.rhythm_analyzer.estimate_tempo(self._notes)
        self._timed_notes = self.rhythm_analyzer.quantize_notes(
            self._notes, self._tempo
        )

    # ============ GETTERS ============

    @property
    def notes(self) -> List[Note]:
        """Get detected notes."""
        if self._notes is None:
            raise RuntimeError("Run .analyze() first!")
        return self._notes

    @property
    def timed_notes(self) -> List[TimedNote]:
        """Get notes with rhythm information."""
        if self._timed_notes is None:
            raise RuntimeError("Run .analyze() first!")
        return self._timed_notes

    @property
    def tempo(self) -> float:
        """Get detected tempo."""
        return self._tempo

    # ============ VISUALIZATION ============

    def plot_spectrogram(self) -> None:
        """Display the spectrogram."""
        if self._spectrogram is None:
            raise RuntimeError("Run .analyze() first!")

        spec_array = np.array(self._spectrogram).reshape(
            self._num_frames, self._freq_bins
        )

        # Convert to dB scale
        spec_db = 20 * np.log10(spec_array + 1e-10)

        plt.figure(figsize=(14, 5))
        plt.imshow(
            spec_db.T,
            aspect="auto",
            origin="lower",
            cmap="magma",
            extent=[
                0,
                self._num_frames * self.hop_size / self._audio.sample_rate,
                0,
                self._audio.sample_rate / 2
            ]
        )
        plt.colorbar(label="Magnitude (dB)")
        plt.xlabel("Time (s)")
        plt.ylabel("Frequency (Hz)")
        plt.title("Spectrogram")
        plt.ylim(0, 2000)  # Focus on musical range
        plt.tight_layout()
        plt.show()

    def plot_notes(self) -> None:
        """Display detected notes on a piano roll."""
        if self._notes is None:
            raise RuntimeError("Run .analyze() first!")

        fig, ax = plt.subplots(figsize=(14, 6))

        for note in self._notes:
            ax.barh(
                note.midi_number,
                note.duration,
                left=note.start_time,
                height=0.8,
                color="steelblue",
                edgecolor="white",
                linewidth=0.5
            )
            ax.text(
                note.start_time + note.duration / 2,
                note.midi_number,
                note.name,
                ha="center",
                va="center",
                fontsize=7,
                color="white",
                fontweight="bold"
            )

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("MIDI Note")
        ax.set_title(f"Detected Notes — Tempo: {self._tempo:.0f} BPM")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    def print_notes(self) -> None:
        """Print all detected notes."""
        print(f"\n{'=' * 60}")
        print(f"  🎵 Detected Notes ({len(self._notes)} total)")
        print(f"  Tempo: {self._tempo:.0f} BPM")
        print(f"{'=' * 60}")

        for i, note in enumerate(self._notes):
            print(f"  {i + 1:>3}. {note}")

        if self._timed_notes:
            self.rhythm_analyzer.print_rhythm_analysis(
                self._timed_notes, self._tempo
            )
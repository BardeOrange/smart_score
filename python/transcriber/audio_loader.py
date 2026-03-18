import subprocess
import numpy as np
import soundfile as sf
import librosa
from pathlib import Path
from typing import Optional, Tuple
import tempfile
import os


class AudioLoader:
    """
    Loads audio from audio/video files.
    Extracts audio from video using FFmpeg.
    """

    # Supported formats
    AUDIO_FORMATS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"}
    VIDEO_FORMATS = {".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv"}

    def __init__(self, file_path: str, target_sr: int = 22050):
        """
        Load audio from file.

        Args:
            file_path: Path to audio or video file
            target_sr: Target sample rate (default 22050 Hz)
        """
        self.file_path = Path(file_path)
        self.target_sr = target_sr
        self._validate_file()

        # Load audio
        self.samples, self.sample_rate = self._load_audio()
        self.duration = len(self.samples) / self.sample_rate

    def _validate_file(self):
        """Check if file exists and format is supported."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        suffix = self.file_path.suffix.lower()
        all_formats = self.AUDIO_FORMATS | self.VIDEO_FORMATS
        if suffix not in all_formats:
            raise ValueError(
                f"Unsupported format: {suffix}\n"
                f"Supported: {', '.join(sorted(all_formats))}"
            )

    def _is_video(self) -> bool:
        """Check if file is a video format."""
        return self.file_path.suffix.lower() in self.VIDEO_FORMATS

    def _extract_audio_from_video(self) -> str:
        """Extract audio from video file using FFmpeg."""
        temp_wav = tempfile.mktemp(suffix=".wav")

        try:
            cmd = [
                "ffmpeg",
                "-i", str(self.file_path),
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # WAV format
                "-ar", str(self.target_sr),  # Sample rate
                "-ac", "1",  # Mono
                "-y",  # Overwrite
                temp_wav
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg error: {result.stderr}"
                )
        except FileNotFoundError:
            raise RuntimeError(
                "FFmpeg not found! Install it: winget install ffmpeg"
            )

        return temp_wav

    def _load_audio(self) -> Tuple[np.ndarray, int]:
        """Load audio samples from file."""
        temp_file = None

        try:
            if self._is_video():
                print(f"🎬 Extracting audio from video...")
                temp_file = self._extract_audio_from_video()
                load_path = temp_file
            else:
                load_path = str(self.file_path)

            print(f"🔊 Loading audio: {self.file_path.name}")

            # Load with librosa (handles resampling and mono conversion)
            samples, sr = librosa.load(
                load_path,
                sr=self.target_sr,
                mono=True
            )

            print(f"   Sample rate: {sr} Hz")
            print(f"   Duration: {len(samples) / sr:.2f}s")
            print(f"   Samples: {len(samples):,}")

            return samples, sr

        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)

    def get_segment(
            self,
            start_time: float,
            end_time: float
    ) -> np.ndarray:
        """Get a segment of audio between start and end time (seconds)."""
        start_sample = int(start_time * self.sample_rate)
        end_sample = int(end_time * self.sample_rate)
        return self.samples[start_sample:end_sample]

    def save_wav(self, output_path: str) -> None:
        """Save the loaded audio as WAV file."""
        sf.write(output_path, self.samples, self.sample_rate)
        print(f"✅ Saved: {output_path}")

    @property
    def info(self) -> dict:
        """Return audio file information."""
        return {
            "file": str(self.file_path),
            "format": self.file_path.suffix,
            "sample_rate": self.sample_rate,
            "duration": round(self.duration, 2),
            "samples": len(self.samples),
            "is_video": self._is_video()
        }
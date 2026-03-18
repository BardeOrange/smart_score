import sys
from pathlib import Path

import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

import audio_core_cpp


class TestFFT:
    def test_single_frequency(self):
        """FFT should detect a single sine wave frequency."""
        sr = 22050
        freq = 440.0
        t = np.linspace(0, 1.0, sr, endpoint=False)
        signal = np.sin(2 * np.pi * freq * t).tolist()

        magnitudes = audio_core_cpp.magnitude_spectrum(signal)
        detected = audio_core_cpp.dominant_frequency(magnitudes, sr)
        assert abs(detected - freq) < 10

    def test_low_frequency(self):
        """Should detect a low frequency."""
        sr = 22050
        freq = 100.0
        t = np.linspace(0, 1.0, sr, endpoint=False)
        signal = np.sin(2 * np.pi * freq * t).tolist()

        magnitudes = audio_core_cpp.magnitude_spectrum(signal)
        detected = audio_core_cpp.dominant_frequency(magnitudes, sr)
        assert abs(detected - freq) < 10

    def test_high_frequency(self):
        """Should detect a high frequency."""
        sr = 22050
        freq = 2000.0
        t = np.linspace(0, 1.0, sr, endpoint=False)
        signal = np.sin(2 * np.pi * freq * t).tolist()

        magnitudes = audio_core_cpp.magnitude_spectrum(signal)
        detected = audio_core_cpp.dominant_frequency(magnitudes, sr)
        assert abs(detected - freq) < 20


class TestSpectrogram:
    def test_output_size(self):
        """Spectrogram dimensions should be correct."""
        signal = [0.0] * 22050  # 1 second
        frame_size = 2048
        hop_size = 512

        spec = audio_core_cpp.compute_spectrogram(signal, frame_size, hop_size)

        fft_size = 1
        while fft_size < frame_size:
            fft_size <<= 1
        freq_bins = fft_size // 2
        expected_frames = (len(signal) - frame_size) // hop_size + 1

        assert len(spec) == expected_frames * freq_bins

    def test_silent_signal(self):
        """Silent signal should have near-zero magnitudes."""
        signal = [0.0] * 22050
        spec = audio_core_cpp.compute_spectrogram(signal, 2048, 512)
        assert max(spec) < 0.001

    def test_invalid_frame_size(self):
        with pytest.raises(Exception):
            audio_core_cpp.compute_spectrogram([1.0] * 100, 0, 512)

    def test_invalid_hop_size(self):
        with pytest.raises(Exception):
            audio_core_cpp.compute_spectrogram([1.0] * 100, 2048, 0)

    def test_empty_signal(self):
        with pytest.raises(Exception):
            audio_core_cpp.compute_spectrogram([], 2048, 512)


class TestOnsetDetection:
    def test_flux_size(self):
        """Spectral flux should have same number of frames."""
        num_frames = 50
        freq_bins = 1024
        spec = [0.0] * (num_frames * freq_bins)

        flux = audio_core_cpp.spectral_flux(spec, num_frames, freq_bins)
        assert len(flux) == num_frames

    def test_silent_no_onsets(self):
        """Silent audio should have no onsets."""
        num_frames = 50
        freq_bins = 1024
        spec = [0.0] * (num_frames * freq_bins)

        flux = audio_core_cpp.spectral_flux(spec, num_frames, freq_bins)
        onsets = audio_core_cpp.find_onsets(flux)
        assert len(onsets) == 0

    def test_sudden_onset(self):
        """A sudden loud frame should be detected as onset."""
        num_frames = 50
        freq_bins = 100
        spec = [0.0] * (num_frames * freq_bins)

        # Add sudden energy at frame 25
        for j in range(freq_bins):
            spec[25 * freq_bins + j] = 1.0

        flux = audio_core_cpp.spectral_flux(spec, num_frames, freq_bins)
        onsets = audio_core_cpp.find_onsets(flux)
        assert len(onsets) >= 1
        assert 25 in onsets


class TestPitchDetection:
    def test_constant_pitch(self):
        """All frames should detect same pitch for constant signal."""
        sr = 22050
        freq = 440.0
        t = np.linspace(0, 1.0, sr, endpoint=False)
        signal = np.sin(2 * np.pi * freq * t).tolist()

        spec = audio_core_cpp.compute_spectrogram(signal, 2048, 512)

        fft_size = 2048
        freq_bins = fft_size // 2
        num_frames = len(spec) // freq_bins

        pitches = audio_core_cpp.detect_pitches(
            spec, num_frames, freq_bins, sr
        )

        # Most pitches should be near 440 Hz
        close_to_440 = sum(1 for p in pitches if abs(p - 440) < 20)
        assert close_to_440 > len(pitches) * 0.8
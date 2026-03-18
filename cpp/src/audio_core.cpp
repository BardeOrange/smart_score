#include <vector>
#include <cstdint>
#include <cmath>
#include <complex>
#include <algorithm>
#include <stdexcept>
#include <numeric>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

namespace audiocore {

    const double PI = 3.14159265358979323846;

    // ============ FFT ============

    using Complex = std::complex<double>;

    /**
     * Cooley-Tukey FFT (radix-2, in-place)
     * Input size must be a power of 2.
     */
    void fft_inplace(std::vector<Complex>& data) {
        size_t n = data.size();
        if (n <= 1) return;

        // Bit-reversal permutation
        for (size_t i = 1, j = 0; i < n; ++i) {
            size_t bit = n >> 1;
            while (j & bit) {
                j ^= bit;
                bit >>= 1;
            }
            j ^= bit;
            if (i < j) std::swap(data[i], data[j]);
        }

        // FFT butterfly
        for (size_t len = 2; len <= n; len <<= 1) {
            double angle = -2.0 * PI / len;
            Complex wn(std::cos(angle), std::sin(angle));

            for (size_t i = 0; i < n; i += len) {
                Complex w(1.0, 0.0);
                for (size_t j = 0; j < len / 2; ++j) {
                    Complex u = data[i + j];
                    Complex v = data[i + j + len / 2] * w;
                    data[i + j] = u + v;
                    data[i + j + len / 2] = u - v;
                    w *= wn;
                }
            }
        }
    }

    /**
     * Compute magnitude spectrum from real signal.
     * Pads to next power of 2 if needed.
     */
    std::vector<double> magnitude_spectrum(const std::vector<double>& signal) {
        // Pad to next power of 2
        size_t n = 1;
        while (n < signal.size()) n <<= 1;

        std::vector<Complex> data(n, Complex(0.0, 0.0));
        for (size_t i = 0; i < signal.size(); ++i) {
            data[i] = Complex(signal[i], 0.0);
        }

        fft_inplace(data);

        // Return magnitude of first half (positive frequencies)
        std::vector<double> magnitudes(n / 2);
        for (size_t i = 0; i < n / 2; ++i) {
            magnitudes[i] = std::abs(data[i]) / n;
        }
        return magnitudes;
    }

    // ============ SPECTROGRAM ============

    /**
     * Apply Hann window to a frame.
     */
    std::vector<double> hann_window(const std::vector<double>& frame) {
        size_t n = frame.size();
        std::vector<double> windowed(n);
        for (size_t i = 0; i < n; ++i) {
            double w = 0.5 * (1.0 - std::cos(2.0 * PI * i / (n - 1)));
            windowed[i] = frame[i] * w;
        }
        return windowed;
    }

    /**
     * Compute spectrogram: time × frequency magnitude matrix.
     * Returns a flat vector (row-major: time frames × freq bins).
     */
    std::vector<double> compute_spectrogram(
        const std::vector<double>& samples,
        int frame_size,
        int hop_size
    ) {
        if (frame_size <= 0 || hop_size <= 0) {
            throw std::invalid_argument("Frame size and hop size must be positive");
        }
        if (samples.empty()) {
            throw std::invalid_argument("Audio samples cannot be empty");
        }

        // Pad frame_size to next power of 2
        size_t fft_size = 1;
        while (fft_size < static_cast<size_t>(frame_size)) fft_size <<= 1;

        size_t num_frames = 0;
        if (samples.size() >= static_cast<size_t>(frame_size)) {
            num_frames = (samples.size() - frame_size) / hop_size + 1;
        } else {
            num_frames = 1;
        }

        size_t freq_bins = fft_size / 2;
        std::vector<double> spectrogram(num_frames * freq_bins);

        for (size_t i = 0; i < num_frames; ++i) {
            // Extract frame
            std::vector<double> frame(fft_size, 0.0);
            size_t start = i * hop_size;
            for (size_t j = 0; j < static_cast<size_t>(frame_size) && (start + j) < samples.size(); ++j) {
                frame[j] = samples[start + j];
            }

            // Apply window
            for (size_t j = 0; j < static_cast<size_t>(frame_size); ++j) {
                double w = 0.5 * (1.0 - std::cos(2.0 * PI * j / (frame_size - 1)));
                frame[j] *= w;
            }

            // FFT
            std::vector<Complex> fft_data(fft_size);
            for (size_t j = 0; j < fft_size; ++j) {
                fft_data[j] = Complex(frame[j], 0.0);
            }
            fft_inplace(fft_data);

            // Magnitude
            for (size_t j = 0; j < freq_bins; ++j) {
                spectrogram[i * freq_bins + j] = std::abs(fft_data[j]) / fft_size;
            }
        }

        return spectrogram;
    }

    // ============ PITCH DETECTION ============

    /**
     * Find the dominant frequency in a magnitude spectrum.
     */
    double dominant_frequency(
        const std::vector<double>& magnitudes,
        double sample_rate,
        double min_freq = 50.0,
        double max_freq = 4200.0
    ) {
        size_t n = magnitudes.size();
        double freq_resolution = sample_rate / (2.0 * n);

        size_t min_bin = static_cast<size_t>(min_freq / freq_resolution);
        size_t max_bin = std::min(
            static_cast<size_t>(max_freq / freq_resolution), n - 1
        );

        double max_mag = 0.0;
        size_t max_idx = min_bin;

        for (size_t i = min_bin; i <= max_bin; ++i) {
            if (magnitudes[i] > max_mag) {
                max_mag = magnitudes[i];
                max_idx = i;
            }
        }

        return max_idx * freq_resolution;
    }

    // ============ ONSET DETECTION ============

    /**
     * Compute spectral flux for onset detection.
     * Returns energy difference between consecutive frames.
     */
    std::vector<double> spectral_flux(
        const std::vector<double>& spectrogram,
        int num_frames,
        int freq_bins
    ) {
        std::vector<double> flux(num_frames, 0.0);

        for (int i = 1; i < num_frames; ++i) {
            double sum = 0.0;
            for (int j = 0; j < freq_bins; ++j) {
                double diff = spectrogram[i * freq_bins + j]
                            - spectrogram[(i - 1) * freq_bins + j];
                if (diff > 0) sum += diff;  // Half-wave rectification
            }
            flux[i] = sum;
        }

        return flux;
    }

    /**
     * Find onset positions from spectral flux.
     * Returns frame indices where onsets occur.
     */
    std::vector<int> find_onsets(
        const std::vector<double>& flux,
        double threshold_multiplier = 1.5
    ) {
        if (flux.empty()) return {};

        // Compute adaptive threshold (mean + multiplier * std)
        double mean = 0.0;
        for (double v : flux) mean += v;
        mean /= flux.size();

        double variance = 0.0;
        for (double v : flux) variance += (v - mean) * (v - mean);
        variance /= flux.size();
        double std_dev = std::sqrt(variance);

        double threshold = mean + threshold_multiplier * std_dev;

        // Find peaks above threshold
        std::vector<int> onsets;
        for (size_t i = 1; i + 1 < flux.size(); ++i) {
            if (flux[i] > threshold &&
                flux[i] > flux[i - 1] &&
                flux[i] >= flux[i + 1]) {
                onsets.push_back(static_cast<int>(i));
            }
        }

        return onsets;
    }

    /**
     * Detect pitches at each frame of the spectrogram.
     * Returns frequency for each frame.
     */
    std::vector<double> detect_pitches(
        const std::vector<double>& spectrogram,
        int num_frames,
        int freq_bins,
        double sample_rate,
        double min_freq = 50.0,
        double max_freq = 4200.0
    ) {
        std::vector<double> pitches(num_frames);

        for (int i = 0; i < num_frames; ++i) {
            std::vector<double> frame_mag(
                spectrogram.begin() + i * freq_bins,
                spectrogram.begin() + (i + 1) * freq_bins
            );
            pitches[i] = dominant_frequency(
                frame_mag, sample_rate, min_freq, max_freq
            );
        }

        return pitches;
    }

} // namespace audiocore


// ============ PYBIND11 BINDINGS ============

PYBIND11_MODULE(audio_core_cpp, m) {
    m.doc() = "C++ Audio Processing Core — FFT, Spectrogram, Pitch Detection";

    m.def("magnitude_spectrum", &audiocore::magnitude_spectrum,
          "Compute magnitude spectrum of a signal",
          py::arg("signal"));

    m.def("compute_spectrogram", &audiocore::compute_spectrogram,
          "Compute spectrogram (time x frequency)",
          py::arg("samples"), py::arg("frame_size"), py::arg("hop_size"));

    m.def("dominant_frequency", &audiocore::dominant_frequency,
          "Find dominant frequency in magnitude spectrum",
          py::arg("magnitudes"), py::arg("sample_rate"),
          py::arg("min_freq") = 50.0, py::arg("max_freq") = 4200.0);

    m.def("spectral_flux", &audiocore::spectral_flux,
          "Compute spectral flux for onset detection",
          py::arg("spectrogram"), py::arg("num_frames"), py::arg("freq_bins"));

    m.def("find_onsets", &audiocore::find_onsets,
          "Find onset positions from spectral flux",
          py::arg("flux"), py::arg("threshold_multiplier") = 1.5);

    m.def("detect_pitches", &audiocore::detect_pitches,
          "Detect pitch at each spectrogram frame",
          py::arg("spectrogram"), py::arg("num_frames"), py::arg("freq_bins"),
          py::arg("sample_rate"),
          py::arg("min_freq") = 50.0, py::arg("max_freq") = 4200.0);
}
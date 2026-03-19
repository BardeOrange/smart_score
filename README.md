# Music Transcriber — Audio to Sheet Music

A music transcription tool that converts audio/video files into sheet music.
Features a C++ audio processing core (FFT, spectrogram, pitch detection)
with a Python interface for note detection, rhythm analysis, and sheet music generation.

![CI](https://github.com/BardeOrange/smart_score/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.13%2B-blue?logo=python)
![C++](https://img.shields.io/badge/C%2B%2B-17-00599C?logo=cplusplus)
![License](https://img.shields.io/badge/License-PERSO-green)

---

## How It Works

```
Audio/Video File (MP3, WAV, MP4, AVI...)
|
v
Audio Extraction -----> FFmpeg (from video)
|
v
Spectrogram ----------> C++ FFT (Fast Fourier Transform)
|
v
Pitch Detection ------> C++ Peak Detection
|
v
Onset Detection ------> C++ Spectral Flux
|
v
Note Identification --> Python (frequency -> note name)
|
v
Rhythm Analysis ------> Python (tempo, beat quantization)
|
v
Instrument Transpose -> Python (piano -> violin, guitar...)
|
v
Sheet Music ----------> MIDI + MusicXML + PDF
```

---

## Features

- **Audio & Video Input** - MP3, WAV, FLAC, MP4, AVI, MKV and more
- **C++ Audio Engine** - FFT, spectrogram, pitch & onset detection
- **Note Detection** - Identifies musical notes with timing and velocity
- **Rhythm Analysis** - Auto tempo detection and beat quantization
- **10 Instruments** - Piano, violin, guitar, flute, trumpet and more
- **Sheet Music Output** - MIDI (.mid) and MusicXML (.xml) files
- **Visualizations** - Spectrogram and piano roll plots
- **CLI Tool** - Full command-line interface
- **35+ Tests** - Comprehensive test coverage

---

## Supported Instruments

| Instrument | Transposition | Range |
|---|---|---|
| Piano | Concert pitch | A0 - C8 |
| Violin | Concert pitch | G3 - G7 |
| Viola | Concert pitch | C3 - G6 |
| Cello | Concert pitch | C2 - E5 |
| Flute | Concert pitch | C4 - C7 |
| Clarinet (Bb) | +2 semitones | D3 - Bb6 |
| Trumpet (Bb) | +2 semitones | G3 - Bb5 |
| Alto Saxophone (Eb) | +9 semitones | Db3 - Ab5 |
| Guitar | +12 semitones | E2 - C6 |
| Bass Guitar | +12 semitones | E1 - G4 |

---

## Tech Stack

| Technology | Purpose |
|---|---|
| **C++17** | FFT, spectrogram, pitch & onset detection |
| **pybind11** | C++ to Python bridge |
| **CMake** | C++ build system |
| **FFmpeg** | Audio extraction from video |
| **librosa** | Audio loading and resampling |
| **music21** | MusicXML sheet music generation |
| **mido** | MIDI file generation |
| **NumPy** | Array operations |
| **matplotlib** | Visualizations |
| **pytest** | Testing |

---

## Project Structure

```
smart_score/
├── cpp/
│   ├── include/
│   │   ├── fft.h
│   │   ├── spectrogram.h
│   │   ├── pitch_detect.h
│   │   └── onset_detect.h
│   └── src/
│       └── audio_core.cpp         # C++ audio engine
├── python/
│   ├── transcriber/
│   │   ├── __init__.py
│   │   ├── audio_loader.py        # Audio/video file loading
│   │   ├── analyzer.py            # Main analysis pipeline
│   │   ├── note_detector.py       # Frequency to note conversion
│   │   ├── rhythm.py              # Tempo & rhythm analysis
│   │   ├── instrument.py          # Instrument transposition
│   │   └── sheet_music.py         # MIDI & MusicXML generation
│   └── cli.py                     # Command-line interface
├── tests/
│   ├── test_audio.py              # C++ module tests
│   ├── test_notes.py              # Note detection tests
│   ├── test_rhythm.py             # Rhythm analysis tests
│   └── test_instrument.py         # Transposition tests
├── examples/
│   └── demo.py
├── CMakeLists.txt
├── build.bat
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- C++17 compiler (MSVC, GCC, or Clang)
- CMake 3.16+
- FFmpeg

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/BardeOrange/smart_score.git
cd smart_score
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
```

3. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

4. **Build the C++ module**

Windows:
```bash
build.bat
```

Manual:
```bash
mkdir build && cd build
cmake .. -Dpybind11_DIR=%VIRTUAL_ENV%\Lib\site-packages\pybind11\share\cmake\pybind11
cmake --build . --config Release
cd ..
copy build\Release\audio_core_cpp*.pyd .
```

5. **Verify**
```bash
python -c "import audio_core_cpp; print('Ready!')"
```

---

## Usage

### CLI Tool

```bash
# Basic: transcribe for piano
python python/cli.py song.mp3

# Specify instrument
python python/cli.py song.mp3 --instrument violin

# From video file
python python/cli.py concert.mp4 --instrument flute

# Override tempo
python python/cli.py song.wav --tempo 100

# Show visualizations
python python/cli.py song.mp3 --show-plots

# MIDI output only
python python/cli.py song.mp3 --format midi

# List instruments
python python/cli.py --list-instruments
```

### Python API

```python
from python.transcriber import AudioAnalyzer, InstrumentTransposer, SheetMusicGenerator

# Analyze audio
analyzer = AudioAnalyzer()
analyzer.load("song.mp3")
analyzer.analyze()

# Print detected notes
analyzer.print_notes()

# Visualize
analyzer.plot_spectrogram()
analyzer.plot_notes()

# Transpose for violin
violin_notes = InstrumentTransposer.transpose(analyzer.notes, "violin")

# Generate sheet music
generator = SheetMusicGenerator(tempo=analyzer.tempo)
generator.generate_midi(analyzer.notes, "output.mid")
generator.generate_musicxml(analyzer.timed_notes, "output.xml")
```

### Generate Test Audio

```bash
python generate_test_audio.py
python python/cli.py test_melody.wav --instrument piano --show-plots
```

---

## Visualizations

### Spectrogram
Shows the frequency content of the audio over time.
The C++ FFT engine processes the audio into a time-frequency representation.

### Piano Roll
Shows detected notes as horizontal bars:
- **Y-axis**: MIDI note number (pitch)
- **X-axis**: Time (seconds)
- **Bar length**: Note duration

---

## Architecture

```
┌─────────────────────────────────────────────┐
│           Python Interface                   │
│  CLI / AudioAnalyzer / SheetMusicGenerator   │
├─────────────────────────────────────────────┤
│           Analysis Layer                     │
│  NoteDetector / RhythmAnalyzer /             │
│  InstrumentTransposer                        │
├─────────────────────────────────────────────┤
│           pybind11 Bridge                    │
├─────────────────────────────────────────────┤
│           C++ Audio Core                     │
│  FFT / Spectrogram / Pitch Detection /       │
│  Onset Detection / Spectral Flux             │
└─────────────────────────────────────────────┘
```

### Why C++ for Audio Processing?

Audio analysis involves heavy computation:
- **FFT**: O(n log n) complex operations per frame
- **Spectrogram**: Hundreds of FFT computations
- **Pitch Detection**: Peak finding across frequency bins

C++ handles these operations orders of magnitude faster than Python,
while pybind11 provides a seamless bridge to the Python ecosystem.

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_audio.py -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=python --cov-report=term-missing -v
```

---

## Supported Formats

### Input

| Format | Type |
|---|---|
| WAV, MP3, FLAC, OGG, M4A, AAC | Audio |
| MP4, AVI, MKV, MOV, WebM, FLV | Video |

### Output

| Format | Description | Open With |
|---|---|---|
| `.mid` | MIDI file | Any MIDI player, DAW |
| `.xml` | MusicXML | MuseScore, Finale, Sibelius |

---

## Algorithm Details

### FFT (Fast Fourier Transform)
Cooley-Tukey radix-2 implementation in C++.
Converts time-domain audio signal to frequency domain.

### Pitch Detection
1. Compute magnitude spectrum via FFT
2. Find dominant frequency peak
3. Map frequency to nearest musical note

### Onset Detection
1. Compute spectral flux between consecutive frames
2. Apply adaptive threshold (mean + k * std)
3. Find peaks in flux signal

### Rhythm Analysis
1. Estimate tempo from inter-onset intervals
2. Snap to nearest common tempo
3. Quantize note durations to standard values
   (whole, half, quarter, eighth, sixteenth)

---

## License

HomeMade Licence
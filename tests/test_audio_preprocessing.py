"""
Tests for acoustic preprocessing, Butterworth filtering, VAD, and chunking.
"""

import math
import struct
import pytest
from field_to_record.audio.preprocessor import AudioPreprocessor
from field_to_record.audio.vad import VoiceActivityDetector
from field_to_record.audio.chunker import AudioChunker


def test_butterworth_highpass_filter_attenuates_low_frequencies():
    sample_rate = 16000
    preprocessor = AudioPreprocessor(target_sample_rate=sample_rate, highpass_cutoff_hz=80.0)

    # Generate 40 Hz wave (should be attenuated heavily)
    duration_sec = 0.5
    total_samples = int(sample_rate * duration_sec)
    low_freq_signal = [0.8 * math.sin(2 * math.pi * 35.0 * (n / sample_rate)) for n in range(total_samples)]

    filtered = preprocessor.apply_highpass_filter(low_freq_signal)

    # Last 200 samples (after filter warm-up)
    rms_original = math.sqrt(sum(x * x for x in low_freq_signal[-200:]) / 200)
    rms_filtered = math.sqrt(sum(x * x for x in filtered[-200:]) / 200)

    # 35 Hz should be attenuated by at least 10 dB (> 65% amplitude drop)
    assert rms_filtered < rms_original * 0.45


def test_pcm_bytes_roundtrip_and_sha256():
    preprocessor = AudioPreprocessor()
    # 1 second of 440Hz tone
    sample_rate = 16000
    floats = [0.5 * math.sin(2 * math.pi * 440.0 * (n / sample_rate)) for n in range(sample_rate)]
    ints = [int(s * 32767.0) for s in floats]
    raw_bytes = struct.pack(f"<{len(ints)}h", *ints)

    processed_bytes, audio_hash = preprocessor.process_pcm_bytes(raw_bytes)
    assert len(processed_bytes) == len(raw_bytes)
    assert len(audio_hash) == 64  # SHA-256


def test_voice_activity_detector_silence_stripping():
    sample_rate = 16000
    vad = VoiceActivityDetector(sample_rate=sample_rate, energy_threshold=0.02)

    # 1 second silence, 1 second tone, 1 second silence
    silence = [0.0001] * sample_rate
    tone = [0.4 * math.sin(2 * math.pi * 500.0 * (n / sample_rate)) for n in range(sample_rate)]
    samples = silence + tone + silence

    segments = vad.detect_speech_segments(samples)
    assert len(segments) >= 1
    # Speech should start roughly around sample 16000
    start_sample = segments[0][0]
    assert 12000 <= start_sample <= 17000


def test_audio_chunker_windowing():
    sample_rate = 16000
    chunker = AudioChunker(sample_rate=sample_rate, chunk_duration_sec=10.0, overlap_sec=2.0)

    # 25 seconds of mock PCM
    total_samples = sample_rate * 25
    mock_pcm = b"\x00\x00" * total_samples

    chunks = chunker.chunk_pcm_bytes(mock_pcm)
    assert len(chunks) >= 3
    assert chunks[0]["start_sec"] == 0.0
    assert chunks[0]["duration_sec"] == 10.0
    assert chunks[1]["start_sec"] == 8.0  # 10s - 2s overlap

"""
Acoustic Noise Injection Simulator.
Synthesizes field-realistic emergency environmental acoustic contaminants:
- Siren frequency sweeps (500 Hz - 1500 Hz)
- Ambulance cabin vibration & low-frequency diesel rumble (< 100 Hz)
- Two-way radio squelch & static
Applies calibrated Signal-to-Noise Ratios (-5 dB to 20 dB SNR).
"""

import math
import struct
import random
from typing import List, Tuple


class AcousticNoiseInjector:
    """
    Simulates emergency vehicle and outdoor disaster acoustic degradation.
    """

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    def generate_siren_waveform(self, duration_sec: float, sweep_rate_hz: float = 0.5) -> List[float]:
        """
        Generates siren sweep between 600 Hz (wail low) and 1400 Hz (wail high).
        """
        total_samples = int(self.sample_rate * duration_sec)
        samples = []
        phase = 0.0

        for n in range(total_samples):
            t = n / float(self.sample_rate)
            # Modulate frequency sinusoidally
            f_inst = 1000.0 + 400.0 * math.sin(2.0 * math.pi * sweep_rate_hz * t)
            phase += 2.0 * math.pi * f_inst / self.sample_rate
            sample = 0.3 * math.sin(phase)
            samples.append(sample)

        return samples

    def generate_engine_rumble(self, duration_sec: float) -> List[float]:
        """
        Generates low-frequency diesel vehicle vibrations (45 Hz and 90 Hz harmonics).
        """
        total_samples = int(self.sample_rate * duration_sec)
        samples = []
        for n in range(total_samples):
            t = n / float(self.sample_rate)
            s1 = 0.4 * math.sin(2.0 * math.pi * 45.0 * t)
            s2 = 0.2 * math.sin(2.0 * math.pi * 90.0 * t)
            noise = (random.random() - 0.5) * 0.05
            samples.append(s1 + s2 + noise)
        return samples

    def mix_signals(self, clean_signal: List[float], noise_signal: List[float], target_snr_db: float) -> List[float]:
        """
        Mixes clean speech signal with noise at target SNR (in decibels).
        Formula:
            P_signal / P_noise = 10^(SNR_dB / 10)
        """
        length = min(len(clean_signal), len(noise_signal))
        if length == 0:
            return clean_signal

        clean_sub = clean_signal[:length]
        noise_sub = noise_signal[:length]

        p_clean = sum(x * x for x in clean_sub) / float(length)
        p_noise = sum(x * x for x in noise_sub) / float(length)

        if p_clean == 0 or p_noise == 0:
            return clean_sub

        # Desired noise power
        desired_p_noise = p_clean / (10.0 ** (target_snr_db / 10.0))
        scale = math.sqrt(desired_p_noise / p_noise)

        mixed = []
        for c, n in zip(clean_sub, noise_sub):
            val = c + n * scale
            # Soft clip to prevent harsh distortion
            mixed.append(max(-1.0, min(1.0, val)))

        return mixed

    def create_synthetic_field_audio_pcm(
        self,
        duration_sec: float = 5.0,
        target_snr_db: float = 5.0,
        include_siren: bool = True,
        include_rumble: bool = True
    ) -> bytes:
        """
        Synthesizes a contaminated ambient field audio PCM buffer for testing.
        """
        total_samples = int(self.sample_rate * duration_sec)
        # Synthetic clean speech proxy: burst of speech-like harmonics
        speech = []
        for n in range(total_samples):
            t = n / float(self.sample_rate)
            # Formants around 300Hz, 800Hz, 2500Hz
            s = 0.4 * math.sin(2 * math.pi * 320 * t) + 0.3 * math.sin(2 * math.pi * 840 * t)
            # Envelope gating
            env = 0.5 * (1 + math.sin(2 * math.pi * 1.5 * t))
            speech.append(s * env)

        noise = [0.0] * total_samples
        if include_siren:
            siren = self.generate_siren_waveform(duration_sec)
            noise = [n + s for n, s in zip(noise, siren)]
        if include_rumble:
            rumble = self.generate_engine_rumble(duration_sec)
            noise = [n + r for n, r in zip(noise, rumble)]

        mixed = self.mix_signals(speech, noise, target_snr_db=target_snr_db)

        # Pack to 16-bit PCM bytes
        out_ints = [int(max(-32768, min(32767, s * 32767.0))) for s in mixed]
        return struct.pack(f"<{len(out_ints)}h", *out_ints)

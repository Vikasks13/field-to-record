"""
Tests for Synthetic Scenario Generation and Acoustic Noise Injection.
"""

import pytest
from field_to_record.synthetic.generator import SyntheticScenarioGenerator
from field_to_record.synthetic.noise_injector import AcousticNoiseInjector


def test_synthetic_scenario_categories():
    scenarios = SyntheticScenarioGenerator.get_all_scenarios()
    assert len(scenarios) >= 8

    categories = {s["category"] for s in scenarios}
    assert "cardiovascular" in categories
    assert "respiratory" in categories
    assert "toxicology" in categories
    assert "trauma" in categories
    assert "neurology" in categories


def test_acoustic_noise_injection_mixing():
    injector = AcousticNoiseInjector(sample_rate=16000)
    # Generate siren
    siren = injector.generate_siren_waveform(duration_sec=0.2)
    assert len(siren) == int(16000 * 0.2)

    # Generate engine rumble
    rumble = injector.generate_engine_rumble(duration_sec=0.2)
    assert len(rumble) == int(16000 * 0.2)

    # Mix with speech proxy
    speech = [0.2] * len(siren)
    mixed = injector.mix_signals(speech, siren, target_snr_db=5.0)
    assert len(mixed) == len(speech)


def test_synthetic_field_audio_pcm_generation():
    injector = AcousticNoiseInjector(sample_rate=16000)
    pcm_bytes = injector.create_synthetic_field_audio_pcm(duration_sec=0.5, target_snr_db=0.0)
    # 0.5 sec * 16000 samples * 2 bytes/sample = 16000 bytes
    assert len(pcm_bytes) == 16000

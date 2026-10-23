"""
Tests for Clinical Safety Guardrails, Plausibility, and LASA Detection.
"""

import pytest
from field_to_record.ontology.safety import ClinicalSafetyGuard


def test_tall_man_lettering():
    assert ClinicalSafetyGuard.get_tall_man_lettering("epinephrine") == "EPINephrine"
    assert ClinicalSafetyGuard.get_tall_man_lettering("ephedrine") == "ePHEDrine"
    assert ClinicalSafetyGuard.get_tall_man_lettering("morphine") == "morPHINE"
    assert ClinicalSafetyGuard.get_tall_man_lettering("hydromorphone") == "HYDROmorphone"


def test_dosage_bounds_outlier_detection():
    # Safe Epinephrine dose
    is_outlier, alert = ClinicalSafetyGuard.validate_dosage("epinephrine", route="IV", dose=1.0, unit="mg")
    assert not is_outlier
    assert alert is None

    # Dangerous 10 mg Epinephrine dose
    is_outlier_high, alert_high = ClinicalSafetyGuard.validate_dosage("epinephrine", route="IV", dose=10.0, unit="mg")
    assert is_outlier_high
    assert "CRITICAL DOSAGE WARNING" in alert_high


def test_route_conflict_during_cpr():
    conflict = ClinicalSafetyGuard.check_route_conflict("aspirin", route="PO", ongoing_cpr=True)
    assert conflict is not None
    assert "ROUTE CONFLICT" in conflict


def test_look_alike_sound_alike_detection():
    alerts = ClinicalSafetyGuard.detect_look_alike_sound_alike("epinephrine")
    assert len(alerts) > 0
    assert any("ePHEDrine" in a for a in alerts)

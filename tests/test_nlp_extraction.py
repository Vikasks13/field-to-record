"""
Tests for Clinical Named Entity Recognition (NER) & Relation Binding.
"""

import pytest
from field_to_record.nlp.extractor import EdgeClinicalExtractor


def test_extract_medications_basic_cardiac():
    extractor = EdgeClinicalExtractor()
    transcript = "Administered 1 mg of epinephrine IV and gave 300 mg of amiodarone IV push."
    meds = extractor.extract_medications(transcript)

    assert len(meds) == 2
    epi = next((m for m in meds if "epinephrine" in m.drug_name.lower()), None)
    amio = next((m for m in meds if "amiodarone" in m.drug_name.lower()), None)

    assert epi is not None
    assert epi.dosage_value == 1.0
    assert epi.dosage_unit == "mg"
    assert epi.route == "IV"
    assert epi.rxnorm_code == "727345"  # Epinephrine 0.1 mg/mL for IV

    assert amio is not None
    assert amio.dosage_value == 300.0
    assert amio.dosage_unit == "mg"
    assert amio.route == "IV"


def test_extract_medications_overdose_narcan():
    extractor = EdgeClinicalExtractor()
    transcript = "Patient unresponsive, administered 2 mg of Narcan IN."
    meds = extractor.extract_medications(transcript)

    assert len(meds) == 1
    narcan = meds[0]
    assert narcan.drug_name.lower() == "naloxone"
    assert narcan.dosage_value == 2.0
    assert narcan.route == "IN"
    assert narcan.rxnorm_code == "1656328"


def test_extract_procedures_and_anatomical_sites():
    extractor = EdgeClinicalExtractor()
    transcript = "Initiated CPR and BVM ventilation. Established IV access left antecubital."
    procs = extractor.extract_procedures(transcript)

    assert len(procs) >= 3
    names = [p.procedure_name for p in procs]
    assert "Cardiopulmonary resuscitation" in names
    assert "Bag-valve-mask ventilation" in names
    assert "Intravenous catheterization" in names

    iv_proc = next(p for p in procs if p.procedure_name == "Intravenous catheterization")
    assert iv_proc.anatomical_site is not None
    assert "left antecubital" in iv_proc.anatomical_site.lower()


def test_extract_observations_vitals():
    extractor = EdgeClinicalExtractor()
    transcript = "Patient GCS 12, SpO2 94%, heart rate 104, blood pressure 130/85."
    obs = extractor.extract_observations(transcript)

    codes = {o.code: o.value for o in obs}
    assert codes.get("GCS") == 12.0
    assert codes.get("SPO2") == 94.0
    assert codes.get("BP_SYS") == 130.0
    assert codes.get("BP_DIA") == 85.0

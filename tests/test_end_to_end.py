"""
End-to-End integration test simulating complete edge pre-hospital pipeline:
Acoustic Ingest -> Denoising -> Clinical NER -> Ontology Grounding ->
Safety Checks -> Audit Block Hash -> DB Persistence -> FHIR & SBAR Export.
"""

import os
import pytest
from field_to_record.schemas import ClinicalFieldRecord, current_iso_timestamp
from field_to_record.audio.preprocessor import AudioPreprocessor
from field_to_record.nlp.extractor import EdgeClinicalExtractor
from field_to_record.ontology.grounder import MedicalOntologyGrounder
from field_to_record.audit.ledger import CryptographicAuditLedger
from field_to_record.storage.database import LocalClinicalDatabase
from field_to_record.fhir.serializer import FHIRLiteSerializer
from field_to_record.fhir.validator import FHIRBundleValidator
from field_to_record.reports.sbar import SBARReportGenerator


def test_full_field_to_record_pipeline(tmp_path):
    # 1. Simulate noisy field audio PCM
    preprocessor = AudioPreprocessor()
    mock_pcm = b"\x12\x34" * 16000  # 1s of audio
    processed_pcm, audio_hash = preprocessor.process_pcm_bytes(mock_pcm)
    assert len(audio_hash) == 64

    # 2. Field Transcript (either from ASR or dictation)
    transcript = (
        "Medic 7 on scene with 48-year-old male in cardiac arrest. "
        "Started CPR and BVM ventilation. Administered 1 mg of epinephrine IV at 14:02. "
        "Delivered defibrillation 200 Joules. Administered 300 mg of amiodarone IV. "
        "Also gave 2 mg of Narcan IN. SpO2 92%."
    )

    # 3. Clinical Extraction and Grounding
    test_db_path = str(tmp_path / "ontology.db")
    grounder = MedicalOntologyGrounder(db_path=test_db_path)
    extractor = EdgeClinicalExtractor(grounder=grounder)
    extraction = extractor.extract_all(transcript)

    meds = extraction["medications"]
    procs = extraction["procedures"]
    obs = extraction["observations"]

    assert len(meds) == 3  # Epinephrine, Amiodarone, Narcan
    assert len(procs) >= 3  # CPR, BVM, Defibrillation
    assert len(obs) >= 1   # SpO2

    # 4. Cryptographic Audit Block
    ledger = CryptographicAuditLedger(device_id="PARAMEDIC-UNIT-07")
    block = ledger.append_block(
        raw_transcript=transcript,
        structured_payload={
            "medications": [m.model_dump() for m in meds],
            "procedures": [p.model_dump() for p in procs],
            "observations": [o.model_dump() for o in obs],
        },
        audio_sha256=audio_hash,
    )
    assert block.prev_hash == "0" * 64
    valid, err = ledger.verify_integrity()
    assert valid is True

    # 5. Build and Persist Run Record
    records_db_path = str(tmp_path / "records.db")
    db = LocalClinicalDatabase(db_path=records_db_path)

    run_record = ClinicalFieldRecord(
        record_id="ems-run-e2e-001",
        patient_identifier="Male (~48yo) Priority-1",
        session_start=current_iso_timestamp(),
        raw_transcript=transcript,
        denoised_audio_hash=audio_hash,
        medications=meds,
        procedures=procs,
        observations=obs,
        audit_hash_chain=block.block_hash,
        audit_blocks=ledger.blocks,
    )
    db.save_record(run_record)

    # Verify retrieval
    loaded = db.get_record("ems-run-e2e-001")
    assert loaded is not None
    assert loaded.record_id == "ems-run-e2e-001"
    assert len(loaded.medications) == 3

    # 6. FHIR R4 Bundle Validation
    fhir_bundle = FHIRLiteSerializer.serialize_bundle(loaded)
    is_valid_fhir, fhir_errs = FHIRBundleValidator.validate_bundle(fhir_bundle)
    assert is_valid_fhir is True
    assert len(fhir_errs) == 0

    # 7. SBAR Handover Document
    sbar = SBARReportGenerator.generate(loaded)
    assert "PRE-HOSPITAL EMERGENCY TRANSFER OF CARE" in sbar
    assert "EPINephrine" in sbar
    assert "amiODAROne" in sbar

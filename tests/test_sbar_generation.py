"""
Tests for SBAR and SOAP Clinical Handover Generators.
"""

import pytest
from field_to_record.schemas import ClinicalFieldRecord, MedicationEvent, ProcedureEvent
from field_to_record.reports.sbar import SBARReportGenerator
from field_to_record.reports.soap import SOAPReportGenerator


def test_sbar_report_generation():
    record = ClinicalFieldRecord(
        record_id="ems-run-test-01",
        patient_identifier="Unknown Male (~35yo)",
        raw_transcript="Found patient in cardiac arrest. Administered 1 mg epinephrine IV.",
        medications=[
            MedicationEvent(
                raw_text="1 mg epinephrine IV",
                drug_name="Epinephrine",
                tall_man_name="EPINephrine",
                rxnorm_code="727345",
                dosage_value=1.0,
                dosage_unit="mg",
                route="IV",
            )
        ],
        procedures=[
            ProcedureEvent(
                raw_text="CPR",
                procedure_name="Cardiopulmonary resuscitation",
                snomed_code="89666000",
            )
        ],
    )

    report = SBARReportGenerator.generate(record)
    assert "SBAR HANDOFF" in report
    assert "EPINephrine" in report
    assert "Cardiopulmonary resuscitation" in report
    assert "[1. SITUATION]" in report
    assert "[4. RECOMMENDATION" in report


def test_soap_note_generation():
    record = ClinicalFieldRecord(
        record_id="ems-run-test-02",
        raw_transcript="Administered 2 mg Narcan IN for opioid toxidrome.",
    )
    soap = SOAPReportGenerator.generate(record)
    assert "[SUBJECTIVE]" in soap
    assert "[OBJECTIVE]" in soap
    assert "[ASSESSMENT]" in soap
    assert "[PLAN]" in soap

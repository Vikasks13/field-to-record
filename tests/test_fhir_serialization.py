"""
Tests for HL7 FHIR R4 Bundle Serialization and Schema Validation.
"""

import pytest
from field_to_record.schemas import ClinicalFieldRecord, MedicationEvent, ProcedureEvent, ObservationEvent
from field_to_record.fhir.serializer import FHIRLiteSerializer
from field_to_record.fhir.validator import FHIRBundleValidator


def test_fhir_bundle_serialization_and_validation():
    record = ClinicalFieldRecord(
        record_id="ems-run-20261023-0001",
        patient_identifier="John Doe (~45yo)",
        raw_transcript="Administered 2 mg Narcan IN. Performed BVM ventilation.",
        medications=[
            MedicationEvent(
                raw_text="2 mg Narcan IN",
                drug_name="Naloxone",
                rxnorm_code="1656328",
                rxnorm_display="Naloxone Hydrochloride 2 MG Nasal Spray",
                dosage_value=2.0,
                dosage_unit="mg",
                route="IN",
                snomed_route_code="46713006",
            )
        ],
        procedures=[
            ProcedureEvent(
                raw_text="BVM ventilation",
                procedure_name="Bag-valve-mask ventilation",
                snomed_code="42550007",
            )
        ],
        observations=[
            ObservationEvent(
                code="SPO2",
                display="Oxygen Saturation",
                value=97.0,
                unit="%",
            )
        ],
    )

    bundle = FHIRLiteSerializer.serialize_bundle(record)

    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    assert len(bundle["entry"]) == 3

    # Check validator
    is_valid, errors = FHIRBundleValidator.validate_bundle(bundle)
    assert is_valid is True
    assert len(errors) == 0

    # Inspect MedicationAdministration entry
    med_admin = bundle["entry"][0]["resource"]
    assert med_admin["resourceType"] == "MedicationAdministration"
    assert med_admin["status"] == "completed"
    assert med_admin["dosage"]["dose"]["value"] == 2.0
    assert med_admin["dosage"]["route"]["coding"][0]["code"] == "46713006"

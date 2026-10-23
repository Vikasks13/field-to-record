"""
NEMSIS v3.5 (National EMS Information System) JSON Mapper.
Aligns pre-hospital documentation with state and national registry reporting standards.
"""

from typing import Dict, Any, List
from field_to_record.schemas import ClinicalFieldRecord


class NEMSISv35Mapper:
    """
    Serializes ClinicalFieldRecord into NEMSIS v3.5 compliant JSON structure.
    """

    @staticmethod
    def to_nemsis_json(record: ClinicalFieldRecord) -> Dict[str, Any]:
        """Maps record entities into NEMSIS v3.5 data dictionary elements."""
        nemsis_meds: List[Dict[str, Any]] = []
        for idx, med in enumerate(record.medications):
            nemsis_meds.append({
                "eMedications.01": med.timestamp,
                "eMedications.02": f"MED-{idx + 1:03d}",
                "eMedications.03": med.rxnorm_code or "9999999",  # RxCUI
                "eMedications.03_description": med.rxnorm_display or med.drug_name,
                "eMedications.04": med.route,  # Route
                "eMedications.05": med.dosage_value,  # Dosage
                "eMedications.06": med.dosage_unit,  # Unit
                "eMedications.07": "Administered Prior to Arrival" if False else "Order Confirmed",
            })

        nemsis_procs: List[Dict[str, Any]] = []
        for idx, proc in enumerate(record.procedures):
            nemsis_procs.append({
                "eProcedures.01": proc.timestamp,
                "eProcedures.02": f"PROC-{idx + 1:03d}",
                "eProcedures.03": proc.snomed_code or "9999999",  # SNOMED CT
                "eProcedures.03_description": proc.snomed_display or proc.procedure_name,
                "eProcedures.05": 1 if proc.success else 0,  # Successful
                "eProcedures.08": proc.anatomical_site or "Unspecified",
            })

        nemsis_vitals: List[Dict[str, Any]] = []
        for obs in record.observations:
            nemsis_vitals.append({
                "eVitals.01": obs.timestamp,
                "eVitals.type": obs.code,
                "eVitals.value": obs.value,
                "eVitals.unit": obs.unit,
            })

        return {
            "nemsisStandard": "v3.5.0",
            "eRecord": {
                "eRecord.01": record.record_id,
                "softwareCreator": "Field-to-Record Offline Engine",
                "softwareVersion": "0.1.0",
                "cryptographicChainHash": record.audit_hash_chain,
            },
            "ePatient": {
                "ePatient.identifier": record.patient_identifier,
            },
            "eMedicationsGroup": {
                "eMedications": nemsis_meds,
            },
            "eProceduresGroup": {
                "eProcedures": nemsis_procs,
            },
            "eVitalsGroup": {
                "eVitals": nemsis_vitals,
            },
            "eNarrative": {
                "eNarrative.01": record.raw_transcript,
            },
        }

"""
HL7 FHIR Release 4 (R4) Lite Serializer.
Converts extracted pre-hospital clinical events into standard FHIR R4 Bundle resources
(MedicationAdministration, Procedure, Observation) ready for seamless ingest by hospital EHRs (Epic, Cerner).
"""

import uuid
from typing import Dict, Any, List
from field_to_record.schemas import ClinicalFieldRecord, MedicationEvent, ProcedureEvent, ObservationEvent


class FHIRLiteSerializer:
    """
    Serializes ClinicalFieldRecord into official HL7 FHIR R4 collection bundle.
    """

    @staticmethod
    def _create_medication_admin_resource(med: MedicationEvent, patient_display: str, audio_hash: str) -> Dict[str, Any]:
        res_id = f"med-admin-{uuid.uuid4().hex[:8]}"
        resource: Dict[str, Any] = {
            "resourceType": "MedicationAdministration",
            "id": res_id,
            "status": "completed",
            "medicationCodeableConcept": {
                "coding": [
                    {
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": med.rxnorm_code or "UNKNOWN",
                        "display": med.rxnorm_display or med.drug_name,
                    }
                ],
                "text": med.raw_text,
            },
            "subject": {"display": patient_display},
            "effectiveDateTime": med.timestamp,
            "dosage": {
                "text": f"{med.dosage_value} {med.dosage_unit} via {med.route}",
                "dose": {
                    "value": med.dosage_value,
                    "unit": med.dosage_unit,
                    "system": "http://unitsofmeasure.org",
                    "code": med.dosage_unit,
                },
            },
            "extension": [
                {
                    "url": "http://ems.audit/provenance",
                    "valueString": f"Spoken: '{med.raw_text}' | AudioHash: {audio_hash[:16]}... | Confidence: {med.confidence_score}",
                }
            ],
        }

        # Route coding
        if med.snomed_route_code:
            resource["dosage"]["route"] = {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": med.snomed_route_code,
                        "display": med.snomed_route_display or med.route,
                    }
                ]
            }

        return resource

    @staticmethod
    def _create_procedure_resource(proc: ProcedureEvent, patient_display: str) -> Dict[str, Any]:
        res_id = f"proc-{uuid.uuid4().hex[:8]}"
        resource: Dict[str, Any] = {
            "resourceType": "Procedure",
            "id": res_id,
            "status": "completed",
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": proc.snomed_code or "UNKNOWN",
                        "display": proc.snomed_display or proc.procedure_name,
                    }
                ],
                "text": proc.procedure_name,
            },
            "subject": {"display": patient_display},
            "performedDateTime": proc.timestamp,
        }

        if proc.anatomical_site:
            resource["bodySite"] = [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": proc.anatomical_site_snomed or "89837001",
                            "display": proc.anatomical_site,
                        }
                    ],
                    "text": proc.anatomical_site,
                }
            ]

        return resource

    @staticmethod
    def _create_observation_resource(obs: ObservationEvent, patient_display: str) -> Dict[str, Any]:
        res_id = f"obs-{uuid.uuid4().hex[:8]}"
        return {
            "resourceType": "Observation",
            "id": res_id,
            "status": "final",
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org" if obs.loinc_code else "http://ems.local/codes",
                        "code": obs.loinc_code or obs.code,
                        "display": obs.display,
                    }
                ],
                "text": obs.display,
            },
            "subject": {"display": patient_display},
            "effectiveDateTime": obs.timestamp,
            "valueQuantity": {
                "value": obs.value,
                "unit": obs.unit,
                "system": "http://unitsofmeasure.org",
                "code": obs.unit,
            },
        }

    @classmethod
    def serialize_bundle(cls, record: ClinicalFieldRecord) -> Dict[str, Any]:
        """
        Transforms record into a complete FHIR R4 Bundle.
        """
        entries = []
        audio_hash = record.denoised_audio_hash or "0" * 64

        # 1. Medications
        for med in record.medications:
            res = cls._create_medication_admin_resource(med, record.patient_identifier, audio_hash)
            entries.append({
                "fullUrl": f"urn:uuid:{res['id']}",
                "resource": res,
            })

        # 2. Procedures
        for proc in record.procedures:
            res = cls._create_procedure_resource(proc, record.patient_identifier)
            entries.append({
                "fullUrl": f"urn:uuid:{res['id']}",
                "resource": res,
            })

        # 3. Observations
        for obs in record.observations:
            res = cls._create_observation_resource(obs, record.patient_identifier)
            entries.append({
                "fullUrl": f"urn:uuid:{res['id']}",
                "resource": res,
            })

        bundle: Dict[str, Any] = {
            "resourceType": "Bundle",
            "id": record.record_id,
            "type": "collection",
            "timestamp": record.session_start,
            "identifier": {
                "system": "http://ems.jurisdiction/run-id",
                "value": record.record_id,
            },
            "meta": {
                "tag": [
                    {"system": "http://ems.audit/merkle-root", "code": record.audit_hash_chain}
                ]
            },
            "entry": entries,
        }
        return bundle

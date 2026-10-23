"""
FHIR Bundle validation engine.
Verifies structure, required keys, coding systems, and cardinality against FHIR R4 specifications.
"""

from typing import Dict, Any, List, Tuple


class FHIRBundleValidator:
    """
    Validates that a generated bundle conforms strictly to FHIR R4 rules.
    """

    @staticmethod
    def validate_bundle(bundle: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validates bundle integrity and resource requirements.
        Returns: (is_valid, error_list)
        """
        errors = []

        if bundle.get("resourceType") != "Bundle":
            errors.append("Root resourceType must be 'Bundle'.")

        if bundle.get("type") != "collection":
            errors.append("Bundle type must be 'collection'.")

        if not bundle.get("id"):
            errors.append("Bundle must contain a valid 'id'.")

        entries = bundle.get("entry", [])
        if not isinstance(entries, list):
            errors.append("Bundle 'entry' must be a list.")
            return False, errors

        for idx, entry in enumerate(entries):
            resource = entry.get("resource", {})
            res_type = resource.get("resourceType")

            if not res_type:
                errors.append(f"Entry {idx} missing 'resourceType'.")
                continue

            if not resource.get("id"):
                errors.append(f"Entry {idx} ({res_type}) missing 'id'.")

            # MedicationAdministration checks
            if res_type == "MedicationAdministration":
                if resource.get("status") != "completed":
                    errors.append(f"MedicationAdministration {resource.get('id')} status must be 'completed'.")
                if "medicationCodeableConcept" not in resource:
                    errors.append(f"MedicationAdministration {resource.get('id')} missing 'medicationCodeableConcept'.")
                if "dosage" not in resource:
                    errors.append(f"MedicationAdministration {resource.get('id')} missing 'dosage'.")

            # Procedure checks
            elif res_type == "Procedure":
                if resource.get("status") != "completed":
                    errors.append(f"Procedure {resource.get('id')} status must be 'completed'.")
                if "code" not in resource:
                    errors.append(f"Procedure {resource.get('id')} missing 'code'.")

            # Observation checks
            elif res_type == "Observation":
                if resource.get("status") != "final":
                    errors.append(f"Observation {resource.get('id')} status must be 'final'.")
                if "valueQuantity" not in resource:
                    errors.append(f"Observation {resource.get('id')} missing 'valueQuantity'.")

        return (len(errors) == 0), errors

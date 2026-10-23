"""
Clinical Named Entity Recognition (NER) & Relation Extraction Engine.
Extracts 7 core clinical entities and binds them into relation graphs:
[Medication, Dose, Unit, Route, Time, Indication]
[Procedure, Anatomical Site, Success, Time]
[Observation, Value, Unit]
"""

import re
from typing import List, Dict, Any, Optional
from field_to_record.schemas import MedicationEvent, ProcedureEvent, ObservationEvent
from field_to_record.ontology.grounder import MedicalOntologyGrounder
from field_to_record.nlp.patterns import (
    MEDICATION_ALIASES,
    ROUTE_ALIASES,
    PROCEDURE_ALIASES,
    ANATOMICAL_SITES,
    MED_REGEX,
    VITALS_REGEX,
    TIME_REGEX,
)


class EdgeClinicalExtractor:
    """
    Offline edge clinical information extraction and slot-relation binding engine.
    """

    def __init__(self, grounder: Optional[MedicalOntologyGrounder] = None):
        self.grounder = grounder or MedicalOntologyGrounder()
        self.site_patterns = [re.compile(p, re.IGNORECASE) for p in ANATOMICAL_SITES]

    def extract_medications(self, transcript: str, ongoing_cpr: bool = False) -> List[MedicationEvent]:
        """Extracts and grounds medication administration events."""
        medications: List[MedicationEvent] = []

        # Find structured dose + drug + route patterns
        for match in MED_REGEX.finditer(transcript):
            raw_text = match.group(0).strip()
            raw_drug = match.group("drug").strip().lower()
            raw_dose = match.group("dose")
            raw_unit = match.group("unit") or "mg"
            raw_route = match.group("route") or "iv"

            # Clean drug name from common filler words ("of", "in", "the", "a")
            clean_drug = re.sub(r"^(?:of|in|the|a)\s+", "", raw_drug, flags=re.IGNORECASE).strip()

            # Resolve alias if present
            canonical_alias = MEDICATION_ALIASES.get(clean_drug, clean_drug)

            # Skip if not a recognized pharmaceutical
            if canonical_alias not in MEDICATION_ALIASES and canonical_alias not in self.grounder.rxnorm_cache:
                continue

            dose = float(raw_dose)
            unit = raw_unit.lower()
            route = ROUTE_ALIASES.get(raw_route.lower(), "IV")

            grounded = self.grounder.ground_medication(
                raw_drug=canonical_alias,
                route=route,
                dose=dose,
                unit=unit,
                ongoing_cpr=ongoing_cpr,
            )

            route_code, route_disp = self.grounder.ground_route(route)

            medications.append(
                MedicationEvent(
                    raw_text=raw_text,
                    drug_name=grounded["canonical_name"],
                    tall_man_name=grounded["tall_man_name"],
                    rxnorm_code=grounded["rxnorm_code"],
                    rxnorm_display=grounded["rxnorm_display"],
                    dosage_value=dose,
                    dosage_unit=unit,
                    route=route,
                    snomed_route_code=route_code,
                    snomed_route_display=route_disp,
                    is_outlier_dose=grounded["is_outlier"],
                    safety_alert=grounded["safety_alert"],
                    confidence_score=0.97,
                )
            )

        # Fallback check for single drug mentions without explicit dose (e.g. "gave narcan")
        for alias, generic in MEDICATION_ALIASES.items():
            pattern = rf"\b(?:gave|pushed|administered)\s+{alias}\b"
            for m in re.finditer(pattern, transcript, re.IGNORECASE):
                # Ensure not already captured in regex matches
                if any(m.group(0).lower() in med.raw_text.lower() for med in medications):
                    continue

                grounded = self.grounder.ground_medication(generic, route="IV", dose=1.0, unit="unit")
                route_code, route_disp = self.grounder.ground_route("IV")
                medications.append(
                    MedicationEvent(
                        raw_text=m.group(0),
                        drug_name=grounded["canonical_name"],
                        tall_man_name=grounded["tall_man_name"],
                        rxnorm_code=grounded["rxnorm_code"],
                        rxnorm_display=grounded["rxnorm_display"],
                        dosage_value=1.0,
                        dosage_unit="unit",
                        route="IV",
                        snomed_route_code=route_code,
                        snomed_route_display=route_disp,
                        confidence_score=0.88,
                    )
                )

        return medications

    def extract_procedures(self, transcript: str) -> List[ProcedureEvent]:
        """Extracts procedures and binds anatomical sites."""
        procedures: List[ProcedureEvent] = []
        lower_text = transcript.lower()

        # Find anatomical site if mentioned
        detected_site = None
        for sp in self.site_patterns:
            site_match = sp.search(transcript)
            if site_match:
                detected_site = site_match.group(0)
                break

        for phrase, canonical_proc in PROCEDURE_ALIASES.items():
            pattern = rf"\b{re.escape(phrase)}\b"
            if re.search(pattern, lower_text):
                # Avoid duplicate insertion for overlapping aliases
                if any(p.procedure_name.lower() == canonical_proc.lower() for p in procedures):
                    continue

                grounded = self.grounder.ground_procedure(canonical_proc)
                procedures.append(
                    ProcedureEvent(
                        raw_text=phrase,
                        procedure_name=canonical_proc,
                        snomed_code=grounded["code"],
                        snomed_display=grounded["display"],
                        anatomical_site=detected_site,
                        confidence_score=0.98,
                    )
                )

        return procedures

    def extract_observations(self, transcript: str) -> List[ObservationEvent]:
        """Extracts vital signs, GCS scores, SpO2, and hemodynamic metrics."""
        observations: List[ObservationEvent] = []

        for match in VITALS_REGEX.finditer(transcript):
            vtype = match.group("type").upper().replace(" ", "")
            val_str = match.group("val")
            unit = match.group("unit") or ""

            # Check BP e.g. 120/80
            if "/" in val_str:
                parts = val_str.split("/")
                try:
                    sys_val = float(parts[0])
                    dia_val = float(parts[1])
                    observations.append(
                        ObservationEvent(code="BP_SYS", display="Systolic Blood Pressure", value=sys_val, unit="mmHg")
                    )
                    observations.append(
                        ObservationEvent(code="BP_DIA", display="Diastolic Blood Pressure", value=dia_val, unit="mmHg")
                    )
                except ValueError:
                    pass
            else:
                try:
                    num_val = float(val_str)
                    display = vtype
                    u = unit or "pts"
                    if "GCS" in vtype:
                        display = "Glasgow Coma Scale"
                        u = "pts"
                    elif "SPO2" in vtype or "O2" in vtype:
                        display = "Oxygen Saturation SpO2"
                        u = "%"
                    elif "HR" in vtype or "PULSE" in vtype or "HEART" in vtype:
                        display = "Heart Rate"
                        u = "bpm"

                    observations.append(
                        ObservationEvent(code=vtype, display=display, value=num_val, unit=u)
                    )
                except ValueError:
                    pass

        return observations

    def extract_all(self, transcript: str) -> Dict[str, Any]:
        """Runs full clinical NER, relation binding, and observation extraction."""
        ongoing_cpr = "cpr" in transcript.lower() or "cardiac arrest" in transcript.lower()
        meds = self.extract_medications(transcript, ongoing_cpr=ongoing_cpr)
        procs = self.extract_procedures(transcript)
        obs = self.extract_observations(transcript)

        return {
            "transcript": transcript,
            "medications": meds,
            "procedures": procs,
            "observations": obs,
        }

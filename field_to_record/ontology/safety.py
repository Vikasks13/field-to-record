"""
Clinical Safety, Sanity Bounds, and Guardrails Engine.
Validates:
1. Adult standard dosage ranges (flags high-hazard overdose or underdose outliers).
2. Administration route feasibility (e.g. prevents oral route during CPR).
3. Look-Alike/Sound-Alike (LASA) drug confusion with FDA Tall Man lettering.
"""

from typing import Dict, Any, Optional, Tuple, List

# FDA Tall Man Lettering mapping for high-alert medications
TALL_MAN_MAP = {
    "epinephrine": "EPINephrine",
    "ephedrine": "ePHEDrine",
    "hydromorphone": "HYDROmorphone",
    "morphine": "morPHINE",
    "amiodarone": "amiODAROne",
    "amitriptyline": "aMIOtriptyline",
    "dobutamine": "DOBUtamine",
    "dopamine": "DOPAmine",
    "nicardipine": "NiCARdipine",
    "nifedipine": "NIFEdipine",
    "prednisone": "predniSONE",
    "prednisolone": "prednisoLONE",
    "naloxone": "nalOXone",
    "naltrexone": "nalTREXone",
    "fentanyl": "fentaNYL",
    "midazolam": "midazolAM",
}

# Standard adult EMS emergency dosage ranges (min, max, standard_unit)
DOSAGE_BOUNDS: Dict[str, Dict[str, Any]] = {
    "epinephrine": {
        "IV": {"min": 0.1, "max": 1.0, "unit": "mg", "hazard_threshold": 1.5},
        "IM": {"min": 0.15, "max": 0.5, "unit": "mg", "hazard_threshold": 1.0},
        "IO": {"min": 0.1, "max": 1.0, "unit": "mg", "hazard_threshold": 1.5},
    },
    "naloxone": {
        "IN": {"min": 0.4, "max": 4.0, "unit": "mg", "hazard_threshold": 8.0},
        "IV": {"min": 0.4, "max": 2.0, "unit": "mg", "hazard_threshold": 6.0},
        "IM": {"min": 0.4, "max": 2.0, "unit": "mg", "hazard_threshold": 6.0},
    },
    "amiodarone": {
        "IV": {"min": 150.0, "max": 300.0, "unit": "mg", "hazard_threshold": 450.0},
        "IO": {"min": 150.0, "max": 300.0, "unit": "mg", "hazard_threshold": 450.0},
    },
    "fentanyl": {
        "IV": {"min": 25.0, "max": 100.0, "unit": "mcg", "hazard_threshold": 250.0},
        "IN": {"min": 50.0, "max": 100.0, "unit": "mcg", "hazard_threshold": 250.0},
        "IM": {"min": 50.0, "max": 100.0, "unit": "mcg", "hazard_threshold": 250.0},
    },
    "morphine": {
        "IV": {"min": 2.0, "max": 10.0, "unit": "mg", "hazard_threshold": 15.0},
        "IM": {"min": 2.0, "max": 10.0, "unit": "mg", "hazard_threshold": 15.0},
    },
    "midazolam": {
        "IV": {"min": 1.0, "max": 5.0, "unit": "mg", "hazard_threshold": 10.0},
        "IN": {"min": 2.5, "max": 10.0, "unit": "mg", "hazard_threshold": 15.0},
        "IM": {"min": 2.5, "max": 10.0, "unit": "mg", "hazard_threshold": 15.0},
    },
    "atropine": {
        "IV": {"min": 0.5, "max": 3.0, "unit": "mg", "hazard_threshold": 3.0},
        "IO": {"min": 0.5, "max": 3.0, "unit": "mg", "hazard_threshold": 3.0},
    },
    "adenosine": {
        "IV": {"min": 6.0, "max": 12.0, "unit": "mg", "hazard_threshold": 18.0},
    },
    "ondansetron": {
        "IV": {"min": 4.0, "max": 8.0, "unit": "mg", "hazard_threshold": 16.0},
        "PO": {"min": 4.0, "max": 8.0, "unit": "mg", "hazard_threshold": 16.0},
    },
}


class ClinicalSafetyGuard:
    """
    Evaluates clinical plausibility, dosage outliers, and sound-alike hazards.
    """

    @staticmethod
    def get_tall_man_lettering(drug_name: str) -> str:
        """Returns the official FDA Tall Man typography or capitalized string."""
        return TALL_MAN_MAP.get(drug_name.lower(), drug_name.capitalize())

    @classmethod
    def validate_dosage(cls, drug_name: str, route: str, dose: float, unit: str) -> Tuple[bool, Optional[str]]:
        """
        Validates dosage against adult safety limits.
        Returns: (is_outlier, alert_message)
        """
        drug_key = drug_name.lower().strip()
        route_key = route.upper().strip()

        if drug_key not in DOSAGE_BOUNDS:
            return False, None

        routes_map = DOSAGE_BOUNDS[drug_key]
        if route_key not in routes_map:
            # Fallback to general route or first available for the drug
            route_key = list(routes_map.keys())[0]

        bounds = routes_map[route_key]
        expected_unit = bounds["unit"]

        # Basic unit validation
        if unit.lower() != expected_unit.lower() and not (unit.lower() in ("mcg", "ug") and expected_unit == "mcg"):
            return True, f"Unit Mismatch Alert: Expected {expected_unit} for {drug_name}, but detected {unit}."

        if dose > bounds["hazard_threshold"]:
            tall_man = cls.get_tall_man_lettering(drug_name)
            return True, (
                f"CRITICAL DOSAGE WARNING: {tall_man} dose {dose}{unit} exceeds safe adult upper bound "
                f"({bounds['max']}{expected_unit} max via {route_key}). Requires paramedic override."
            )

        if dose < bounds["min"] * 0.5:
            return True, f"Sub-therapeutic dosage detected for {drug_name}: {dose}{unit} (typical min: {bounds['min']}{expected_unit})."

        return False, None

    @classmethod
    def check_route_conflict(cls, drug_name: str, route: str, ongoing_cpr: bool = False) -> Optional[str]:
        """
        Identifies inappropriate administration routes (e.g. oral meds during CPR or cardiac arrest).
        """
        r = route.upper()
        if ongoing_cpr and r == "PO":
            return f"ROUTE CONFLICT: Oral route (PO) contraindicated during active CPR / cardiac arrest."

        # High-potency sedatives via oral route in emergency
        if drug_name.lower() in ("amiodarone", "adenosine") and r == "PO":
            return f"ROUTE FEASIBILITY ALERT: {drug_name} emergency bolus cannot be administered PO."

        return None

    @classmethod
    def detect_look_alike_sound_alike(cls, input_name: str) -> List[str]:
        """Flags potential Look-Alike/Sound-Alike (LASA) pairs requiring visual differentiation."""
        alerts = []
        name = input_name.lower()
        if "epi" in name:
            alerts.append("CONFUSION ALERT: Verify EPINephrine vs ePHEDrine before administration.")
        elif "morphine" in name or "hydromorphone" in name:
            alerts.append("CONFUSION ALERT: Verify morPHINE vs HYDROmorphone (7x potency difference).")
        elif "amiodarone" in name:
            alerts.append("CONFUSION ALERT: amiODAROne (Antiarrhythmic) vs aMIOtriptyline.")
        return alerts

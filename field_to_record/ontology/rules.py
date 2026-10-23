"""
Clinical disambiguation rules for field shorthand and concentration ratios.
Example:
- Epinephrine 1:1,000 (IM/SubQ for Anaphylaxis) vs Epinephrine 1:10,000 (IV/IO for Cardiac Arrest).
- Normal Saline large volume bolus vs IV flush.
"""

from typing import Dict, Any, Tuple


def disambiguate_epinephrine(route: str, dose: float, unit: str) -> Tuple[str, str]:
    """
    Differentiates Epinephrine 1:1,000 (anaphylaxis) from 1:10,000 (cardiac arrest)
    based on administration route and dosage.
    Returns: (rxnorm_cui, display_name)
    """
    r = route.upper()
    # IM or SubQ -> Epinephrine 1 mg/mL (1:1,000)
    if r in ("IM", "SUBQ", "SQ"):
        return ("727316", "Epinephrine 1 MG/ML Injectable Solution [1:1,000]")

    # IV or IO -> Epinephrine 0.1 mg/mL (1:10,000)
    if r in ("IV", "IO"):
        return ("727345", "Epinephrine 0.1 MG/ML Injectable Solution [1:10,000]")

    # Default if ambiguous
    if dose <= 0.5:
        return ("727316", "Epinephrine 1 MG/ML Injectable Solution [1:1,000]")
    return ("727345", "Epinephrine 0.1 MG/ML Injectable Solution [1:10,000]")


def disambiguate_saline(volume: float, unit: str) -> Tuple[str, str]:
    """
    Differentiates Normal Saline IV push/flush from large volume resuscitation bag.
    """
    u = unit.lower()
    if u in ("ml", "cc"):
        if volume <= 20:
            return ("1807632", "Sodium Chloride 0.9 % Flushing Solution")
        else:
            return ("313002", "Sodium Chloride 0.9 % Solution for Infusion")
    elif u in ("l", "liter", "liters", "bag"):
        return ("313002", "Sodium Chloride 0.9 % Solution for Infusion")

    return ("313002", "Sodium Chloride 0.9 % Solution for Infusion")

"""
Ontology subpackage for RxNorm and SNOMED CT grounding, phonetic matching, and clinical safety.
"""

from field_to_record.ontology.grounder import MedicalOntologyGrounder
from field_to_record.ontology.phonetic import double_metaphone, damerau_levenshtein_distance, find_best_phonetic_match
from field_to_record.ontology.safety import ClinicalSafetyGuard
from field_to_record.ontology.rules import disambiguate_epinephrine, disambiguate_saline

__all__ = [
    "MedicalOntologyGrounder",
    "double_metaphone",
    "damerau_levenshtein_distance",
    "find_best_phonetic_match",
    "ClinicalSafetyGuard",
    "disambiguate_epinephrine",
    "disambiguate_saline",
]

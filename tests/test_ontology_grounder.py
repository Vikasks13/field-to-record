"""
Tests for Medical Ontology Grounding, Phonetic Matching & Disambiguation.
"""

import pytest
from field_to_record.ontology.grounder import MedicalOntologyGrounder
from field_to_record.ontology.phonetic import double_metaphone, damerau_levenshtein_distance, find_best_phonetic_match
from field_to_record.ontology.rules import disambiguate_epinephrine


def test_damerau_levenshtein():
    assert damerau_levenshtein_distance("narcan", "narcon") == 1
    assert damerau_levenshtein_distance("epinephrine", "epinephrine") == 0
    # Transposition
    assert damerau_levenshtein_distance("naloxne", "naloxone") == 1


def test_double_metaphone():
    pri, sec = double_metaphone("fentanyl")
    assert pri.startswith("F")


def test_phonetic_fuzzy_match_candidate():
    candidates = ["naloxone", "epinephrine", "amiodarone", "fentanyl", "midazolam"]
    # Typo: "narcon" -> "naloxone" is semantic, but "fentanil" -> "fentanyl"
    match = find_best_phonetic_match("fentanil", candidates)
    assert match == "fentanyl"

    match_amio = find_best_phonetic_match("amiodaron", candidates)
    assert match_amio == "amiodarone"


def test_epinephrine_route_disambiguation():
    # IM route for anaphylaxis
    cui_im, disp_im = disambiguate_epinephrine(route="IM", dose=0.3, unit="mg")
    assert cui_im == "727316"
    assert "1:1,000" in disp_im

    # IV route for cardiac arrest
    cui_iv, disp_iv = disambiguate_epinephrine(route="IV", dose=1.0, unit="mg")
    assert cui_iv == "727345"
    assert "1:10,000" in disp_iv


def test_ground_procedure():
    grounder = MedicalOntologyGrounder()
    res = grounder.ground_procedure("intubation")
    assert res["code"] == "112798008"
    assert "intubation" in res["display"].lower()

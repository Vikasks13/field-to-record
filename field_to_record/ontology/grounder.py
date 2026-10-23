"""
Medical ontology grounding and normalization engine.
Matches extracted drug names and procedures against offline RxNorm and SNOMED CT subsets
using Trie / SQLite indexing and phonetic fuzzy matching.
"""

import os
import sqlite3
from typing import Dict, Any, Optional, List, Tuple
from field_to_record.ontology.phonetic import find_best_phonetic_match
from field_to_record.ontology.rules import disambiguate_epinephrine, disambiguate_saline
from field_to_record.ontology.safety import ClinicalSafetyGuard

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "ontology.db")

# Seed RxNorm concepts for emergency pre-hospital medicine
RXNORM_SEED = [
    ("727316", "epinephrine", "Epinephrine 1 MG/ML Injectable Solution [1:1,000]", "EPINephrine"),
    ("727345", "epinephrine", "Epinephrine 0.1 MG/ML Injectable Solution [1:10,000]", "EPINephrine"),
    ("1656328", "naloxone", "Naloxone Hydrochloride 2 MG Nasal Spray [Narcan]", "nalOXone"),
    ("1191", "fentanyl", "Fentanyl Citrate 0.05 MG/ML Injectable Solution", "fentaNYL"),
    ("703", "amiodarone", "Amiodarone Hydrochloride 50 MG/ML Injectable Solution", "amiODAROne"),
    ("6960", "midazolam", "Midazolam 5 MG/ML Injectable Solution [Versed]", "midazolAM"),
    ("7052", "morphine", "Morphine Sulfate 10 MG/ML Injectable Solution", "morPHINE"),
    ("1223", "atropine", "Atropine Sulfate 0.1 MG/ML Injectable Solution", "Atropine"),
    ("296", "adenosine", "Adenosine 3 MG/ML Injectable Solution [Adenocard]", "Adenosine"),
    ("26225", "ondansetron", "Ondansetron 2 MG/ML Injectable Solution [Zofran]", "Ondansetron"),
    ("435", "albuterol", "Albuterol 0.83 MG/ML Inhalation Solution", "Albuterol"),
    ("6020", "ipratropium", "Ipratropium Bromide 0.2 MG/ML Inhalation Solution", "Ipratropium"),
    ("6130", "ketamine", "Ketamine Hydrochloride 50 MG/ML Injectable Solution", "Ketamine"),
    ("10763", "tranexamic acid", "Tranexamic Acid 100 MG/ML Injectable Solution", "Tranexamic Acid"),
    ("313002", "normal saline", "Sodium Chloride 0.9 % Solution for Infusion", "Normal Saline"),
    ("1807632", "normal saline", "Sodium Chloride 0.9 % Flushing Solution", "Normal Saline Flush"),
    ("1191", "lactated ringers", "Lactated Ringer's Solution for Infusion", "Lactated Ringer's"),
    ("4850", "dextrose", "Dextrose 500 MG/ML Injectable Solution [D50W]", "Dextrose 50%"),
    ("4832", "glucagon", "Glucagon 1 MG Injection Kit", "Glucagon"),
    ("1191", "aspirin", "Aspirin 81 MG Chewable Tablet", "Aspirin"),
    ("7435", "nitroglycerin", "Nitroglycerin 0.4 MG Sublingual Tablet", "Nitroglycerin"),
    ("6646", "magnesium sulfate", "Magnesium Sulfate 500 MG/ML Injectable Solution", "Magnesium Sulfate"),
    ("3992", "ephedrine", "Ephedrine Sulfate 50 MG/ML Injectable Solution", "ePHEDrine"),
    ("3423", "hydromorphone", "Hydromorphone Hydrochloride 2 MG/ML Injection [Dilaudid]", "HYDROmorphone"),
]

# Seed SNOMED CT Procedure codes
SNOMED_PROCEDURES_SEED = [
    ("112798008", "Endotracheal intubation", "Intubation", "112798008"),
    ("42550007", "Bag-valve-mask ventilation", "BVM", "42550007"),
    ("89666000", "Cardiopulmonary resuscitation", "CPR", "89666000"),
    ("24171008", "Cardiac defibrillation", "Defibrillation", "24171008"),
    ("75569001", "Synchronized cardioversion", "Cardioversion", "75569001"),
    ("230040009", "Needle thoracostomy", "Needle Decompression", "230040009"),
    ("417255000", "Intraosseous vascular access", "IO access", "417255000"),
    ("392230005", "Intravenous catheterization", "IV access", "392230005"),
    ("268400002", "12-lead electrocardiogram", "12-lead ECG", "268400002"),
    ("225358003", "Application of tourniquet", "Tourniquet", "225358003"),
    ("428014008", "Insertion of supraglottic airway", "Supraglottic Airway", "428014008"),
]

# Seed SNOMED CT Route codes
SNOMED_ROUTE_SEED = {
    "IV": ("47625008", "Intravenous route"),
    "IO": ("417255000", "Intraosseous route"),
    "IM": ("78421000", "Intramuscular route"),
    "IN": ("46713006", "Nasal route"),
    "SUBQ": ("34206005", "Subcutaneous route"),
    "SQ": ("34206005", "Subcutaneous route"),
    "NEBULIZED": ("447694001", "Respiratory tract route"),
    "PO": ("26643006", "Oral route"),
    "SL": ("37839007", "Sublingual route"),
    "ETT": ("372464004", "Endotracheal route"),
}


class MedicalOntologyGrounder:
    """
    Offline SQLite + Trie grounding engine for clinical concepts.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_database()
        self._load_cache()

    def _init_database(self) -> None:
        """Initializes tables and seeds initial EMS concepts if empty."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS rxnorm (
                rxcui TEXT,
                generic_name TEXT,
                display_name TEXT,
                tall_man TEXT,
                PRIMARY KEY (rxcui, generic_name)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS snomed_procedures (
                snomed_code TEXT PRIMARY KEY,
                display_name TEXT,
                alias TEXT,
                concept_id TEXT
            )
        """)

        # Check if table populated
        cur.execute("SELECT COUNT(*) FROM rxnorm")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO rxnorm VALUES (?, ?, ?, ?)",
                RXNORM_SEED
            )
            cur.executemany(
                "INSERT INTO snomed_procedures VALUES (?, ?, ?, ?)",
                SNOMED_PROCEDURES_SEED
            )
            conn.commit()
        conn.close()

    def _load_cache(self) -> None:
        """Loads indexed terms into memory for instant sub-millisecond queries."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT generic_name, rxcui, display_name, tall_man FROM rxnorm")
        self.rxnorm_cache: Dict[str, List[Dict[str, str]]] = {}
        for gen, cui, disp, tm in cur.fetchall():
            if gen not in self.rxnorm_cache:
                self.rxnorm_cache[gen] = []
            self.rxnorm_cache[gen].append({"rxcui": cui, "display": disp, "tall_man": tm})

        cur.execute("SELECT snomed_code, display_name, alias FROM snomed_procedures")
        self.snomed_cache: Dict[str, Dict[str, str]] = {}
        for code, disp, alias in cur.fetchall():
            self.snomed_cache[disp.lower()] = {"code": code, "display": disp}
            self.snomed_cache[alias.lower()] = {"code": code, "display": disp}
        conn.close()

    def ground_medication(
        self,
        raw_drug: str,
        route: str = "IV",
        dose: float = 1.0,
        unit: str = "mg",
        ongoing_cpr: bool = False
    ) -> Dict[str, Any]:
        """
        Maps raw pharmaceutical mention to standard RxNorm concept, applying
        route disambiguation, Tall Man lettering, and clinical safety bounds.
        """
        clean_drug = raw_drug.lower().strip()
        candidates = list(self.rxnorm_cache.keys())

        matched_key = find_best_phonetic_match(clean_drug, candidates, max_dist=2) or clean_drug

        # Disambiguation logic
        if matched_key == "epinephrine":
            cui, disp = disambiguate_epinephrine(route, dose, unit)
        elif matched_key == "normal saline":
            cui, disp = disambiguate_saline(dose, unit)
        elif matched_key in self.rxnorm_cache:
            entry = self.rxnorm_cache[matched_key][0]
            cui, disp = entry["rxcui"], entry["display"]
        else:
            cui, disp = "UNKNOWN", raw_drug.capitalize()

        tall_man = ClinicalSafetyGuard.get_tall_man_lettering(matched_key)
        is_outlier, dose_alert = ClinicalSafetyGuard.validate_dosage(matched_key, route, dose, unit)
        route_alert = ClinicalSafetyGuard.check_route_conflict(matched_key, route, ongoing_cpr)

        alerts = []
        if dose_alert:
            alerts.append(dose_alert)
        if route_alert:
            alerts.append(route_alert)
        alerts.extend(ClinicalSafetyGuard.detect_look_alike_sound_alike(matched_key))

        return {
            "canonical_name": matched_key.capitalize(),
            "tall_man_name": tall_man,
            "rxnorm_code": cui,
            "rxnorm_display": disp,
            "is_outlier": is_outlier,
            "safety_alert": " | ".join(alerts) if alerts else None,
        }

    def ground_procedure(self, raw_proc: str) -> Dict[str, str]:
        """Maps procedure mention to standard SNOMED CT concept."""
        clean_proc = raw_proc.lower().strip()
        candidates = list(self.snomed_cache.keys())
        matched = find_best_phonetic_match(clean_proc, candidates, max_dist=2)

        if matched and matched in self.snomed_cache:
            item = self.snomed_cache[matched]
            return {"code": item["code"], "display": item["display"]}

        return {"code": "UNKNOWN", "display": raw_proc.capitalize()}

    def ground_route(self, route_str: str) -> Tuple[Optional[str], Optional[str]]:
        """Maps route string to SNOMED CT route coding."""
        r = route_str.upper().strip()
        if r in SNOMED_ROUTE_SEED:
            code, disp = SNOMED_ROUTE_SEED[r]
            return code, disp
        return None, None

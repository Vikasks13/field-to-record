"""
Clinical terminology patterns, entity regexes, and normalization lexicons.
Specially tuned for EMS dictation shorthand, trade names, and abbreviations.
"""

import re

# Medication aliases mapped to standard generic keys
MEDICATION_ALIASES = {
    "narcan": "naloxone",
    "naloxone": "naloxone",
    "epinephrine": "epinephrine",
    "epi": "epinephrine",
    "adrenaline": "epinephrine",
    "fentanyl": "fentanyl",
    "sublimaze": "fentanyl",
    "amiodarone": "amiodarone",
    "cordarone": "amiodarone",
    "midazolam": "midazolam",
    "versed": "midazolam",
    "morphine": "morphine",
    "atropine": "atropine",
    "adenosine": "adenosine",
    "adenocard": "adenosine",
    "ondansetron": "ondansetron",
    "zofran": "ondansetron",
    "albuterol": "albuterol",
    "proventil": "albuterol",
    "ventolin": "albuterol",
    "ipratropium": "ipratropium",
    "atrovent": "ipratropium",
    "ketamine": "ketamine",
    "ketalar": "ketamine",
    "tranexamic acid": "tranexamic acid",
    "txa": "tranexamic acid",
    "normal saline": "normal saline",
    "ns": "normal saline",
    "lactated ringers": "lactated ringers",
    "lr": "lactated ringers",
    "dextrose": "dextrose",
    "d50": "dextrose",
    "glucagon": "glucagon",
    "aspirin": "aspirin",
    "asa": "aspirin",
    "nitroglycerin": "nitroglycerin",
    "nitro": "nitroglycerin",
    "magnesium sulfate": "magnesium sulfate",
    "mag": "magnesium sulfate",
    "ephedrine": "ephedrine",
    "hydromorphone": "hydromorphone",
    "dilaudid": "hydromorphone",
}

# Routes and normalization
ROUTE_ALIASES = {
    "iv": "IV",
    "intravenous": "IV",
    "io": "IO",
    "intraosseous": "IO",
    "im": "IM",
    "intramuscular": "IM",
    "in": "IN",
    "intranasal": "IN",
    "nasal": "IN",
    "subq": "SubQ",
    "subcutaneous": "SubQ",
    "sq": "SubQ",
    "nebulized": "Nebulized",
    "nebulizer": "Nebulized",
    "neb": "Nebulized",
    "po": "PO",
    "oral": "PO",
    "sublingual": "SL",
    "sl": "SL",
    "ett": "ETT",
}

# Standard EMS Procedures
PROCEDURE_ALIASES = {
    "intubation": "Endotracheal intubation",
    "endotracheal intubation": "Endotracheal intubation",
    "ett": "Endotracheal intubation",
    "bvm": "Bag-valve-mask ventilation",
    "bag valve mask": "Bag-valve-mask ventilation",
    "bagged": "Bag-valve-mask ventilation",
    "cpr": "Cardiopulmonary resuscitation",
    "chest compressions": "Cardiopulmonary resuscitation",
    "defibrillation": "Cardiac defibrillation",
    "defib": "Cardiac defibrillation",
    "shock": "Cardiac defibrillation",
    "cardioversion": "Synchronized cardioversion",
    "needle decompression": "Needle thoracostomy",
    "needle thoracostomy": "Needle thoracostomy",
    "io access": "Intraosseous vascular access",
    "io placement": "Intraosseous vascular access",
    "iv access": "Intravenous catheterization",
    "started an iv": "Intravenous catheterization",
    "12-lead ecg": "12-lead electrocardiogram",
    "12 lead": "12-lead electrocardiogram",
    "ecg": "12-lead electrocardiogram",
    "tourniquet": "Application of tourniquet",
    "cat tourniquet": "Application of tourniquet",
    "king airway": "Insertion of supraglottic airway",
    "i-gel": "Insertion of supraglottic airway",
}

# Anatomical Sites
ANATOMICAL_SITES = [
    r"left\s+antecubital(?:\s+fossa)?",
    r"right\s+antecubital(?:\s+fossa)?",
    r"left\s+arm",
    r"right\s+arm",
    r"left\s+forearm",
    r"right\s+forearm",
    r"left\s+hand",
    r"right\s+hand",
    r"proximal\s+tibia",
    r"right\s+tibia",
    r"left\s+tibia",
    r"right\s+leg",
    r"left\s+leg",
    r"2nd\s+intercostal\s+space",
    r"midclavicular\s+line",
    r"right\s+anterior\s+axillary",
    r"left\s+anterior\s+axillary",
    r"right\s+upper\s+extremity",
    r"left\s+upper\s+extremity",
    r"right\s+lower\s+extremity",
    r"left\s+lower\s+extremity",
]

# Regex patterns for clinical slots
MED_REGEX = re.compile(
    r"(?:administered|gave|pushed|delivered|hung|started)?\s*"
    r"(?P<dose>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>mg|mcg|ug|ml|g|mEq|gtts|puffs|joules|j|units|amps?)?\s*"
    r"(?:of\s*)?"
    r"(?P<drug>[a-zA-Z0-9\-\s]+?)\s*"
    r"(?:via|through|by|using)?\s*"
    r"(?P<route>iv|io|im|in|subq|sq|nebulized|neb|po|sl|ett)?\b",
    re.IGNORECASE
)

# Observation / Vitals pattern: e.g. "GCS 14", "SpO2 92%", "BP 120/80", "HR 110", "pulse 98"
VITALS_REGEX = re.compile(
    r"\b(?P<type>gcs|spo2|o2\s*sat|hr|heart\s*rate|pulse|bp|blood\s*pressure)\s*"
    r"(?:is|of|was|at)?\s*"
    r"(?P<val>\d+(?:/\d+)?)\s*"
    r"(?P<unit>%|bpm|mmHg|pts)?\b",
    re.IGNORECASE
)

# Time anchor pattern: e.g. "at 14:02", "at 09:30", "10 minutes ago", "just now"
TIME_REGEX = re.compile(
    r"\b(?:at\s*(?P<time>\d{1,2}:\d{2})|(?P<rel>\d+\s*minutes?\s*ago)|(?P<now>just\s*now))\b",
    re.IGNORECASE
)

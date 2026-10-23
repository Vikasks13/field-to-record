"""
Clinical vocabulary biasing prompts for edge Whisper models.
Guides beam search decoding towards high-risk EMS pharmacotherapy, routes,
and critical resuscitation procedures.
"""

# Core EMS Pharmacopeia & Resuscitation prompt
EMS_CLINICAL_PROMPT = (
    "EMS paramedic field report. Medications: Epinephrine, Naloxone, Narcan, Fentanyl, "
    "Amiodarone, Midazolam, Versed, Morphine, Atropine, Adenosine, Ondansetron, Zofran, "
    "Albuterol, Ipratropium, Atrovent, Ketamine, Tranexamic Acid, TXA, Normal Saline, "
    "Lactated Ringers, Dextrose D50, Glucagon, Aspirin, Nitroglycerin, Magnesium Sulfate. "
    "Routes: IV, IO, IM, IN, Nebulized, SubQ, PO, ETT. "
    "Procedures: Endotracheal Intubation, Bag-Valve-Mask, BVM, CPR, Chest Compressions, "
    "Defibrillation, Synchronized Cardioversion, Needle Thoracostomy, Chest Decompression, "
    "IO Needle Insertion, King LT Airway, i-gel, 12-lead ECG, Tourniquet placement."
)

# Domain-specific prompt expansions
CARDIAC_PROMPT = (
    "Cardiac arrest resuscitation. Epinephrine 1:10000 1 mg IV push every 3 to 5 minutes. "
    "Amiodarone 300 mg IV first dose, 150 mg second dose. Defibrillation 200 Joules biphasic. "
    "CPR ongoing, ROSC achieved, 12-lead ECG shows STEMI."
)

OVERDOSE_PROMPT = (
    "Suspected opioid toxidrome. Naloxone Narcan 2 mg intranasal IN administered. "
    "Pinpoint pupils, shallow respirations 4 per minute, bag-valve-mask assisted ventilations."
)

TRAUMA_PROMPT = (
    "Penetrating trauma report. CombatCAT tourniquet applied high and tight right upper extremity. "
    "Tranexamic Acid TXA 1 gram in 100 mL Normal Saline over 10 minutes IV. "
    "Needle decompression 2nd intercostal space midclavicular line."
)


def get_conditioned_prompt(scenario: str = "general") -> str:
    """Returns specialized prompt based on scenario keyword."""
    s = scenario.lower()
    if "cardiac" in s or "arrest" in s:
        return f"{EMS_CLINICAL_PROMPT} {CARDIAC_PROMPT}"
    elif "overdose" in s or "tox" in s:
        return f"{EMS_CLINICAL_PROMPT} {OVERDOSE_PROMPT}"
    elif "trauma" in s:
        return f"{EMS_CLINICAL_PROMPT} {TRAUMA_PROMPT}"
    return EMS_CLINICAL_PROMPT

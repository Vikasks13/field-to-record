"""
Synthetic EMS Scenario Generator (Zero PHI).
Produces realistic de-identified paramedic field dictation transcripts
across 5 core emergency categories for benchmarking and evaluation.
"""

import random
from typing import List, Dict, Any

SCENARIO_TEMPLATES = {
    "cardiovascular": [
        {
            "transcript": "Medic 12 on scene with 58-year-old male in ventricular fibrillation. Initiated CPR immediately. Delivered defibrillation 200 Joules biphasic. Administered 1 mg of epinephrine IV at 15:32 and 300 mg of amiodarone IV. ROSC achieved after second shock. GCS 8, SpO2 96%.",
            "expected_meds": ["epinephrine", "amiodarone"],
            "expected_procs": ["Cardiopulmonary resuscitation", "Cardiac defibrillation"],
        },
        {
            "transcript": "Medic 4 transporting 64-year-old female with acute chest pain. 12-lead ECG confirmed inferior STEMI. Administered 324 mg of aspirin PO and 0.4 mg of nitroglycerin SL. Established IV access left antecubital. Blood pressure 130/80, heart rate 88.",
            "expected_meds": ["aspirin", "nitroglycerin"],
            "expected_procs": ["12-lead electrocardiogram", "Intravenous catheterization"],
        },
    ],
    "respiratory": [
        {
            "transcript": "Rescue 7 responding to severe respiratory distress. 24-year-old female with acute asthma exacerbation. SpO2 84% on room air. Administered 2.5 mg of albuterol nebulized and 0.5 mg of ipratropium nebulizer. Administered 0.3 mg of epinephrine IM right thigh for bronchospasm.",
            "expected_meds": ["albuterol", "ipratropium", "epinephrine"],
            "expected_procs": [],
        },
        {
            "transcript": "Engine 9 on scene. 70-year-old male with COPD exacerbation in extremis. Assisted ventilations with BVM ventilation. Administered 5 mg of albuterol neb. Placed supraglottic King airway with bilateral breath sounds.",
            "expected_meds": ["albuterol"],
            "expected_procs": ["Bag-valve-mask ventilation", "Insertion of supraglottic airway"],
        },
    ],
    "toxicology": [
        {
            "transcript": "Medic 2 arriving with 32-year-old male found unresponsive with suspected fentanyl overdose. Respiratory rate 4 per minute, pinpoint pupils. Administered 2 mg of Narcan IN at 21:10. Assisted with bag valve mask ventilation. Patient resumed spontaneous respirations. GCS improved to 14.",
            "expected_meds": ["naloxone"],
            "expected_procs": ["Bag-valve-mask ventilation"],
        },
        {
            "transcript": "Engine 11 on scene. Unresponsive female in vehicle. Administered 4 mg of naloxone IN nasal spray followed by 1 mg of naloxone IV push. Established IV access right arm.",
            "expected_meds": ["naloxone"],
            "expected_procs": ["Intravenous catheterization"],
        },
    ],
    "trauma": [
        {
            "transcript": "Medic 8 transporting penetrating trauma from motor vehicle collision. Severe bleeding controlled with CAT tourniquet to right upper extremity. Administered 1 gram of tranexamic acid TXA in 100 mL normal saline IV over 10 minutes. Performed needle decompression at 2nd intercostal space right chest.",
            "expected_meds": ["tranexamic acid", "normal saline"],
            "expected_procs": ["Application of tourniquet", "Needle thoracostomy"],
        },
        {
            "transcript": "Squad 3 on scene. Severe crush injury left lower extremity. Tourniquet applied proximal left leg. Started 500 ml of normal saline bolus IV. Administered 100 mcg of fentanyl IV for analgesia.",
            "expected_meds": ["normal saline", "fentanyl"],
            "expected_procs": ["Application of tourniquet"],
        },
    ],
    "neurology": [
        {
            "transcript": "Medic 5 evaluating 45-year-old female in active status epilepticus. Continuous generalized tonic-clonic seizure for 10 minutes. Administered 5 mg of midazolam Versed IV at 10:45. Seizure activity ceased. Post-ictal, GCS 9, SpO2 95%.",
            "expected_meds": ["midazolam"],
            "expected_procs": [],
        },
        {
            "transcript": "Medic 15 dispatched to possible acute ischemic stroke. Last seen normal 45 minutes prior. Cincinnati Stroke Scale positive for right facial droop and right arm drift. Blood glucose 110 mg/dL, blood pressure 170/95.",
            "expected_meds": [],
            "expected_procs": [],
        },
    ],
}


class SyntheticScenarioGenerator:
    """
    Generates synthetic, privacy-compliant EMS field audio dictation scripts.
    """

    @classmethod
    def get_all_scenarios(cls) -> List[Dict[str, Any]]:
        """Returns all gold-standard test scenarios across the 5 categories."""
        all_cases = []
        for cat, cases in SCENARIO_TEMPLATES.items():
            for idx, item in enumerate(cases):
                all_cases.append({
                    "id": f"syn-{cat}-{idx + 1:02d}",
                    "category": cat,
                    "transcript": item["transcript"],
                    "expected_meds": item["expected_meds"],
                    "expected_procs": item["expected_procs"],
                })
        return all_cases

    @classmethod
    def get_random_scenario(cls, category: str = "cardiovascular") -> Dict[str, Any]:
        """Returns a single scenario for dynamic benchmarking."""
        cat_key = category.lower()
        if cat_key not in SCENARIO_TEMPLATES:
            cat_key = "cardiovascular"
        return random.choice(SCENARIO_TEMPLATES[cat_key])

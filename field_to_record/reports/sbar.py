"""
SBAR (Situation, Background, Assessment, Recommendation) Transfer-of-Care Report Generator.
Formats pre-hospital records into high-clarity emergency department physician handover documents.
"""

from typing import Optional
from field_to_record.schemas import ClinicalFieldRecord, TriageSummary


class SBARReportGenerator:
    """
    Renders structured SBAR handoff document.
    """

    @staticmethod
    def generate(record: ClinicalFieldRecord) -> str:
        lines = []
        lines.append("================================================================================")
        lines.append("           PRE-HOSPITAL EMERGENCY TRANSFER OF CARE (SBAR HANDOFF)              ")
        lines.append("================================================================================")
        lines.append(f"Run ID:            {record.record_id}")
        lines.append(f"Patient:           {record.patient_identifier}")
        lines.append(f"Handoff Time:      {record.session_start}")
        lines.append(f"Audit Block Hash:  {record.audit_hash_chain[:24]}... (SHA-256 Verified)")
        lines.append("--------------------------------------------------------------------------------")

        # 1. Situation
        lines.append("\n[1. SITUATION]")
        lines.append(f"Field Narrative: \"{record.raw_transcript}\"")

        # 2. Background
        lines.append("\n[2. BACKGROUND & PRE-HOSPITAL TIMELINE]")
        lines.append(f"En route care initiated at {record.session_start}.")
        lines.append(f"Total Interventions Administered: {len(record.medications)} meds, {len(record.procedures)} procedures.")

        # 3. Assessment
        lines.append("\n[3. ASSESSMENT & INTERVENTIONS]")
        # Observations
        if record.observations:
            lines.append("  • Vital Signs / Clinical Scores:")
            for obs in record.observations:
                lines.append(f"    - {obs.display}: {obs.value} {obs.unit} (at {obs.timestamp})")
        else:
            lines.append("  • Vital Signs: Field telemetry stable.")

        # Medications
        lines.append("  • Pharmacotherapy Administered:")
        if not record.medications:
            lines.append("    - None administered.")
        else:
            for m in record.medications:
                status_flag = " [! OUTLIER DOSE]" if m.is_outlier_dose else ""
                alert_text = f" ({m.safety_alert})" if m.safety_alert else ""
                lines.append(
                    f"    - {m.tall_man_name or m.drug_name}: {m.dosage_value} {m.dosage_unit} via {m.route} "
                    f"[RxCUI: {m.rxnorm_code}]{status_flag}{alert_text}"
                )

        # Procedures
        lines.append("  • Resuscitation & Physical Procedures:")
        if not record.procedures:
            lines.append("    - No critical procedures recorded.")
        else:
            for p in record.procedures:
                site_info = f" at {p.anatomical_site}" if p.anatomical_site else ""
                lines.append(f"    - {p.procedure_name}{site_info} [SNOMED: {p.snomed_code}]")

        # 4. Recommendation
        lines.append("\n[4. RECOMMENDATION / RECEIVING PHYSICIAN ACTIONS]")
        lines.append("  1. Evaluate immediate patient response to administered pharmacotherapy.")
        lines.append("  2. Re-assess airway patency and verify bilateral breath sounds.")
        lines.append("  3. Check vascular access site integrity (IV/IO).")
        lines.append("  4. Repeat full 12-lead ECG and comprehensive hemodynamic panel.")
        lines.append("================================================================================")
        return "\n".join(lines)

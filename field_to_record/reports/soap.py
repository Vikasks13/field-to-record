"""
SOAP (Subjective, Objective, Assessment, Plan) Clinical Note Generator.
Formats structured field runs into hospital-grade clinical documentation notes.
"""

from field_to_record.schemas import ClinicalFieldRecord


class SOAPReportGenerator:
    """
    Renders structured SOAP clinical note.
    """

    @staticmethod
    def generate(record: ClinicalFieldRecord) -> str:
        lines = []
        lines.append("================================================================================")
        lines.append("                  PRE-HOSPITAL CLINICAL PROGRESS NOTE (SOAP)                    ")
        lines.append("================================================================================")
        lines.append(f"Record ID:   {record.record_id}")
        lines.append(f"Patient:     {record.patient_identifier}")
        lines.append(f"Date/Time:   {record.session_start}")
        lines.append(f"Audit Trail: {record.audit_hash_chain}")
        lines.append("--------------------------------------------------------------------------------")

        # Subjective
        lines.append("\n[SUBJECTIVE]")
        lines.append(f"Chief Complaint & Field Report: \"{record.raw_transcript}\"")

        # Objective
        lines.append("\n[OBJECTIVE]")
        lines.append("Physical Findings & Recorded Observations:")
        if record.observations:
            for obs in record.observations:
                lines.append(f"  • {obs.display}: {obs.value} {obs.unit}")
        else:
            lines.append("  • No explicit numeric vitals dictated.")

        lines.append("\nInterventions Executed Prior to ED Arrival:")
        for med in record.medications:
            lines.append(
                f"  • Medication: {med.tall_man_name or med.drug_name} {med.dosage_value}{med.dosage_unit} "
                f"via {med.route} [RxNorm CUI: {med.rxnorm_code}]"
            )
        for proc in record.procedures:
            site = f" ({proc.anatomical_site})" if proc.anatomical_site else ""
            lines.append(f"  • Procedure: {proc.procedure_name}{site} [SNOMED CT: {proc.snomed_code}]")

        # Assessment
        lines.append("\n[ASSESSMENT]")
        lines.append("Pre-hospital Clinical Trajectory:")
        lines.append(f"  • Patient managed under standard EMS clinical protocols.")
        if any(m.is_outlier_dose for m in record.medications):
            lines.append("  • NOTICE: One or more dosages required clinical outlier verification.")

        # Plan
        lines.append("\n[PLAN]")
        lines.append("Receiving ED Handoff:")
        lines.append("  • Transfer of care to receiving emergency department team.")
        lines.append("  • Continuous cardiac and pulse oximetry monitoring.")
        lines.append("  • Re-assess vitals within 5 minutes of bed transfer.")
        lines.append("================================================================================")
        return "\n".join(lines)

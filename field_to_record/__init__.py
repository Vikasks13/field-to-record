"""
Field-to-Record: Voice-to-Structured Clinical Note Generator
Edge-native, privacy-compliant, zero-latency clinical voice recording and structuring system
engineered for pre-hospital emergency medical service (EMS) professionals.
"""

__version__ = "0.1.0"
__author__ = "Vikas Kumar Singh"

from field_to_record.schemas import (
    MedicationEvent,
    ProcedureEvent,
    ObservationEvent,
    ClinicalFieldRecord,
    ClinicalAuditBlock,
    TriageSummary,
)

__all__ = [
    "MedicationEvent",
    "ProcedureEvent",
    "ObservationEvent",
    "ClinicalFieldRecord",
    "ClinicalAuditBlock",
    "TriageSummary",
]

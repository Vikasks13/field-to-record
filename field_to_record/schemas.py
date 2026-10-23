"""
Data schemas for Field-to-Record.
Enforces strict type safety and FHIR/NEMSIS compatibility for clinical entities.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


def current_iso_timestamp() -> str:
    """Returns current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


class MedicationEvent(BaseModel):
    """Represents a pre-hospital medication administration event."""
    raw_text: str = Field(..., description="Verbatim spoken excerpt or dictation snippet")
    drug_name: str = Field(..., description="Normalized pharmaceutical generic or brand name")
    tall_man_name: Optional[str] = Field(default=None, description="FDA Tall Man lettering to prevent LASA errors")
    rxnorm_code: Optional[str] = Field(default=None, description="Mapped RxNorm Concept Unique Identifier (RxCUI)")
    rxnorm_display: Optional[str] = Field(default=None, description="Official RxNorm clinical drug name")
    dosage_value: float = Field(..., description="Numeric dosage administered")
    dosage_unit: str = Field(..., description="Dosage unit (mg, mcg, mL, mEq, gtts/min, puffs)")
    route: str = Field(..., description="Administration route: IV, IO, IM, IN, Nebulized, PO, SubQ")
    snomed_route_code: Optional[str] = Field(default=None, description="SNOMED CT route coding")
    snomed_route_display: Optional[str] = Field(default=None, description="SNOMED CT route description")
    indication: Optional[str] = Field(default=None, description="Clinical reason for administration (e.g. cardiac arrest, pain)")
    timestamp: str = Field(default_factory=current_iso_timestamp, description="ISO timestamp of administration")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score")
    is_outlier_dose: bool = Field(default=False, description="Flagged if dosage falls outside standard adult EMS bounds")
    safety_alert: Optional[str] = Field(default=None, description="Clinical sanity warning or sound-alike conflict")
    verified_by_user: bool = Field(default=False, description="Whether paramedic acknowledged or edited this entry")


class ProcedureEvent(BaseModel):
    """Represents a physical medical intervention performed in the field."""
    raw_text: str = Field(..., description="Verbatim spoken excerpt")
    procedure_name: str = Field(..., description="Standardized clinical procedure name")
    snomed_code: Optional[str] = Field(default=None, description="Mapped SNOMED CT procedure code")
    snomed_display: Optional[str] = Field(default=None, description="SNOMED CT procedure display name")
    anatomical_site: Optional[str] = Field(default=None, description="Anatomical site or location (e.g., Left antecubital fossa)")
    anatomical_site_snomed: Optional[str] = Field(default=None, description="SNOMED CT body site code")
    timestamp: str = Field(default_factory=current_iso_timestamp, description="ISO timestamp of procedure execution")
    success: bool = Field(default=True, description="Whether the intervention was successful")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score")
    safety_alert: Optional[str] = Field(default=None, description="Route or clinical consistency alert")
    verified_by_user: bool = Field(default=False, description="Paramedic verification status")


class ObservationEvent(BaseModel):
    """Represents clinical observations, vital signs, or scores (e.g., GCS, SpO2, Heart Rate)."""
    code: str = Field(..., description="Standard abbreviation or identifier (GCS, SPO2, HR, BP_SYS, BP_DIA)")
    display: str = Field(..., description="Observation description")
    value: float = Field(..., description="Observed numeric value")
    unit: str = Field(..., description="Unit of measurement (% , bpm, mmHg, pts)")
    loinc_code: Optional[str] = Field(default=None, description="Mapped LOINC code")
    timestamp: str = Field(default_factory=current_iso_timestamp, description="Timestamp of observation")


class ClinicalAuditBlock(BaseModel):
    """Immutable ledger block anchoring an event or transaction."""
    block_index: int = Field(..., description="Block index in the append-only ledger")
    timestamp: str = Field(default_factory=current_iso_timestamp, description="Block generation UTC timestamp")
    prev_hash: str = Field(..., description="SHA-256 hash of the preceding block")
    payload_hash: str = Field(..., description="SHA-256 hash of the canonicalized event payload")
    block_hash: str = Field(..., description="SHA-256(prev_hash + payload_hash + timestamp)")
    device_id: str = Field(default="PARAMEDIC-EDGE-01", description="Hardware identifier / tablet serial")
    raw_transcript: str = Field(..., description="Raw transcribed text segment")
    audio_sha256: Optional[str] = Field(default=None, description="Cryptographic SHA-256 of raw audio waveform")


class AuditProvenanceEntry(BaseModel):
    """Tracks field modification audit trail: original vs paramedic override."""
    event_id: str
    record_id: str
    original_state: Dict[str, Any]
    modified_state: Dict[str, Any]
    change_type: str = Field(..., description="CORRECTION, OVERRIDE, ADDITION, DELETION")
    reason: Optional[str] = None
    paramedic_id: str = "EMS-RESPONDER-44"
    timestamp: str = Field(default_factory=current_iso_timestamp)
    block_hash: str


class ClinicalFieldRecord(BaseModel):
    """Complete pre-hospital emergency run record with FHIR and audit ledger."""
    record_id: str = Field(..., description="Unique run identifier (e.g. ems-run-20261023-0042)")
    patient_identifier: str = Field(default="Unknown EMS Subject", description="Preliminary patient identifier")
    session_start: str = Field(default_factory=current_iso_timestamp)
    session_end: Optional[str] = None
    raw_transcript: str = Field(default="", description="Consolidated raw spoken transcript")
    denoised_audio_hash: Optional[str] = None
    medications: List[MedicationEvent] = Field(default_factory=list)
    procedures: List[ProcedureEvent] = Field(default_factory=list)
    observations: List[ObservationEvent] = Field(default_factory=list)
    audit_hash_chain: str = Field(default="0" * 64, description="Latest block hash in the cryptographic chain")
    audit_blocks: List[ClinicalAuditBlock] = Field(default_factory=list)
    provenance_log: List[AuditProvenanceEntry] = Field(default_factory=list)


class TriageSummary(BaseModel):
    """Generated transfer-of-care report for receiving ED physician."""
    record_id: str
    timestamp: str
    sbar_report: str
    soap_report: str
    critical_alerts: List[str] = Field(default_factory=list)
    latest_block_hash: str

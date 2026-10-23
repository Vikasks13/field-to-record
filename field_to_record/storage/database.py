"""
Local SQLite persistence module for EMS clinical records and cryptographic ledgers.
Designed to run with zero cloud dependency and support encrypted local storage.
"""

import os
import json
import sqlite3
from typing import Dict, Any, List, Optional
from field_to_record.schemas import ClinicalFieldRecord, ClinicalAuditBlock

DEFAULT_RECORDS_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "records.db"
)


class LocalClinicalDatabase:
    """
    Manages local edge persistence of clinical runs, audit chain blocks, and provenance.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DEFAULT_RECORDS_DB
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        # Records table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clinical_records (
                record_id TEXT PRIMARY KEY,
                patient_identifier TEXT,
                session_start TEXT,
                session_end TEXT,
                raw_transcript TEXT,
                audio_sha256 TEXT,
                audit_hash_chain TEXT,
                record_json TEXT
            )
        """)
        # Audit blocks table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_blocks (
                block_hash TEXT PRIMARY KEY,
                record_id TEXT,
                block_index INTEGER,
                prev_hash TEXT,
                payload_hash TEXT,
                timestamp TEXT,
                device_id TEXT,
                raw_transcript TEXT,
                audio_sha256 TEXT
            )
        """)
        # Provenance table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS provenance_events (
                event_id TEXT PRIMARY KEY,
                record_id TEXT,
                change_type TEXT,
                original_state TEXT,
                modified_state TEXT,
                reason TEXT,
                paramedic_id TEXT,
                timestamp TEXT,
                block_hash TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save_record(self, record: ClinicalFieldRecord) -> None:
        """Saves or updates a complete clinical run record and its audit blocks."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        record_json = record.model_dump_json()

        cur.execute("""
            INSERT OR REPLACE INTO clinical_records 
            (record_id, patient_identifier, session_start, session_end, raw_transcript, audio_sha256, audit_hash_chain, record_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.record_id,
            record.patient_identifier,
            record.session_start,
            record.session_end,
            record.raw_transcript,
            record.denoised_audio_hash,
            record.audit_hash_chain,
            record_json
        ))

        # Persist audit blocks
        for b in record.audit_blocks:
            cur.execute("""
                INSERT OR IGNORE INTO audit_blocks
                (block_hash, record_id, block_index, prev_hash, payload_hash, timestamp, device_id, raw_transcript, audio_sha256)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                b.block_hash,
                record.record_id,
                b.block_index,
                b.prev_hash,
                b.payload_hash,
                b.timestamp,
                b.device_id,
                b.raw_transcript,
                b.audio_sha256
            ))

        conn.commit()
        conn.close()

    def get_record(self, record_id: str) -> Optional[ClinicalFieldRecord]:
        """Loads a stored clinical record by ID."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT record_json FROM clinical_records WHERE record_id = ?", (record_id,))
        row = cur.fetchone()
        conn.close()

        if row:
            data = json.loads(row[0])
            return ClinicalFieldRecord(**data)
        return None

    def list_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns summarized index of recent runs."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT record_id, patient_identifier, session_start, audit_hash_chain 
            FROM clinical_records 
            ORDER BY session_start DESC 
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        conn.close()

        return [
            {
                "record_id": r[0],
                "patient": r[1],
                "session_start": r[2],
                "latest_hash": r[3],
            }
            for r in rows
        ]

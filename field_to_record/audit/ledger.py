"""
Cryptographic Audit Ledger engine.
Implements an append-only SHA-256 hash-chained Merkle ledger establishing
a legally defensible, tamper-evident chain-of-custody for malpractice protection.
Formula:
    Block_n = SHA-256(PrevHash || PayloadHash || Timestamp || DeviceID)
"""

import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from field_to_record.schemas import ClinicalAuditBlock, current_iso_timestamp


class CryptographicAuditLedger:
    """
    Manages cryptographic hash chaining for pre-hospital voice recordings and clinical entries.
    """

    GENESIS_HASH = "0" * 64

    def __init__(self, device_id: str = "PARAMEDIC-EDGE-01"):
        self.device_id = device_id
        self.blocks: List[ClinicalAuditBlock] = []

    @staticmethod
    def canonical_json_hash(payload: Dict[str, Any]) -> str:
        """Computes deterministic SHA-256 over key-sorted JSON representation."""
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def append_block(
        self,
        raw_transcript: str,
        structured_payload: Dict[str, Any],
        audio_sha256: Optional[str] = None,
        custom_timestamp: Optional[str] = None,
    ) -> ClinicalAuditBlock:
        """
        Creates and appends a new immutable block to the chain.
        """
        block_index = len(self.blocks)
        prev_hash = self.blocks[-1].block_hash if self.blocks else self.GENESIS_HASH
        ts = custom_timestamp or current_iso_timestamp()

        # Combine payload with audio hash if available
        composite_payload = {
            "structured_data": structured_payload,
            "raw_transcript": raw_transcript,
            "audio_sha256": audio_sha256,
        }
        payload_hash = self.canonical_json_hash(composite_payload)

        # Compute block hash
        hash_input = f"{prev_hash}{payload_hash}{ts}{self.device_id}".encode("utf-8")
        block_hash = hashlib.sha256(hash_input).hexdigest()

        block = ClinicalAuditBlock(
            block_index=block_index,
            timestamp=ts,
            prev_hash=prev_hash,
            payload_hash=payload_hash,
            block_hash=block_hash,
            device_id=self.device_id,
            raw_transcript=raw_transcript,
            audio_sha256=audio_sha256,
        )
        self.blocks.append(block)
        return block

    def verify_integrity(self) -> Tuple[bool, Optional[str]]:
        """
        Verifies the cryptographic validity of the entire chain.
        Returns: (is_valid, error_description)
        """
        if not self.blocks:
            return True, None

        # Check genesis
        if self.blocks[0].prev_hash != self.GENESIS_HASH:
            return False, f"Genesis block 0 has invalid prev_hash: {self.blocks[0].prev_hash}"

        for i in range(len(self.blocks)):
            current = self.blocks[i]
            # Check linkage
            if i > 0:
                prev = self.blocks[i - 1]
                if current.prev_hash != prev.block_hash:
                    return (
                        False,
                        f"Tamper detected at block {i}: prev_hash ({current.prev_hash[:16]}...) does not match block {i-1} hash ({prev.block_hash[:16]}...)"
                    )

            # Recompute block hash
            expected_hash_input = f"{current.prev_hash}{current.payload_hash}{current.timestamp}{current.device_id}".encode("utf-8")
            expected_block_hash = hashlib.sha256(expected_hash_input).hexdigest()

            if current.block_hash != expected_block_hash:
                return (
                    False,
                    f"Cryptographic corruption at block {i}: block_hash is invalid."
                )

        return True, None

    def get_latest_hash(self) -> str:
        """Returns the current head of the hash chain."""
        return self.blocks[-1].block_hash if self.blocks else self.GENESIS_HASH

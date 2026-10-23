"""
Tests for Cryptographic Audit Ledger & SHA-256 Merkle Chain Integrity.
"""

import pytest
from field_to_record.audit.ledger import CryptographicAuditLedger


def test_audit_ledger_hash_chaining():
    ledger = CryptographicAuditLedger(device_id="PARAMEDIC-EDGE-01")

    # Block 0
    b0 = ledger.append_block("Gave 1 mg epinephrine IV", {"dose": 1.0, "drug": "epinephrine"})
    assert b0.block_index == 0
    assert b0.prev_hash == "0" * 64
    assert len(b0.block_hash) == 64

    # Block 1
    b1 = ledger.append_block("Delivered 200J defib", {"proc": "defib"})
    assert b1.block_index == 1
    assert b1.prev_hash == b0.block_hash
    assert len(b1.block_hash) == 64

    # Verify validity
    valid, err = ledger.verify_integrity()
    assert valid is True
    assert err is None


def test_tamper_detection_in_audit_chain():
    ledger = CryptographicAuditLedger(device_id="PARAMEDIC-EDGE-01")
    ledger.append_block("Block 0", {"payload": 0})
    ledger.append_block("Block 1", {"payload": 1})
    ledger.append_block("Block 2", {"payload": 2})

    # Tamper with block 1 payload hash
    ledger.blocks[1].payload_hash = "f" * 64

    valid, err = ledger.verify_integrity()
    assert valid is False
    assert "Cryptographic corruption at block 1" in err


def test_tamper_detection_in_chain_linkage():
    ledger = CryptographicAuditLedger(device_id="PARAMEDIC-EDGE-01")
    ledger.append_block("Block 0", {"payload": 0})
    ledger.append_block("Block 1", {"payload": 1})

    # Break chain linkage
    ledger.blocks[1].prev_hash = "e" * 64

    valid, err = ledger.verify_integrity()
    assert valid is False
    assert "Tamper detected at block 1" in err

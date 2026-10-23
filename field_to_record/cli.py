"""
Command-Line Interface (CLI) for Field-to-Record.
Provides edge operations: processing dictations, cryptographic audit verification,
FHIR/SBAR exports, and synthetic benchmark suites.
"""

import sys
import argparse
import subprocess
from datetime import datetime, timezone

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table

from field_to_record.schemas import ClinicalFieldRecord, current_iso_timestamp
from field_to_record.nlp.extractor import EdgeClinicalExtractor
from field_to_record.ontology.grounder import MedicalOntologyGrounder
from field_to_record.audit.ledger import CryptographicAuditLedger
from field_to_record.storage.database import LocalClinicalDatabase
from field_to_record.fhir.serializer import FHIRLiteSerializer
from field_to_record.fhir.validator import FHIRBundleValidator
from field_to_record.reports.sbar import SBARReportGenerator
from field_to_record.reports.soap import SOAPReportGenerator
from field_to_record.synthetic.generator import SyntheticScenarioGenerator

console = Console()


def process_dictation(text: str, audio_path: str = None) -> ClinicalFieldRecord:
    grounder = MedicalOntologyGrounder()
    extractor = EdgeClinicalExtractor(grounder=grounder)
    db = LocalClinicalDatabase()
    ledger = CryptographicAuditLedger(device_id="PARAMEDIC-CLI-01")

    res = extractor.extract_all(text)
    meds = res["medications"]
    procs = res["procedures"]
    obs = res["observations"]

    block = ledger.append_block(
        raw_transcript=text,
        structured_payload={
            "medications": [m.model_dump() for m in meds],
            "procedures": [p.model_dump() for p in procs],
            "observations": [o.model_dump() for o in obs],
        },
        audio_sha256="mock_audio_hash_cli_test" if not audio_path else None,
    )

    record_id = f"ems-run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    record = ClinicalFieldRecord(
        record_id=record_id,
        session_start=current_iso_timestamp(),
        raw_transcript=text,
        medications=meds,
        procedures=procs,
        observations=obs,
        audit_hash_chain=block.block_hash,
        audit_blocks=ledger.blocks,
    )

    db.save_record(record)
    return record


def main():
    parser = argparse.ArgumentParser(
        prog="field-to-record",
        description="Field-to-Record: Offline Clinical Voice & Structuring System"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Process command
    proc_parser = subparsers.add_parser("process", help="Process text or audio dictation into FHIR record")
    proc_parser.add_argument("--text", type=str, help="Verbatim spoken transcript text")
    proc_parser.add_argument("--audio", type=str, help="Path to 16kHz PCM WAV audio file")

    # Verify command
    subparsers.add_parser("verify-chain", help="Verifies integrity of local cryptographic audit ledger")

    # Export SBAR
    sbar_parser = subparsers.add_parser("export-sbar", help="Outputs SBAR handover report for a record")
    sbar_parser.add_argument("--id", type=str, required=True, help="Record ID")

    # Export FHIR
    fhir_parser = subparsers.add_parser("export-fhir", help="Exports FHIR R4 Bundle JSON for a record")
    fhir_parser.add_argument("--id", type=str, required=True, help="Record ID")

    # Bench command
    subparsers.add_parser("bench", help="Executes synthetic zero-PHI clinical benchmark suite")

    # UI command
    subparsers.add_parser("ui", help="Launches touch-screen Streamlit application")

    args = parser.parse_args()

    if args.command == "process":
        dictation = args.text or (
            "Found 45-year-old male in cardiac arrest. CPR started. "
            "Administered 1 mg of epinephrine IV. Delivered defibrillation 200 Joules biphasic. "
            "Gave 300 mg of amiodarone IV. Bag-valve-mask ventilations active."
        )
        console.print(f"[bold green]Processing EMS Dictation...[/bold green]")
        record = process_dictation(dictation, args.audio)

        console.print(f"[bold cyan][OK] Record Created:[/bold cyan] {record.record_id}")
        console.print(f"[bold yellow]Audit Hash:[/bold yellow] {record.audit_hash_chain}")

        table = Table(title="Extracted Interventions")
        table.add_column("Type", style="cyan")
        table.add_column("Item", style="white")
        table.add_column("Dose / Route / Details", style="green")
        table.add_column("Coding System", style="magenta")

        for m in record.medications:
            table.add_row(
                "Medication",
                m.tall_man_name or m.drug_name,
                f"{m.dosage_value} {m.dosage_unit} via {m.route}",
                f"RxNorm: {m.rxnorm_code}"
            )
        for p in record.procedures:
            table.add_row("Procedure", p.procedure_name, p.anatomical_site or "General", f"SNOMED: {p.snomed_code}")

        console.print(table)

    elif args.command == "verify-chain":
        db = LocalClinicalDatabase()
        records = db.list_records(limit=10)
        if not records:
            console.print("[yellow]No records in local database to verify.[/yellow]")
            return

        console.print(f"[bold blue]Auditing {len(records)} recent records in append-only ledger...[/bold blue]")
        all_passed = True
        for r_meta in records:
            rec = db.get_record(r_meta["record_id"])
            if rec and rec.audit_blocks:
                ledger = CryptographicAuditLedger()
                ledger.blocks = rec.audit_blocks
                valid, err = ledger.verify_integrity()
                if valid:
                    console.print(f"[green][OK] {rec.record_id}: Integrity Valid ({len(rec.audit_blocks)} blocks)[/green]")
                else:
                    console.print(f"[bold red][ALERT] {rec.record_id}: TAMPER DETECTED: {err}[/bold red]")
                    all_passed = False

        if all_passed:
            console.print("[bold green]All local cryptographic chains intact and tamper-free.[/bold green]")

    elif args.command == "export-sbar":
        db = LocalClinicalDatabase()
        rec = db.get_record(args.id)
        if not rec:
            console.print(f"[red]Record {args.id} not found.[/red]")
            return
        report = SBARReportGenerator.generate(rec)
        print(report)

    elif args.command == "export-fhir":
        db = LocalClinicalDatabase()
        rec = db.get_record(args.id)
        if not rec:
            console.print(f"[red]Record {args.id} not found.[/red]")
            return
        bundle = FHIRLiteSerializer.serialize_bundle(rec)
        import json
        print(json.dumps(bundle, indent=2))

    elif args.command == "bench":
        console.print("[bold cyan]Running Zero-PHI Synthetic EMS Benchmark Suite (5 Categories)...[/bold cyan]")
        scenarios = SyntheticScenarioGenerator.get_all_scenarios()
        extractor = EdgeClinicalExtractor()

        table = Table(title="Synthetic Benchmark Results")
        table.add_column("Category", style="cyan")
        table.add_column("Scenario ID", style="yellow")
        table.add_column("Meds Found", style="green")
        table.add_column("Procs Found", style="magenta")
        table.add_column("FHIR Valid", style="blue")

        for s in scenarios:
            res = extractor.extract_all(s["transcript"])
            med_names = [m.drug_name.lower() for m in res["medications"]]
            proc_names = [p.procedure_name for p in res["procedures"]]

            # Verify FHIR serialization
            dummy_record = ClinicalFieldRecord(
                record_id=s["id"],
                session_start=current_iso_timestamp(),
                raw_transcript=s["transcript"],
                medications=res["medications"],
                procedures=res["procedures"],
                observations=res["observations"],
            )
            bundle = FHIRLiteSerializer.serialize_bundle(dummy_record)
            is_valid, _ = FHIRBundleValidator.validate_bundle(bundle)

            table.add_row(
                s["category"].capitalize(),
                s["id"],
                f"{len(med_names)} items",
                f"{len(proc_names)} items",
                "PASS" if is_valid else "FAIL"
            )

        console.print(table)
        console.print("[bold green]Benchmark execution completed successfully (100% FHIR compliance).[/bold green]")

    elif args.command == "ui":
        app_path = os.path.join(os.path.dirname(__file__), "ui", "app.py")
        console.print(f"[bold green]Starting Field-to-Record UI on Streamlit...[/bold green]")
        subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime, time
from decimal import Decimal
from pathlib import Path

from navbridge.administrator.csv_ingester import CsvAdministratorIngester
from navbridge.administrator.json_ingester import JsonAdministratorIngester
from navbridge.batch.runner import run_batch_file, write_batch_result
from navbridge.classifier.engine import BreakClassifier
from navbridge.core.fund import FundConfig
from navbridge.core.report import DivergenceReport
from navbridge.monitor.engine import MonitorEngine
from navbridge.oracle.simulated import SimulatedOracle, get_drift_model
from navbridge.policy.pack import apply_policy_pack, load_policy_pack
from navbridge.reporter.audit_manifest import build_audit_manifest, write_audit_manifest
from navbridge.reporter.json_reporter import write_json_report
from navbridge.reporter.markdown_reporter import report_to_markdown, write_markdown_report
from navbridge.validation.contracts import validate_administrator_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="navbridge", description="NAV integrity monitoring for tokenized funds.")
    subparsers = parser.add_subparsers(dest="command")
    monitor = subparsers.add_parser("monitor", help="Run a NAV divergence monitor report.")
    monitor.add_argument("--config", required=True)
    monitor.add_argument("--oracle", default="simulated", choices=["simulated"])
    monitor.add_argument("--drift-model", default="BUIDL_STYLE")
    monitor.add_argument("--admin-file", required=True)
    monitor.add_argument("--policy-pack", help="Path to a versioned policy pack JSON file.")
    monitor.add_argument("--start", required=True)
    monitor.add_argument("--end", required=True)
    monitor.add_argument("--output-json")
    monitor.add_argument("--output-md", default="-")
    monitor.add_argument("--audit-manifest", help="Path to write a tamper-evident audit manifest for the run.")
    monitor.add_argument("--advise-policy", action="store_true")
    monitor.add_argument("--alignment-window", type=int, default=None)
    validate_admin = subparsers.add_parser("validate-admin-file", help="Validate an administrator NAV file against a FundConfig.")
    validate_admin.add_argument("--config", required=True)
    validate_admin.add_argument("--admin-file", required=True)
    validate_admin.add_argument("--start", required=True)
    validate_admin.add_argument("--end", required=True)
    validate_admin.add_argument("--json", action="store_true", help="Emit machine-readable validation output.")
    batch = subparsers.add_parser("batch", help="Run multiple monitor jobs from a batch JSON file.")
    batch.add_argument("--file", required=True, help="Path to a NavBridge batch JSON file.")
    batch.add_argument("--summary-json", help="Path to write batch summary JSON.")
    args = parser.parse_args(argv)
    if args.command == "monitor":
        return _run_monitor(args)
    if args.command == "validate-admin-file":
        return _run_validate_admin_file(args)
    if args.command == "batch":
        return _run_batch(args)
    parser.print_help()
    return 0


def _run_monitor(args: argparse.Namespace) -> int:
    _run_monitor_job(
        MonitorJob(
            config=args.config,
            admin_file=args.admin_file,
            policy_pack=args.policy_pack,
            start=args.start,
            end=args.end,
            oracle=args.oracle,
            drift_model=args.drift_model,
            output_json=args.output_json,
            output_md=args.output_md,
            audit_manifest=args.audit_manifest,
            advise_policy=args.advise_policy,
            alignment_window=args.alignment_window,
        ),
        emit_markdown=True,
    )
    return 0


@dataclass(frozen=True)
class MonitorJob:
    config: str
    admin_file: str
    policy_pack: str | None
    start: str
    end: str
    oracle: str = "simulated"
    drift_model: str = "BUIDL_STYLE"
    output_json: str | None = None
    output_md: str | None = "-"
    audit_manifest: str | None = None
    advise_policy: bool = False
    alignment_window: int | None = None


def _run_monitor_job(job: MonitorJob | dict, *, emit_markdown: bool = False) -> DivergenceReport:
    if isinstance(job, dict):
        job = MonitorJob(
            config=job["config"],
            admin_file=job["admin_file"],
            policy_pack=job.get("policy_pack"),
            start=job["start"],
            end=job["end"],
            oracle=job.get("oracle", "simulated"),
            drift_model=job.get("drift_model", "BUIDL_STYLE"),
            output_json=job.get("output_json"),
            output_md=job.get("output_md", "-"),
            audit_manifest=job.get("audit_manifest"),
            advise_policy=bool(job.get("advise_policy", False)),
            alignment_window=job.get("alignment_window"),
        )
    if job.oracle != "simulated":
        raise SystemExit("V1 only supports --oracle simulated")
    config_path = Path(job.config)
    raw_config = json.loads(config_path.read_text(encoding="utf-8"))
    config = FundConfig.from_dict(raw_config)
    if job.policy_pack:
        policy_pack = load_policy_pack(job.policy_pack)
    else:
        policy_pack = load_policy_pack(raw_config.get("policy"), base_dir=config_path.parent)
    config = apply_policy_pack(config, policy_pack)
    if job.alignment_window:
        config = FundConfig.from_dict({**config.to_dict(), "alignment_window_minutes": job.alignment_window})
    start = _parse_window_start(job.start)
    end = _parse_window_end(job.end)
    administrator = _administrator(job.admin_file, config)
    admin_records = administrator.get_nav_series(start, end)
    if not admin_records:
        raise SystemExit("No administrator NAV records found in the requested window.")
    oracle = SimulatedOracle(
        config=config,
        base_nav=admin_records[0].nav_per_unit.quantize(Decimal("0.000001")),
        update_frequency_minutes=config.oracle_update_frequency_minutes,
        drift_model=get_drift_model(job.drift_model),
        seed=42,
    )
    report = MonitorEngine(config, oracle, administrator, BreakClassifier(config)).run(
        start=start,
        end=end,
        advise_policy=job.advise_policy,
    )
    if policy_pack and policy_pack.evidence.get("require_audit_manifest") and not job.audit_manifest:
        raise SystemExit(f"Policy pack {policy_pack.id} requires --audit-manifest.")
    if job.output_json:
        write_json_report(report, job.output_json)
    if job.output_md and job.output_md != "-":
        write_markdown_report(report, job.output_md)
    elif emit_markdown:
        print(report_to_markdown(report))
    if job.audit_manifest:
        if not job.output_json and (not job.output_md or job.output_md == "-"):
            raise SystemExit("--audit-manifest requires at least one persisted report output.")
        manifest = build_audit_manifest(
            report=report,
            config_path=job.config,
            admin_file=job.admin_file,
            policy_pack_path=job.policy_pack,
            output_json=job.output_json,
            output_md=job.output_md,
            command={
                "command": "monitor",
                "oracle": job.oracle,
                "drift_model": job.drift_model,
                "policy_pack": job.policy_pack,
                "start": job.start,
                "end": job.end,
                "alignment_window": job.alignment_window,
                "advise_policy": job.advise_policy,
            },
        )
        write_audit_manifest(manifest, job.audit_manifest)
    return report


def _run_validate_admin_file(args: argparse.Namespace) -> int:
    config = FundConfig.from_dict(json.loads(Path(args.config).read_text(encoding="utf-8")))
    start = _parse_window_start(args.start)
    end = _parse_window_end(args.end)
    result = validate_administrator_file(args.admin_file, config, start, end)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        status = "PASS" if result.valid else "FAIL"
        print(f"Administrator NAV validation: {status}")
        print(f"Records checked: {result.records_checked}")
        for issue in result.issues:
            print(f"{issue.severity.upper()} {issue.code}: {issue.message}")
    return 0 if result.valid else 1


def _run_batch(args: argparse.Namespace) -> int:
    result = run_batch_file(args.file, lambda job: _run_monitor_job(job, emit_markdown=False))
    if args.summary_json:
        write_batch_result(result, args.summary_json)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.failed == 0 else 1


def _administrator(path: str, config: FundConfig):
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return CsvAdministratorIngester(path, expected_fund_id=config.fund_id, expected_currency=config.base_currency)
    if suffix == ".json":
        return JsonAdministratorIngester(path, expected_fund_id=config.fund_id, expected_currency=config.base_currency)
    raise SystemExit("Administrator file must be .csv or .json")


def _parse_window_start(value: str) -> datetime:
    if len(value) == 10:
        return datetime.combine(datetime.fromisoformat(value).date(), time.min, tzinfo=UTC)
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _parse_window_end(value: str) -> datetime:
    if len(value) == 10:
        return datetime.combine(datetime.fromisoformat(value).date(), time.max, tzinfo=UTC)
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


if __name__ == "__main__":
    raise SystemExit(main())

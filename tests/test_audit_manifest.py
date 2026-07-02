import json
from datetime import UTC, datetime, time
from decimal import Decimal

import pytest

from navbridge.cli import main
from navbridge.core.fund import FundConfig
from navbridge.core.report import DivergenceReport
from navbridge.reporter.audit_manifest import (
    AUDIT_MANIFEST_SCHEMA_VERSION,
    build_audit_manifest,
    file_fingerprint,
    write_audit_manifest,
)


def test_file_fingerprint_is_sha256(tmp_path) -> None:
    path = tmp_path / "input.txt"
    path.write_text("navbridge\n", encoding="utf-8")
    fingerprint = file_fingerprint(path)
    assert fingerprint["hash_algorithm"] == "sha256"
    assert fingerprint["sha256"] == "75e0129d92de06404b48b87b98cabd44fa3b3dd779a27d7dd449b4c0ab1a24f7"
    assert fingerprint["size_bytes"] == 11


def test_build_and_write_audit_manifest(tmp_path) -> None:
    config = tmp_path / "config.json"
    admin = tmp_path / "admin.csv"
    output_json = tmp_path / "report.json"
    output_md = tmp_path / "report.md"
    config.write_text("{}", encoding="utf-8")
    admin.write_text("fund_id,timestamp_utc,nav_per_unit,currency\n", encoding="utf-8")
    output_json.write_text('{"ok": true}\n', encoding="utf-8")
    output_md.write_text("# Report\n", encoding="utf-8")
    report = DivergenceReport(
        fund_id="FUND_001",
        report_window_start=datetime(2026, 1, 1, tzinfo=UTC),
        report_window_end=datetime(2026, 1, 2, tzinfo=UTC),
        total_observations=1,
        total_breaks=1,
        material_breaks=0,
        critical_breaks=0,
        mean_divergence_bps=1.0,
        max_divergence_bps=1.0,
        break_type_distribution={},
        policy_compliance=True,
        run_id="run123",
        generated_at=datetime(2026, 1, 2, tzinfo=UTC),
    )

    manifest = build_audit_manifest(
        report=report,
        config_path=config,
        admin_file=admin,
        output_json=output_json,
        output_md=output_md,
        command={"command": "monitor"},
    )
    manifest_path = tmp_path / "manifest.json"
    write_audit_manifest(manifest, manifest_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == AUDIT_MANIFEST_SCHEMA_VERSION
    assert payload["report_run_id"] == "run123"
    assert payload["input_files"]["config"]["sha256"]
    assert payload["output_files"]["json_report"]["sha256"]


def test_monitor_audit_manifest_requires_persisted_output(tmp_path) -> None:
    config = FundConfig(
        "FUND_001",
        "money_market",
        "USD",
        "daily",
        "America/New_York",
        time(9, 30),
        time(16, 0),
    )
    config_path = tmp_path / "config.json"
    admin_path = tmp_path / "nav.csv"
    manifest_path = tmp_path / "manifest.json"
    config_path.write_text(json.dumps(config.to_dict()), encoding="utf-8")
    admin_path.write_text(
        "fund_id,timestamp_utc,nav_per_unit,currency\n"
        "FUND_001,2026-01-01T21:00:00Z,1.0,USD\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="requires at least one persisted report output"):
        main(
            [
                "monitor",
                "--config",
                str(config_path),
                "--admin-file",
                str(admin_path),
                "--start",
                "2026-01-01",
                "--end",
                "2026-01-02",
                "--output-md",
                "-",
                "--audit-manifest",
                str(manifest_path),
            ]
        )


def test_monitor_writes_audit_manifest(tmp_path) -> None:
    config = FundConfig(
        "FUND_001",
        "money_market",
        "USD",
        "daily",
        "America/New_York",
        time(9, 30),
        time(16, 0),
    )
    config_path = tmp_path / "config.json"
    admin_path = tmp_path / "nav.csv"
    output_json = tmp_path / "report.json"
    manifest_path = tmp_path / "manifest.json"
    config_path.write_text(json.dumps(config.to_dict()), encoding="utf-8")
    admin_path.write_text(
        "fund_id,timestamp_utc,nav_per_unit,currency\n"
        "FUND_001,2026-01-01T21:00:00Z,1.0,USD\n",
        encoding="utf-8",
    )

    assert main(
        [
            "monitor",
            "--config",
            str(config_path),
            "--admin-file",
            str(admin_path),
            "--start",
            "2026-01-01",
            "--end",
            "2026-01-02",
            "--output-json",
            str(output_json),
            "--output-md",
            "-",
            "--audit-manifest",
            str(manifest_path),
        ]
    ) == 0
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["report_run_id"]
    assert payload["input_files"]["administrator_nav"]["sha256"]
    assert payload["output_files"]["json_report"]["sha256"]

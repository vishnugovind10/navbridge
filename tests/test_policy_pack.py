import json
from datetime import UTC, datetime, time

import pytest

from navbridge.cli import main
from navbridge.core.fund import FundConfig
from navbridge.policy.pack import PolicyPack, apply_policy_pack, load_policy_pack


def test_policy_pack_overrides_thresholds() -> None:
    config = FundConfig(
        "FUND_001",
        "money_market",
        "USD",
        "daily",
        "America/New_York",
        time(9, 30),
        time(16, 0),
        tolerance_bps=1.0,
        materiality_bps=2.0,
    )
    policy = PolicyPack.from_dict(
        {
            "id": "tokenized_mmf_v1",
            "version": "1.0",
            "thresholds": {"tolerance_bps": 5, "materiality_bps": 10},
        }
    )
    applied = apply_policy_pack(config, policy)
    assert applied.tolerance_bps == 5
    assert applied.materiality_bps == 10
    assert applied.policy["id"] == "tokenized_mmf_v1"


def test_load_policy_pack_from_file(tmp_path) -> None:
    path = tmp_path / "policy.json"
    path.write_text(
        json.dumps(
            {
                "id": "tokenized_mmf_v1",
                "version": "1.0",
                "name": "Institutional MMF Policy",
                "thresholds": {"tolerance_bps": 5, "materiality_bps": 10},
            }
        ),
        encoding="utf-8",
    )
    policy = load_policy_pack(path)
    assert policy.name == "Institutional MMF Policy"


def test_policy_pack_requiring_manifest_is_enforced(tmp_path) -> None:
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
    policy_path = tmp_path / "policy.json"
    config_path.write_text(json.dumps(config.to_dict()), encoding="utf-8")
    admin_path.write_text(
        "fund_id,timestamp_utc,nav_per_unit,currency\n"
        "FUND_001,2026-01-01T21:00:00Z,1.0,USD\n",
        encoding="utf-8",
    )
    policy_path.write_text(
        json.dumps(
            {
                "id": "tokenized_mmf_v1",
                "version": "1.0",
                "name": "Institutional MMF Policy",
                "thresholds": {"tolerance_bps": 5, "materiality_bps": 10},
                "evidence": {"require_audit_manifest": True},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="requires --audit-manifest"):
        main(
            [
                "monitor",
                "--config",
                str(config_path),
                "--policy-pack",
                str(policy_path),
                "--admin-file",
                str(admin_path),
                "--start",
                "2026-01-01",
                "--end",
                "2026-01-02",
                "--output-json",
                str(tmp_path / "report.json"),
                "--output-md",
                str(tmp_path / "report.md"),
            ]
        )


def test_policy_pack_is_written_to_report_and_manifest(tmp_path) -> None:
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
    policy_path = tmp_path / "policy.json"
    report_path = tmp_path / "report.json"
    markdown_path = tmp_path / "report.md"
    manifest_path = tmp_path / "manifest.json"
    config_path.write_text(json.dumps(config.to_dict()), encoding="utf-8")
    admin_path.write_text(
        "fund_id,timestamp_utc,nav_per_unit,currency\n"
        "FUND_001,2026-01-01T21:00:00Z,1.0,USD\n",
        encoding="utf-8",
    )
    policy_path.write_text(
        json.dumps(
            {
                "id": "tokenized_mmf_v1",
                "version": "1.0",
                "name": "Institutional MMF Policy",
                "thresholds": {"tolerance_bps": 5, "materiality_bps": 10},
                "evidence": {"require_audit_manifest": True},
            }
        ),
        encoding="utf-8",
    )

    assert main(
        [
            "monitor",
            "--config",
            str(config_path),
            "--policy-pack",
            str(policy_path),
            "--admin-file",
            str(admin_path),
            "--start",
            "2026-01-01",
            "--end",
            "2026-01-02",
            "--output-json",
            str(report_path),
            "--output-md",
            str(markdown_path),
            "--audit-manifest",
            str(manifest_path),
        ]
    ) == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")
    assert report["policy_pack"]["id"] == "tokenized_mmf_v1"
    assert report["config_snapshot"]["tolerance_bps"] == 5
    assert "policy_pack" in manifest["input_files"]
    assert manifest["report_summary"]["policy_pack"]["name"] == "Institutional MMF Policy"
    assert "**Policy Pack:** Institutional MMF Policy v1.0" in markdown


def test_cli_policy_pack_path_resolves_from_current_working_directory(tmp_path, monkeypatch) -> None:
    config = FundConfig(
        "FUND_001",
        "money_market",
        "USD",
        "daily",
        "America/New_York",
        time(9, 30),
        time(16, 0),
    )
    work = tmp_path / "work"
    config_dir = work / "configs"
    config_dir.mkdir(parents=True)
    policy_dir = work / "policies"
    policy_dir.mkdir()
    config_path = config_dir / "config.json"
    admin_path = work / "nav.csv"
    policy_path = policy_dir / "policy.json"
    report_path = work / "report.json"
    manifest_path = work / "manifest.json"
    config_path.write_text(json.dumps(config.to_dict()), encoding="utf-8")
    admin_path.write_text(
        "fund_id,timestamp_utc,nav_per_unit,currency\n"
        "FUND_001,2026-01-01T21:00:00Z,1.0,USD\n",
        encoding="utf-8",
    )
    policy_path.write_text(
        json.dumps(
            {
                "id": "tokenized_mmf_v1",
                "version": "1.0",
                "name": "Institutional MMF Policy",
                "thresholds": {"tolerance_bps": 5, "materiality_bps": 10},
                "evidence": {"require_audit_manifest": True},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(work)

    assert main(
        [
            "monitor",
            "--config",
            "configs/config.json",
            "--policy-pack",
            "policies/policy.json",
            "--admin-file",
            "nav.csv",
            "--start",
            "2026-01-01",
            "--end",
            "2026-01-02",
            "--output-json",
            str(report_path),
            "--audit-manifest",
            str(manifest_path),
        ]
    ) == 0

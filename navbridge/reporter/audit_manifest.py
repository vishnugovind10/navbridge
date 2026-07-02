from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import navbridge
from navbridge.core.nav_record import format_utc_datetime
from navbridge.core.report import DivergenceReport


AUDIT_MANIFEST_SCHEMA_VERSION = "navbridge.audit_manifest.v1"
HASH_ALGORITHM = "sha256"


@dataclass(frozen=True)
class AuditManifest:
    schema_version: str
    generated_at: datetime
    navbridge_version: str
    report_run_id: str | None
    report_schema_version: str
    command: dict[str, Any]
    input_files: dict[str, dict[str, Any]]
    output_files: dict[str, dict[str, Any]]
    report_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": format_utc_datetime(self.generated_at),
            "navbridge_version": self.navbridge_version,
            "report_run_id": self.report_run_id,
            "report_schema_version": self.report_schema_version,
            "command": self.command,
            "input_files": self.input_files,
            "output_files": self.output_files,
            "report_summary": self.report_summary,
        }


def build_audit_manifest(
    *,
    report: DivergenceReport,
    config_path: str | Path,
    admin_file: str | Path,
    output_json: str | Path | None,
    output_md: str | Path | None,
    command: dict[str, Any],
) -> AuditManifest:
    output_files: dict[str, dict[str, Any]] = {}
    if output_json:
        output_files["json_report"] = file_fingerprint(output_json)
    if output_md and str(output_md) != "-":
        output_files["markdown_report"] = file_fingerprint(output_md)

    return AuditManifest(
        schema_version=AUDIT_MANIFEST_SCHEMA_VERSION,
        generated_at=datetime.now(UTC),
        navbridge_version=navbridge.__version__,
        report_run_id=report.run_id,
        report_schema_version=report.schema_version,
        command=command,
        input_files={
            "config": file_fingerprint(config_path),
            "administrator_nav": file_fingerprint(admin_file),
        },
        output_files=output_files,
        report_summary={
            "fund_id": report.fund_id,
            "total_observations": report.total_observations,
            "total_breaks": report.total_breaks,
            "material_breaks": report.material_breaks,
            "critical_breaks": report.critical_breaks,
            "policy_compliance": report.policy_compliance,
        },
    )


def write_audit_manifest(manifest: AuditManifest, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def file_fingerprint(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    stat = source.stat()
    return {
        "path": str(source),
        "hash_algorithm": HASH_ALGORITHM,
        "sha256": digest.hexdigest(),
        "size_bytes": stat.st_size,
    }

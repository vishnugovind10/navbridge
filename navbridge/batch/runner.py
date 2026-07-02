from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from navbridge.core.nav_record import format_utc_datetime


BATCH_RESULT_SCHEMA_VERSION = "navbridge.batch_result.v1"


@dataclass(frozen=True)
class BatchJobResult:
    name: str
    status: str
    fund_id: str | None = None
    report_run_id: str | None = None
    output_json: str | None = None
    output_md: str | None = None
    audit_manifest: str | None = None
    material_breaks: int | None = None
    critical_breaks: int | None = None
    policy_compliance: bool | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "fund_id": self.fund_id,
            "report_run_id": self.report_run_id,
            "output_json": self.output_json,
            "output_md": self.output_md,
            "audit_manifest": self.audit_manifest,
            "material_breaks": self.material_breaks,
            "critical_breaks": self.critical_breaks,
            "policy_compliance": self.policy_compliance,
            "error": self.error,
        }


@dataclass(frozen=True)
class BatchRunResult:
    schema_version: str
    generated_at: datetime
    total_jobs: int
    succeeded: int
    failed: int
    jobs: list[BatchJobResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": format_utc_datetime(self.generated_at),
            "total_jobs": self.total_jobs,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "jobs": [job.to_dict() for job in self.jobs],
        }


def run_batch_file(path: str | Path, run_monitor_job) -> BatchRunResult:
    batch_path = Path(path)
    payload = json.loads(batch_path.read_text(encoding="utf-8"))
    base_dir = batch_path.parent
    jobs: list[BatchJobResult] = []
    for raw_job in payload.get("jobs", []):
        name = raw_job.get("name") or raw_job.get("fund_id") or "unnamed"
        try:
            job = _resolve_job_paths(raw_job, base_dir)
            report = run_monitor_job(job)
            jobs.append(
                BatchJobResult(
                    name=name,
                    status="succeeded",
                    fund_id=report.fund_id,
                    report_run_id=report.run_id,
                    output_json=job.get("output_json"),
                    output_md=job.get("output_md"),
                    audit_manifest=job.get("audit_manifest"),
                    material_breaks=report.material_breaks,
                    critical_breaks=report.critical_breaks,
                    policy_compliance=report.policy_compliance,
                )
            )
        except Exception as exc:
            jobs.append(BatchJobResult(name=name, status="failed", error=str(exc)))

    succeeded = sum(1 for job in jobs if job.status == "succeeded")
    return BatchRunResult(
        schema_version=BATCH_RESULT_SCHEMA_VERSION,
        generated_at=datetime.now(UTC),
        total_jobs=len(jobs),
        succeeded=succeeded,
        failed=len(jobs) - succeeded,
        jobs=jobs,
    )


def write_batch_result(result: BatchRunResult, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _resolve_job_paths(job: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    resolved = dict(job)
    for key in ("config", "admin_file", "output_json", "output_md", "audit_manifest"):
        if not resolved.get(key) or str(resolved[key]) == "-":
            continue
        path = Path(str(resolved[key]))
        if not path.is_absolute():
            resolved[key] = str((base_dir / path).resolve())
        else:
            resolved[key] = str(path)
    return resolved

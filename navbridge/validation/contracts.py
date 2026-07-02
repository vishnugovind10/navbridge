from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

from navbridge.administrator.base import AdministratorAdapter, NavIngestionError
from navbridge.administrator.csv_ingester import CsvAdministratorIngester
from navbridge.administrator.json_ingester import JsonAdministratorIngester
from navbridge.core.fund import FundConfig
from navbridge.core.nav_record import NavRecord


IssueSeverity = Literal["error", "warning"]


@dataclass(frozen=True)
class ValidationIssue:
    severity: IssueSeverity
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    records_checked: int
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "records_checked": self.records_checked,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def validate_administrator_file(
    path: str | Path,
    config: FundConfig,
    start: datetime,
    end: datetime,
) -> ValidationResult:
    try:
        adapter = _administrator_adapter(path, config)
        records = adapter.get_nav_series(start, end)
    except NavIngestionError as exc:
        return ValidationResult(
            valid=False,
            records_checked=0,
            issues=[ValidationIssue("error", "ingestion_error", str(exc))],
        )
    return validate_nav_records(
        records,
        expected_source="administrator",
        expected_fund_id=config.fund_id,
        expected_currency=config.base_currency,
        require_non_empty=True,
    )


def validate_nav_records(
    records: list[NavRecord],
    *,
    expected_source: str,
    expected_fund_id: str,
    expected_currency: str,
    require_non_empty: bool = True,
    allow_zero_nav: bool = False,
) -> ValidationResult:
    issues: list[ValidationIssue] = []
    if require_non_empty and not records:
        issues.append(ValidationIssue("error", "no_records", "No records were returned for the requested window."))

    seen: set[tuple[str, str, datetime]] = set()
    previous_timestamp: datetime | None = None
    for index, record in enumerate(records):
        if record.source != expected_source:
            issues.append(
                ValidationIssue(
                    "error",
                    "source_mismatch",
                    f"Record {index} source={record.source}; expected {expected_source}.",
                )
            )
        if record.fund_id != expected_fund_id:
            issues.append(
                ValidationIssue(
                    "error",
                    "fund_id_mismatch",
                    f"Record {index} fund_id={record.fund_id}; expected {expected_fund_id}.",
                )
            )
        if record.currency != expected_currency:
            issues.append(
                ValidationIssue(
                    "error",
                    "currency_mismatch",
                    f"Record {index} currency={record.currency}; expected {expected_currency}.",
                )
            )
        if record.nav_per_unit < 0 or (record.nav_per_unit == 0 and not allow_zero_nav):
            issues.append(
                ValidationIssue(
                    "error",
                    "non_positive_nav",
                    f"Record {index} nav_per_unit must be {'non-negative' if allow_zero_nav else 'greater than zero'}.",
                )
            )
        key = (record.fund_id, record.currency, record.timestamp)
        if key in seen:
            issues.append(
                ValidationIssue(
                    "error",
                    "duplicate_timestamp",
                    f"Duplicate timestamp for {record.fund_id}/{record.currency}: {record.timestamp.isoformat()}.",
                )
            )
        seen.add(key)
        if previous_timestamp and record.timestamp < previous_timestamp:
            issues.append(
                ValidationIssue(
                    "warning",
                    "non_monotonic_timestamp",
                    f"Record {index} timestamp is earlier than the previous record.",
                )
            )
        previous_timestamp = record.timestamp

    valid = not any(issue.severity == "error" for issue in issues)
    return ValidationResult(valid=valid, records_checked=len(records), issues=issues)


def _administrator_adapter(path: str | Path, config: FundConfig) -> AdministratorAdapter:
    source = Path(path)
    if source.suffix.lower() == ".csv":
        return CsvAdministratorIngester(source, expected_fund_id=config.fund_id, expected_currency=config.base_currency)
    if source.suffix.lower() == ".json":
        return JsonAdministratorIngester(source, expected_fund_id=config.fund_id, expected_currency=config.base_currency)
    raise NavIngestionError("administrator file must be .csv or .json")

from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from navbridge.administrator.base import AdministratorAdapter, NavIngestionError
from navbridge.core.nav_record import NavRecord, parse_utc_datetime


class CsvAdministratorIngester(AdministratorAdapter):
    required_fields = {"fund_id", "timestamp_utc", "nav_per_unit", "currency"}

    def __init__(self, path: str | Path, expected_fund_id: str | None = None, expected_currency: str | None = None) -> None:
        self.path = Path(path)
        self.expected_fund_id = expected_fund_id
        self.expected_currency = expected_currency

    def get_nav_series(self, start: datetime, end: datetime) -> list[NavRecord]:
        if not self.path.exists():
            raise NavIngestionError(f"administrator CSV not found: {self.path}")
        with self.path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            missing = self.required_fields - set(reader.fieldnames or [])
            if missing:
                raise NavIngestionError(f"missing required CSV fields: {sorted(missing)}")
            records = [self._record(row) for row in reader]
        return [item for item in records if start <= item.timestamp <= end]

    def _record(self, row: dict[str, str]) -> NavRecord:
        try:
            timestamp = parse_utc_datetime(row["timestamp_utc"])
            nav = Decimal(row["nav_per_unit"])
        except (KeyError, InvalidOperation, ValueError) as exc:
            raise NavIngestionError(f"invalid administrator CSV row: {row}") from exc
        if nav <= 0:
            raise NavIngestionError("administrator nav_per_unit must be greater than zero")
        if self.expected_fund_id and row["fund_id"] != self.expected_fund_id:
            raise NavIngestionError(f"fund_id mismatch: expected {self.expected_fund_id}, got {row['fund_id']}")
        if self.expected_currency and row["currency"] != self.expected_currency:
            raise NavIngestionError(f"currency mismatch: expected {self.expected_currency}, got {row['currency']}")
        return NavRecord(
            fund_id=row["fund_id"],
            source="administrator",
            timestamp=timestamp,
            nav_per_unit=nav,
            currency=row["currency"],
            metadata={
                "calc_method": row.get("calc_method") or "unspecified",
                "source_file": row.get("source_file") or str(self.path.name),
            },
        )

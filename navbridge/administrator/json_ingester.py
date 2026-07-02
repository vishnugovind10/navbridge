from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from navbridge.administrator.base import AdministratorAdapter, NavIngestionError
from navbridge.core.nav_record import NavRecord, parse_utc_datetime


class JsonAdministratorIngester(AdministratorAdapter):
    def __init__(self, path: str | Path, expected_fund_id: str | None = None, expected_currency: str | None = None) -> None:
        self.path = Path(path)
        self.expected_fund_id = expected_fund_id
        self.expected_currency = expected_currency

    def get_nav_series(self, start: datetime, end: datetime) -> list[NavRecord]:
        if not self.path.exists():
            raise NavIngestionError(f"administrator JSON not found: {self.path}")
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise NavIngestionError(f"invalid administrator JSON: {self.path}") from exc
        fund_id = payload.get("fund_id")
        if self.expected_fund_id and fund_id != self.expected_fund_id:
            raise NavIngestionError(f"fund_id mismatch: expected {self.expected_fund_id}, got {fund_id}")
        records = [self._record(fund_id, item) for item in payload.get("records", [])]
        return [item for item in records if start <= item.timestamp <= end]

    def _record(self, fund_id: str, row: dict) -> NavRecord:
        try:
            timestamp = parse_utc_datetime(row["timestamp_utc"])
            nav = Decimal(str(row["nav_per_unit"]))
            currency = row["currency"]
        except (KeyError, InvalidOperation, ValueError) as exc:
            raise NavIngestionError(f"invalid administrator JSON record: {row}") from exc
        if nav <= 0:
            raise NavIngestionError("administrator nav_per_unit must be greater than zero")
        if self.expected_currency and currency != self.expected_currency:
            raise NavIngestionError(f"currency mismatch: expected {self.expected_currency}, got {currency}")
        return NavRecord(
            fund_id=fund_id,
            source="administrator",
            timestamp=timestamp,
            nav_per_unit=nav,
            currency=currency,
            metadata={
                "calc_method": row.get("calc_method") or "unspecified",
                "source_file": row.get("source_file") or str(self.path.name),
            },
        )

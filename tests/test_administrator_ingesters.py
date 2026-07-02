import json
from datetime import UTC, datetime

import pytest

from navbridge.administrator.base import NavIngestionError
from navbridge.administrator.csv_ingester import CsvAdministratorIngester
from navbridge.administrator.json_ingester import JsonAdministratorIngester


def test_csv_ingester_handles_optional_fields(tmp_path) -> None:
    path = tmp_path / "nav.csv"
    path.write_text("fund_id,timestamp_utc,nav_per_unit,currency\nFUND_001,2026-01-01T21:00:00Z,1.0,USD\n", encoding="utf-8")
    rows = CsvAdministratorIngester(path, "FUND_001", "USD").get_nav_series(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 2, tzinfo=UTC),
    )
    assert rows[0].metadata["calc_method"] == "unspecified"


def test_json_ingester_currency_mismatch_raises(tmp_path) -> None:
    path = tmp_path / "nav.json"
    path.write_text(json.dumps({"fund_id": "FUND_001", "records": [{"timestamp_utc": "2026-01-01T21:00:00Z", "nav_per_unit": "1.0", "currency": "EUR"}]}), encoding="utf-8")
    with pytest.raises(NavIngestionError):
        JsonAdministratorIngester(path, "FUND_001", "USD").get_nav_series(
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 2, tzinfo=UTC),
        )


def test_csv_ingester_malformed_timestamp_raises(tmp_path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("fund_id,timestamp_utc,nav_per_unit,currency\nFUND_001,not-a-date,1.0,USD\n", encoding="utf-8")
    with pytest.raises(NavIngestionError):
        CsvAdministratorIngester(path).get_nav_series(
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 2, tzinfo=UTC),
        )

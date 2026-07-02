import json
from datetime import UTC, datetime
from decimal import Decimal

from navbridge.cli import main
from navbridge.core.fund import FundConfig
from navbridge.core.nav_record import NavRecord
from navbridge.validation.contracts import validate_administrator_file, validate_nav_records


def _config() -> FundConfig:
    return FundConfig.from_dict(
        {
            "fund_id": "FUND_001",
            "fund_type": "money_market",
            "base_currency": "USD",
            "nav_frequency": "daily",
            "market_timezone": "America/New_York",
            "market_open": "09:30",
            "market_close": "16:00",
        }
    )


def test_validate_administrator_file_passes_valid_csv(tmp_path) -> None:
    path = tmp_path / "nav.csv"
    path.write_text(
        "fund_id,timestamp_utc,nav_per_unit,currency\n"
        "FUND_001,2026-01-01T21:00:00Z,1.0,USD\n",
        encoding="utf-8",
    )
    result = validate_administrator_file(
        path,
        _config(),
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 2, tzinfo=UTC),
    )
    assert result.valid is True
    assert result.records_checked == 1
    assert result.issues == []


def test_validate_administrator_file_returns_ingestion_error(tmp_path) -> None:
    path = tmp_path / "nav.csv"
    path.write_text(
        "fund_id,timestamp_utc,nav_per_unit,currency\n"
        "OTHER,2026-01-01T21:00:00Z,1.0,USD\n",
        encoding="utf-8",
    )
    result = validate_administrator_file(
        path,
        _config(),
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 2, tzinfo=UTC),
    )
    assert result.valid is False
    assert result.issues[0].code == "ingestion_error"


def test_validate_nav_records_detects_duplicate_and_non_positive_nav() -> None:
    timestamp = datetime(2026, 1, 1, 21, tzinfo=UTC)
    records = [
        NavRecord("FUND_001", "administrator", timestamp, Decimal("1.0"), "USD", {}),
        NavRecord("FUND_001", "administrator", timestamp, Decimal("0"), "USD", {}),
    ]
    result = validate_nav_records(
        records,
        expected_source="administrator",
        expected_fund_id="FUND_001",
        expected_currency="USD",
    )
    assert result.valid is False
    assert {issue.code for issue in result.issues} == {"duplicate_timestamp", "non_positive_nav"}


def test_validate_nav_records_can_allow_zero_oracle_nav() -> None:
    timestamp = datetime(2026, 1, 1, 21, tzinfo=UTC)
    records = [
        NavRecord("FUND_001", "oracle", timestamp, Decimal("0"), "USD", {}),
    ]
    result = validate_nav_records(
        records,
        expected_source="oracle",
        expected_fund_id="FUND_001",
        expected_currency="USD",
        allow_zero_nav=True,
    )
    assert result.valid is True


def test_validate_admin_file_cli_json_output(tmp_path, capsys) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(_config().to_dict()), encoding="utf-8")
    admin_path = tmp_path / "nav.csv"
    admin_path.write_text(
        "fund_id,timestamp_utc,nav_per_unit,currency\n"
        "FUND_001,2026-01-01T21:00:00Z,1.0,USD\n",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate-admin-file",
            "--config",
            str(config_path),
            "--admin-file",
            str(admin_path),
            "--start",
            "2026-01-01",
            "--end",
            "2026-01-02",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["valid"] is True
    assert payload["records_checked"] == 1

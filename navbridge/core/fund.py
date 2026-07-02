from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Any, Literal


FundType = Literal["money_market", "treasury_bond"]
NavFrequency = Literal["daily", "intraday"]


@dataclass(frozen=True)
class FundConfig:
    fund_id: str
    fund_type: FundType
    base_currency: str
    nav_frequency: NavFrequency
    market_timezone: str
    market_open: time
    market_close: time
    tolerance_bps: float = 2.0
    materiality_bps: float = 5.0
    oracle_update_frequency_minutes: int = 60
    alignment_window_minutes: int = 30

    def __post_init__(self) -> None:
        if not self.fund_id:
            raise ValueError("fund_id is required")
        if self.fund_type not in {"money_market", "treasury_bond"}:
            raise ValueError("fund_type must be money_market or treasury_bond")
        if self.nav_frequency not in {"daily", "intraday"}:
            raise ValueError("nav_frequency must be daily or intraday")
        if len(self.base_currency) != 3:
            raise ValueError("base_currency must be an ISO 4217 code")
        if self.tolerance_bps < 0 or self.materiality_bps < 0:
            raise ValueError("tolerance_bps and materiality_bps must be non-negative")
        if self.materiality_bps < self.tolerance_bps:
            raise ValueError("materiality_bps must be greater than or equal to tolerance_bps")
        if self.oracle_update_frequency_minutes <= 0:
            raise ValueError("oracle_update_frequency_minutes must be positive")
        if self.alignment_window_minutes <= 0:
            raise ValueError("alignment_window_minutes must be positive")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "FundConfig":
        data = dict(payload)
        data["market_open"] = _parse_time(data["market_open"])
        data["market_close"] = _parse_time(data["market_close"])
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fund_id": self.fund_id,
            "fund_type": self.fund_type,
            "base_currency": self.base_currency,
            "nav_frequency": self.nav_frequency,
            "market_timezone": self.market_timezone,
            "market_open": self.market_open.isoformat(timespec="minutes"),
            "market_close": self.market_close.isoformat(timespec="minutes"),
            "tolerance_bps": self.tolerance_bps,
            "materiality_bps": self.materiality_bps,
            "oracle_update_frequency_minutes": self.oracle_update_frequency_minutes,
            "alignment_window_minutes": self.alignment_window_minutes,
        }


def _parse_time(value: time | str) -> time:
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        return time.fromisoformat(value)
    raise ValueError("market time values must be time objects or HH:MM strings")

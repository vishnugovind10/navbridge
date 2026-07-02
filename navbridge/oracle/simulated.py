from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from navbridge.core.fund import FundConfig
from navbridge.core.nav_record import NavRecord
from navbridge.oracle.base import OracleAdapter


@dataclass(frozen=True)
class DriftModel:
    timing_lag_minutes: int
    methodology_spread_bps: float
    overnight_drift_bps_per_hour: float
    corporate_action_delay_hours: float
    random_noise_bps: float
    feed_failure_start: datetime | None = None
    feed_failure_duration_hours: float = 0.0

    @classmethod
    def from_dict(cls, payload: dict) -> "DriftModel":
        data = dict(payload)
        if data.get("feed_failure_start"):
            data["feed_failure_start"] = _parse_utc_datetime(data["feed_failure_start"])
        return cls(**data)


DRIFT_PRESETS: dict[str, DriftModel] = {
    "BUIDL_STYLE": DriftModel(
        timing_lag_minutes=45,
        methodology_spread_bps=0.3,
        overnight_drift_bps_per_hour=0.05,
        corporate_action_delay_hours=0,
        random_noise_bps=0.03,
    ),
    "ONDO_STYLE": DriftModel(
        timing_lag_minutes=60,
        methodology_spread_bps=1.4,
        overnight_drift_bps_per_hour=0.12,
        corporate_action_delay_hours=6,
        random_noise_bps=0.05,
    ),
    "MARKET_HOURS_STRESS": DriftModel(
        timing_lag_minutes=120,
        methodology_spread_bps=0.4,
        overnight_drift_bps_per_hour=0.25,
        corporate_action_delay_hours=12,
        random_noise_bps=0.02,
        feed_failure_start=datetime(2026, 1, 8, 14, 0, tzinfo=UTC),
        feed_failure_duration_hours=4,
    ),
}


class SimulatedOracle(OracleAdapter):
    def __init__(
        self,
        config: FundConfig,
        base_nav: Decimal,
        update_frequency_minutes: int,
        drift_model: DriftModel,
        seed: int | None = None,
    ) -> None:
        self.config = config
        self.base_nav = base_nav
        self.update_frequency_minutes = update_frequency_minutes
        self.drift_model = drift_model
        self.random = random.Random(seed)
        self._last_good_nav: Decimal | None = None

    def get_nav_series(self, start: datetime, end: datetime) -> list[NavRecord]:
        start = start.astimezone(UTC)
        end = end.astimezone(UTC)
        current = start
        records: list[NavRecord] = []
        while current <= end:
            records.append(self._record_at(current, start))
            current += timedelta(minutes=self.update_frequency_minutes)
        return records

    def _record_at(self, timestamp: datetime, start: datetime) -> NavRecord:
        metadata = {
            "simulated": True,
            "drift_model": _model_name(self.drift_model),
            "timing_lag_minutes": self.drift_model.timing_lag_minutes,
            "update_frequency_minutes": self.update_frequency_minutes,
        }
        true_nav = self._administrator_like_nav(timestamp, start)
        bps = self._drift_bps(timestamp)
        if self._inside_feed_failure(timestamp):
            nav = self._last_good_nav or true_nav
            metadata["stale_duration_minutes"] = int(
                (timestamp - self.drift_model.feed_failure_start).total_seconds() // 60
            )
        else:
            nav = true_nav * (Decimal("1") + Decimal(str(bps)) / Decimal("10000"))
            self._last_good_nav = nav

        if self._inside_corporate_action_delay(timestamp, start):
            metadata["corporate_action_delay"] = True

        return NavRecord(
            fund_id=self.config.fund_id,
            source="oracle",
            timestamp=timestamp,
            nav_per_unit=nav.quantize(Decimal("0.000001")),
            currency=self.config.base_currency,
            metadata=metadata,
        )

    def _administrator_like_nav(self, timestamp: datetime, start: datetime) -> Decimal:
        day_index = max(0, (timestamp.date() - start.date()).days)
        daily_yield_bps = Decimal("0.35") if self.config.fund_type == "money_market" else Decimal("0.55")
        nav = self.base_nav * (Decimal("1") + (daily_yield_bps * day_index / Decimal("10000")))
        action_day = start.date() + timedelta(days=14)
        if self.config.fund_type == "treasury_bond" and timestamp.date() >= action_day:
            nav *= Decimal("1.0008")
        return nav

    def _drift_bps(self, timestamp: datetime) -> float:
        bps = self.drift_model.methodology_spread_bps
        if not _is_market_open(self.config, timestamp):
            bps += _hours_since_market_close(self.config, timestamp) * self.drift_model.overnight_drift_bps_per_hour
        bps += self.random.uniform(-self.drift_model.random_noise_bps, self.drift_model.random_noise_bps)
        return bps

    def _inside_corporate_action_delay(self, timestamp: datetime, start: datetime) -> bool:
        if self.drift_model.corporate_action_delay_hours <= 0:
            return False
        action_start = datetime.combine(start.date() + timedelta(days=14), self.config.market_close, tzinfo=ZoneInfo(self.config.market_timezone)).astimezone(UTC)
        action_end = action_start + timedelta(hours=self.drift_model.corporate_action_delay_hours)
        return action_start <= timestamp <= action_end

    def _inside_feed_failure(self, timestamp: datetime) -> bool:
        if not self.drift_model.feed_failure_start or self.drift_model.feed_failure_duration_hours <= 0:
            return False
        failure_end = self.drift_model.feed_failure_start + timedelta(hours=self.drift_model.feed_failure_duration_hours)
        return self.drift_model.feed_failure_start <= timestamp <= failure_end


def get_drift_model(name_or_path: str) -> DriftModel:
    if name_or_path in DRIFT_PRESETS:
        return DRIFT_PRESETS[name_or_path]
    path = Path(name_or_path)
    if not path.exists():
        raise ValueError(f"Unknown drift model preset or file: {name_or_path}")
    return DriftModel.from_dict(json.loads(path.read_text(encoding="utf-8")))


def _is_market_open(config: FundConfig, timestamp: datetime) -> bool:
    local = timestamp.astimezone(ZoneInfo(config.market_timezone))
    if local.weekday() >= 5:
        return False
    return config.market_open <= local.time() <= config.market_close


def _hours_since_market_close(config: FundConfig, timestamp: datetime) -> float:
    local = timestamp.astimezone(ZoneInfo(config.market_timezone))
    close_today = datetime.combine(local.date(), config.market_close, tzinfo=ZoneInfo(config.market_timezone))
    if local.time() >= config.market_close and local.weekday() < 5:
        delta = local - close_today
    else:
        previous = close_today - timedelta(days=1)
        while previous.weekday() >= 5:
            previous -= timedelta(days=1)
        delta = local - previous
    return max(0.0, delta.total_seconds() / 3600)


def _parse_utc_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _model_name(model: DriftModel) -> str:
    for name, preset in DRIFT_PRESETS.items():
        if model == preset:
            return name
    return "CUSTOM"

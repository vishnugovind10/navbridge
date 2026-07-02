from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal


NavSource = Literal["oracle", "administrator"]


@dataclass(frozen=True)
class NavRecord:
    fund_id: str
    source: NavSource
    timestamp: datetime
    nav_per_unit: Decimal
    currency: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.source not in {"oracle", "administrator"}:
            raise ValueError("source must be oracle or administrator")
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware UTC")
        if self.timestamp.utcoffset() != datetime.now(UTC).utcoffset():
            raise ValueError("timestamp must be UTC")
        if self.nav_per_unit < 0:
            raise ValueError("nav_per_unit cannot be negative")
        if len(self.currency) != 3:
            raise ValueError("currency must be an ISO 4217 code")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "NavRecord":
        return cls(
            fund_id=payload["fund_id"],
            source=payload["source"],
            timestamp=parse_utc_datetime(payload["timestamp"]),
            nav_per_unit=Decimal(str(payload["nav_per_unit"])),
            currency=payload["currency"],
            metadata=dict(payload.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "fund_id": self.fund_id,
            "source": self.source,
            "timestamp": format_utc_datetime(self.timestamp),
            "nav_per_unit": str(self.nav_per_unit),
            "currency": self.currency,
            "metadata": self.metadata,
        }


def parse_utc_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    parsed = parsed.astimezone(UTC)
    return parsed


def format_utc_datetime(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")

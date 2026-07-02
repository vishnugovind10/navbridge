from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from navbridge.core.fund import FundConfig


@dataclass(frozen=True)
class PolicyPack:
    id: str
    version: str
    name: str
    thresholds: dict[str, float]
    escalation: dict[str, str] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("policy pack id is required")
        if not self.version:
            raise ValueError("policy pack version is required")
        if "tolerance_bps" not in self.thresholds:
            raise ValueError("policy pack thresholds.tolerance_bps is required")
        if "materiality_bps" not in self.thresholds:
            raise ValueError("policy pack thresholds.materiality_bps is required")
        tolerance = float(self.thresholds["tolerance_bps"])
        materiality = float(self.thresholds["materiality_bps"])
        if tolerance < 0 or materiality < 0:
            raise ValueError("policy pack thresholds must be non-negative")
        if materiality < tolerance:
            raise ValueError("policy pack materiality_bps must be >= tolerance_bps")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PolicyPack":
        return cls(
            id=payload["id"],
            version=str(payload["version"]),
            name=payload.get("name") or payload["id"],
            thresholds={key: float(value) for key, value in payload.get("thresholds", {}).items()},
            escalation=dict(payload.get("escalation", {})),
            evidence=dict(payload.get("evidence", {})),
            metadata=dict(payload.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "name": self.name,
            "thresholds": self.thresholds,
            "escalation": self.escalation,
            "evidence": self.evidence,
            "metadata": self.metadata,
        }


def load_policy_pack(value: str | Path | dict[str, Any] | None, *, base_dir: str | Path | None = None) -> PolicyPack | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return PolicyPack.from_dict(value)
    path = Path(value)
    if not path.is_absolute() and base_dir is not None:
        path = Path(base_dir) / path
    if path.suffix.lower() != ".json":
        raise ValueError("policy pack files must be JSON in V1")
    return PolicyPack.from_dict(json.loads(path.read_text(encoding="utf-8")))


def apply_policy_pack(config: FundConfig, policy_pack: PolicyPack | None) -> FundConfig:
    if policy_pack is None:
        return config
    data = config.to_dict()
    data["tolerance_bps"] = float(policy_pack.thresholds["tolerance_bps"])
    data["materiality_bps"] = float(policy_pack.thresholds["materiality_bps"])
    data["policy"] = policy_pack.to_dict()
    return FundConfig.from_dict(data)

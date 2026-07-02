from __future__ import annotations

from navbridge.core.divergence import DivergenceEvent


def recommend_tolerance_bps(events: list[DivergenceEvent]) -> float | None:
    values = sorted(abs(event.divergence_bps) for event in events if abs(event.divergence_bps) > 0)
    if not values:
        return None
    index = min(len(values) - 1, round((len(values) - 1) * 0.97))
    return round(values[index], 2)

from __future__ import annotations

import json
from pathlib import Path

from navbridge.core.report import DivergenceReport


def report_to_json(report: DivergenceReport) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=True)


def write_json_report(report: DivergenceReport, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report_to_json(report) + "\n", encoding="utf-8")

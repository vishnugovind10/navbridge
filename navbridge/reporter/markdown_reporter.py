from __future__ import annotations

from pathlib import Path

from navbridge.core.nav_record import format_utc_datetime
from navbridge.core.report import DivergenceReport


def report_to_markdown(report: DivergenceReport) -> str:
    lines = [
        "# NavBridge Divergence Report",
        f"**Schema:** {report.schema_version}",
        f"**Run ID:** {report.run_id or 'not recorded'}",
        f"**Fund:** {report.fund_id}",
        f"**Window:** {format_utc_datetime(report.report_window_start)} to {format_utc_datetime(report.report_window_end)}",
        f"**Generated:** {format_utc_datetime(report.generated_at) if report.generated_at else 'not recorded'}",
        "",
        "## Summary",
        "| Metric | Value |",
        "|---|---|",
        f"| Total NAV observations | {report.total_observations} |",
        f"| Oracle records read | {report.input_record_counts.get('oracle', 0)} |",
        f"| Administrator records read | {report.input_record_counts.get('administrator', 0)} |",
        f"| Total divergence events | {report.total_breaks} |",
        f"| Material breaks | {report.material_breaks} |",
        f"| Critical breaks | {report.critical_breaks} |",
        f"| Mean divergence | {report.mean_divergence_bps:.2f} bps |",
        f"| Max divergence | {report.max_divergence_bps:.2f} bps |",
        f"| Policy compliance | {'Yes' if report.policy_compliance else 'No'} |",
        "",
        "## Break Distribution",
        "| Break Type | Count | % of breaks |",
        "|---|---:|---:|",
    ]
    total_classified = sum(report.break_type_distribution.values())
    if total_classified == 0:
        lines.append("| None | 0 | 0% |")
    else:
        for break_type, count in sorted(report.break_type_distribution.items(), key=lambda item: item[0].value):
            pct = count / total_classified * 100
            lines.append(f"| {break_type.value.replace('_', ' ').title()} | {count} | {pct:.0f}% |")

    lines.extend([
        "",
        "## Material Breaks",
        "| Timestamp | Divergence (bps) | Type | Severity | Notes |",
        "|---|---:|---|---|---|",
    ])
    material = [event for event in report.events if event.severity in {"material", "critical"}]
    if not material:
        lines.append("| None | 0.00 | - | - | No material breaks detected. |")
    else:
        for event in material:
            lines.append(
                "| "
                f"{format_utc_datetime(event.administrator_record.timestamp)} | "
                f"{event.divergence_bps:.2f} | "
                f"{event.break_type.value if event.break_type else 'unclassified'} | "
                f"{event.severity} | "
                f"{event.notes} |"
            )

    if report.recommended_tolerance_bps is not None:
        lines.extend([
            "",
            "## Policy Advisor Recommendation",
            (
                "Based on the observed break distribution, a tolerance policy of "
                f"**{report.recommended_tolerance_bps:.2f} bps** would classify most routine breaks "
                "as within tolerance while preserving material-review escalation."
            ),
        ])
    return "\n".join(lines) + "\n"


def write_markdown_report(report: DivergenceReport, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report_to_markdown(report), encoding="utf-8")

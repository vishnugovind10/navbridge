# Internal Adoption Guide

This guide is for teams evaluating whether NavBridge can be adapted inside an institution.

## Recommended First Integration

1. Keep `core`, `classifier`, `monitor`, and `reporter` unchanged.
2. Write one internal `AdministratorAdapter` that maps the fund administrator's daily NAV file or API output to `NavRecord`.
3. Write one internal `OracleAdapter` that maps the approved oracle feed to `NavRecord`.
4. Validate administrator records with `navbridge validate-admin-file` or `validate_nav_records()`.
5. Run `navbridge batch` for a historical period and compare output against existing reconciliation breaks.
6. Write an audit manifest with `--audit-manifest` and store it with JSON and Markdown reports.

## Internal Extension Points

- Administrator source: replace `CsvAdministratorIngester` or `JsonAdministratorIngester`.
- Oracle source: replace `SimulatedOracle`.
- Policy: adjust `FundConfig` thresholds per fund.
- Reporting: keep JSON schema stable and add downstream dashboards outside the core package.

## Controls to Review Before Production

- Timestamp conventions across oracle, administrator, and market close.
- Currency and fund-ID mapping.
- Corporate-action event source.
- Stale oracle detection interval.
- Report retention and reviewer sign-off.
- Change-control process for classifier rules.
- JSON schema compatibility for downstream systems.
- Batch performance over expected fund and observation volumes.
- Evidence-retention location for JSON reports, Markdown reports, and audit manifests.
- Batch summary ingestion for operational dashboards or workflow queues.

## Suggested Operating Model

Run NavBridge as a deterministic batch job after administrator NAV publication. Treat generated JSON as machine-readable evidence and Markdown as the reviewer packet. Escalate `material` and `critical` events into the institution's existing operational-risk workflow.

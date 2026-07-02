# Changelog

## 0.4.0 - Classification Audit Trail

- Added stable classifier rule IDs, ruleset version, and per-event classification evidence.
- Extended JSON report schema documentation for classification audit fields.
- Updated classification, controls, and model-risk docs.
- Added tests for classifier rule metadata and report schema output.

## 0.3.0 - Validation and Conformance Surface

- Added `navbridge.validation` for pre-run adapter and administrator-file validation.
- Added `navbridge validate-admin-file` with text and JSON output.
- Added validation documentation for internal integration teams.
- Added tests for validation API and CLI behavior.

## 0.2.0 - Institutional Contract Hardening

- Added versioned JSON report metadata: `schema_version`, `run_id`, input counts, monitor parameters, and config snapshot.
- Added `docs/report_schema_v1.json`.
- Added adapter contract enforcement in `MonitorEngine`.
- Added indexed nearest-timestamp oracle alignment.
- Added CI workflow, security policy, controls matrix, internal adoption guide, and model-risk guidance.
- Added tests for report schema fields and adapter contract failures.

## 0.1.0 - Initial Framework

- Added core domain models, simulated oracle, administrator ingesters, classifier, monitor engine, reporters, CLI, examples, and tests.

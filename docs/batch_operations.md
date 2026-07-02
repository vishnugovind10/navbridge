# Batch Operations

Institutional users typically run NAV integrity checks across a portfolio of funds or share classes after administrator NAV publication. `navbridge batch` provides a file-based orchestration layer without introducing a database or service runtime.

## Batch File

```json
{
  "jobs": [
    {
      "name": "mmf_january",
      "config": "mmf_scenario/config.json",
      "admin_file": "mmf_scenario/administrator_nav.csv",
      "oracle": "simulated",
      "drift_model": "BUIDL_STYLE",
      "start": "2026-01-01",
      "end": "2026-01-31",
      "output_json": "../reports/batch_mmf_january.json",
      "output_md": "../reports/batch_mmf_january.md",
      "audit_manifest": "../reports/batch_mmf_january.audit.json",
      "advise_policy": true
    }
  ]
}
```

Relative paths are resolved against the batch file location.

## Run

```powershell
navbridge batch `
  --file examples/batch_portfolio.json `
  --summary-json reports/batch_summary.json
```

The command prints the summary JSON and writes it to `--summary-json` when provided. Exit code is `0` only when every job succeeds.

## Summary Contract

The batch result uses `schema_version="navbridge.batch_result.v1"` and records:

- total jobs
- succeeded and failed counts
- per-job status
- fund ID and report run ID for successful jobs
- output report and audit manifest paths
- material/critical break counts
- policy-compliance status
- error message for failed jobs

Batch mode intentionally reuses the single-run monitor path, including JSON/Markdown output, audit manifests, validation behavior, classifier metadata, and report schema.

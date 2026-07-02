# Evidence Retention

NavBridge can write an audit manifest for monitor runs. The manifest links the input files, output reports, package version, run ID, and high-level report summary using SHA256 fingerprints.

## CLI

```powershell
navbridge monitor `
  --config examples/mmf_scenario/config.json `
  --oracle simulated `
  --drift-model BUIDL_STYLE `
  --admin-file examples/mmf_scenario/administrator_nav.csv `
  --start 2026-01-01 `
  --end 2026-01-31 `
  --output-json reports/mmf_january.json `
  --output-md reports/mmf_january.md `
  --audit-manifest reports/mmf_january.audit.json `
  --advise-policy
```

`--audit-manifest` requires at least one persisted report output. A manifest over stdout-only output is rejected because there is no report file to fingerprint.

## Manifest Contents

- `schema_version`: currently `navbridge.audit_manifest.v1`.
- `navbridge_version`: installed package version.
- `report_run_id`: deterministic report run identifier.
- `input_files`: config and administrator NAV file hashes.
- `output_files`: JSON and Markdown report hashes.
- `report_summary`: observation counts, break counts, and policy-compliance status.
- `command`: monitor parameters used for the run.

The manifest is not a signature and does not replace a controlled document store. It is a reproducibility and evidence-retention artifact that downstream governance systems can ingest.

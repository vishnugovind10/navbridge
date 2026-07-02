# Data Validation

Institutional integrations should validate administrator NAV input before running a monitor report. This catches schema, identity, currency, duplicate timestamp, and empty-window issues at the source boundary.

## CLI

```powershell
navbridge validate-admin-file `
  --config examples/mmf_scenario/config.json `
  --admin-file examples/mmf_scenario/administrator_nav.csv `
  --start 2026-01-01 `
  --end 2026-01-31
```

Machine-readable output:

```powershell
navbridge validate-admin-file `
  --config examples/mmf_scenario/config.json `
  --admin-file examples/mmf_scenario/administrator_nav.csv `
  --start 2026-01-01 `
  --end 2026-01-31 `
  --json
```

The command exits `0` when validation passes and `1` when any error-level issue is found.

## Python API

```python
from navbridge.validation import validate_administrator_file

result = validate_administrator_file(path, config, start, end)
if not result.valid:
    for issue in result.issues:
        print(issue.code, issue.message)
```

## Checks

- File parses through the selected ingester.
- At least one record exists in the requested window.
- `source`, `fund_id`, and `currency` match the expected run configuration.
- NAV values are positive.
- Oracle adapter validation can allow zero NAV where the monitor is expected to classify it as `data_feed_failure`.
- Duplicate timestamps are rejected.
- Non-monotonic timestamps are flagged as warnings.

Validation is not a substitute for source-system reconciliation. It is a boundary check that prevents malformed input from being misread as ordinary NAV divergence.

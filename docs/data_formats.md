# Data Formats

NavBridge V1 ingests administrator NAV files in a small CSV or JSON schema. Real fund administrator exports usually need a one-time transformation before they can be loaded.

## CSV

```csv
fund_id,timestamp_utc,nav_per_unit,currency,calc_method,source_file
FUND_001,2026-01-15T21:00:00Z,1.002341,USD,evaluated_bid,nav_20260115.csv
```

Required fields:

- `fund_id`
- `timestamp_utc`
- `nav_per_unit`
- `currency`

Optional fields:

- `calc_method`
- `source_file`

## JSON

```json
{
  "fund_id": "FUND_001",
  "records": [
    {
      "timestamp_utc": "2026-01-15T21:00:00Z",
      "nav_per_unit": "1.002341",
      "currency": "USD",
      "calc_method": "evaluated_bid"
    }
  ]
}
```

All timestamps are UTC. `nav_per_unit` is parsed as a decimal string to avoid binary floating-point ingestion drift.

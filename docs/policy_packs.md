# Policy Packs

Policy Packs turn NavBridge from a monitor into a policy execution layer. A policy pack is a versioned JSON artifact that defines thresholds, escalation expectations, and evidence requirements for a class of fund.

## Example

```json
{
  "id": "tokenized_mmf_v1",
  "version": "1.0",
  "name": "Institutional Tokenized MMF Policy",
  "thresholds": {
    "tolerance_bps": 3.0,
    "materiality_bps": 5.0
  },
  "escalation": {
    "critical": "immediate",
    "material": "next_business_day"
  },
  "evidence": {
    "require_audit_manifest": true
  }
}
```

## CLI

```powershell
navbridge monitor `
  --config examples/mmf_scenario/config.json `
  --policy-pack policies/tokenized_mmf_v1.json `
  --admin-file examples/mmf_scenario/administrator_nav.csv `
  --start 2026-01-01 `
  --end 2026-01-31 `
  --output-json reports/mmf_policy.json `
  --output-md reports/mmf_policy.md `
  --audit-manifest reports/mmf_policy.audit.json `
  --advise-policy
```

If `evidence.require_audit_manifest` is true, NavBridge rejects the run unless `--audit-manifest` is supplied.

## Inline Policy

Fund configs may also include a `policy` object. A CLI `--policy-pack` file takes precedence over an inline policy object.

## Report Output

Reports include the applied policy under `policy_pack`, and Markdown reports show:

```markdown
**Policy Pack:** Institutional Tokenized MMF Policy v1.0
```

Audit manifests include the policy pack file hash when a file-based policy is used.

## Scope

Policy Packs do not calculate legal NAV or approve exceptions. They bind monitoring behavior to named institutional thresholds, escalation expectations, and evidence requirements.

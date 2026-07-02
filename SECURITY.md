# Security Policy

NavBridge V1 is a local library and CLI. It does not run a server, hold credentials, or make live network calls.

## Supported Versions

Only the `main` branch is currently supported.

## Reporting a Vulnerability

Open a private security advisory on GitHub or contact the repository owner. Do not disclose exploitable issues publicly before maintainers have had a chance to review.

## Security Boundaries

- Administrator files are treated as untrusted input and parsed through typed ingesters.
- Report output is local file output only.
- V1 oracle data is simulated; live oracle adapters should not perform network calls at import time.
- No secrets should be stored in configs, examples, reports, or adapter metadata.

## Production Review Checklist

- Validate administrator-file transforms before ingestion.
- Pin package versions in downstream deployments.
- Store generated reports in the institution's normal evidence-retention system.
- Review adapter code before enabling live network access.
- Treat policy-advisor output as a decision-support signal, not an automated control approval.

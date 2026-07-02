import json
from pathlib import Path

from navbridge.batch.runner import BATCH_RESULT_SCHEMA_VERSION, run_batch_file, write_batch_result
from navbridge.cli import main


def test_batch_cli_runs_multiple_jobs(tmp_path) -> None:
    root = Path(__file__).resolve().parents[1]
    batch = tmp_path / "batch.json"
    out_dir = tmp_path / "out"
    batch.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "name": "mmf",
                        "config": str(root / "examples" / "mmf_scenario" / "config.json"),
                        "admin_file": str(root / "examples" / "mmf_scenario" / "administrator_nav.csv"),
                        "oracle": "simulated",
                        "drift_model": "BUIDL_STYLE",
                        "start": "2026-01-01",
                        "end": "2026-01-31",
                        "output_json": str(out_dir / "mmf.json"),
                        "output_md": str(out_dir / "mmf.md"),
                        "audit_manifest": str(out_dir / "mmf.audit.json"),
                        "advise_policy": True,
                    },
                    {
                        "name": "stress",
                        "config": str(root / "examples" / "market_hours_scenario" / "config.json"),
                        "admin_file": str(root / "examples" / "market_hours_scenario" / "administrator_nav.csv"),
                        "oracle": "simulated",
                        "drift_model": "MARKET_HOURS_STRESS",
                        "start": "2026-01-01",
                        "end": "2026-01-09",
                        "output_json": str(out_dir / "stress.json"),
                        "output_md": str(out_dir / "stress.md"),
                        "audit_manifest": str(out_dir / "stress.audit.json"),
                        "advise_policy": True,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    summary = tmp_path / "summary.json"
    assert main(["batch", "--file", str(batch), "--summary-json", str(summary)]) == 0
    payload = json.loads(summary.read_text(encoding="utf-8"))
    assert payload["schema_version"] == BATCH_RESULT_SCHEMA_VERSION
    assert payload["total_jobs"] == 2
    assert payload["succeeded"] == 2
    assert (out_dir / "mmf.audit.json").exists()
    assert (out_dir / "stress.audit.json").exists()


def test_batch_result_records_failed_jobs(tmp_path) -> None:
    batch = tmp_path / "batch.json"
    batch.write_text(json.dumps({"jobs": [{"name": "bad", "config": "missing.json"}]}), encoding="utf-8")
    result = run_batch_file(batch, lambda job: (_ for _ in ()).throw(RuntimeError("bad job")))
    assert result.failed == 1
    assert result.jobs[0].status == "failed"
    assert result.jobs[0].error == "bad job"

    output = tmp_path / "summary.json"
    write_batch_result(result, output)
    assert json.loads(output.read_text(encoding="utf-8"))["failed"] == 1

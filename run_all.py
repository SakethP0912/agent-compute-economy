#!/usr/bin/env python3
"""One-command clean replay. No credentials, network, or third-party packages."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "replay")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("Choose an empty output directory to avoid replacing evidence")
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    commands = [
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        [sys.executable, "-m", "unittest", "discover", "-s", "real_workload", "-p", "test_*.py", "-v"],
        *[[sys.executable, "-m", "economy.experiment", stage, "--output", str(output)]
          for stage in ("develop", "freeze", "evaluate")],
        [sys.executable, "-m", "economy.analyze", "--results", str(output)],
        [sys.executable, "real_workload/benchmark.py", "--output", str(output / "real_workload")],
        [sys.executable, "real_workload/confirmatory.py", "--output", str(output / "confirmatory")],
        [sys.executable, "sensitivity/run_sensitivity.py", "--output", str(output / "sensitivity")],
    ]
    for command in commands:
        print("Running:", " ".join(command), flush=True)
        subprocess.run(command, cwd=ROOT, check=True)
    comparisons = [(ROOT / "results/evaluation.csv", output / "evaluation.csv"),
                   (ROOT / "real_workload/results/runs.csv", output / "real_workload/runs.csv"),
                   (ROOT / "real_workload/confirmatory_results/runs.csv", output / "confirmatory/runs.csv"),
                   (ROOT / "sensitivity/results/runs.csv", output / "sensitivity/runs.csv")]
    replay_checks = {}
    for original, replay in comparisons:
        if original.exists():
            same = original.read_bytes() == replay.read_bytes()
            replay_checks[str(original.relative_to(ROOT))] = same
            if not same:
                raise AssertionError(f"Substantive replay differs from retained evidence: {original}")
    files = [p for p in output.rglob("*") if p.is_file()]
    manifest = dict(python=sys.version, platform=platform.platform(),
                    elapsed_seconds=time.perf_counter()-started,
                    commands=commands,
                    retained_raw_evidence_matches=replay_checks,
                    sha256={str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    (output / "replay_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print("Replay complete:", output)


if __name__ == "__main__":
    main()

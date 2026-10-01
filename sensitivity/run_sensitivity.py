#!/usr/bin/env python3
"""Fresh-seed exploratory equal-controller-cost sensitivity; frozen code unchanged."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import statistics
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from economy.policies import make_policy as frozen_make_policy
from economy.simulator import SCENARIOS, World, run

POLICIES = ("ucb", "salary", "salary_milestones", "revised")
SEEDS = tuple(range(20000, 20100))
CONTROLLER_FEE = .04
RESAMPLES = 2000
BOOTSTRAP_SEED = 734922


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_manifest():
    path = ROOT / "results/frozen_config.json"
    if sha(path) != (ROOT / "results/frozen_config.sha256").read_text().strip():
        raise ValueError("Frozen configuration checksum mismatch")
    manifest = json.loads(path.read_text())
    for name, expected in manifest["source_hashes"].items():
        if sha(ROOT / name) != expected:
            raise ValueError(f"Frozen source checksum mismatch: {name}")
    for name, expected in manifest["design_hashes"].items():
        if sha(ROOT / name) != expected:
            raise ValueError(f"Frozen design checksum mismatch: {name}")
    if sha(HERE / "PROTOCOL.md") != (HERE / "protocol.sha256").read_text().strip():
        raise ValueError("Sensitivity protocol checksum mismatch")
    if set(SEEDS) & (set(manifest["development_seeds"]) | set(manifest["evaluation_seeds"])):
        raise ValueError("Sensitivity seeds overlap development or original evaluation")
    if [s.__dict__ for s in SCENARIOS] != manifest["scenarios"]:
        raise ValueError("Frozen scenarios differ from implementation")
    return manifest


def equal_fee_policy(config, budget):
    policy = frozen_make_policy(config, budget)
    policy.overhead = CONTROLLER_FEE
    return policy


def percentile(values, q):
    values = sorted(values)
    p = (len(values) - 1) * q
    k = int(p)
    return values[k] + (values[min(k + 1, len(values) - 1)] - values[k]) * (p - k)


def interval(values):
    return [percentile(values, .025), percentile(values, .975)]


def summarize(rows):
    by = {p: {s: [] for s in SEEDS} for p in POLICIES}
    for row in rows:
        by[row["policy"]][row["seed"]].append(row["completed"])
    seed_means = {p: [statistics.fmean(by[p][s]) for s in SEEDS] for p in POLICIES}
    n = len(SEEDS)
    rng = random.Random(BOOTSTRAP_SEED)
    draws = [[rng.randrange(n) for _ in range(n)] for _ in range(RESAMPLES)]
    boot = {p: [statistics.fmean(seed_means[p][i] for i in indices) for indices in draws] for p in POLICIES}
    policies = {}
    for policy in POLICIES:
        subset = [r for r in rows if r["policy"] == policy]
        completed = sum(r["completed"] for r in subset)
        spent = sum(r["spent"] for r in subset)
        policies[policy] = dict(runs=len(subset), mean_completed=statistics.fmean(seed_means[policy]),
                                total_completed=completed, mean_spent=spent/len(subset),
                                cost_per_completion=spent/completed if completed else None)
    comparisons = []
    for policy in POLICIES[1:]:
        tm = policies[policy]["mean_completed"]
        cm = policies["ucb"]["mean_completed"]
        diffs = [t-c for t,c in zip(boot[policy], boot["ucb"])]
        ratios = [t/c-1 for t,c in zip(boot[policy], boot["ucb"]) if c > 0]
        comparisons.append(dict(treatment=policy, control="ucb", status="exploratory accounting sensitivity",
                                mean_difference=tm-cm, difference_ci95=interval(diffs),
                                relative_gain=tm/cm-1 if cm else None,
                                relative_gain_ci95=interval(ratios) if ratios else None,
                                valid_ratio_resamples=len(ratios)))
    return dict(seed_blocks=n, rows=len(rows), policies=policies, comparisons=comparisons)


def report(summary):
    group = summary["groups"]["all"]
    lines = ["# Exploratory equal-controller-cost sensitivity", "",
             "This post-hoc sensitivity uses fresh seeds to test an assumed bookkeeping cost. It does not replace the frozen primary experiment.", "",
             "All four policies pay 0.04 modeled credits per action for controller bookkeeping. All other costs, rules, and frozen configurations remain unchanged.", "",
             "15,600 runs: 100 independent paired seed blocks, 13 scenarios, three budgets, four policies. Intervals use 2,000 paired seed-block resamples. Synthetic credits are not dollars or LLM tokens.", ""]
    for policy, values in group["policies"].items():
        lines.append(f"- {policy}: {values['mean_completed']:.6f} completed tasks/project; {values['cost_per_completion']:.4f} modeled credits/completion.")
    lines += ["", "## Paired comparisons against UCB", ""]
    for c in group["comparisons"]:
        dl, dh = c["difference_ci95"]
        rl, rh = c["relative_gain_ci95"]
        lines.append(f"- {c['treatment']}: {c['mean_difference']:+.6f} tasks/project, 95% interval [{dl:+.6f}, {dh:+.6f}]; relative difference {100*c['relative_gain']:+.3f}%, interval [{100*rl:+.3f}%, {100*rh:+.3f}%].")
    lines += ["", "## Per-budget relative differences", ""]
    for budget in summary["metadata"]["budgets"]:
        group = summary["groups"][f"budget:{budget}"]
        parts = [f"{c['treatment']} {100*c['relative_gain']:+.3f}%" for c in group["comparisons"]]
        lines.append(f"- {budget} credits: " + "; ".join(parts) + ".")
    lines += ["", "## Interpretation limits", "",
              "Controller costs in both the original experiment and this sensitivity are assumptions. Equalizing them tests robustness to that assumption; it does not establish the actual overhead of any implementation. New seeds differ from the original evaluation, so the difference between these two reported effect sizes is not a paired causal estimate of the fee change. The main all-in experiment and this sensitivity must both be retained.", "",
              "All comparisons and subgroup intervals are exploratory, with no family-wise coverage guarantee. The chosen scenario mixture is not a deployment population. A favorable result would not establish LLM performance, market value, or that a currency system is necessary. The shared-progress null has identical completion outcomes across all four policies, as required when controller fees are equal.", "",
              "Full per-scenario estimates and intervals are in summary.json; individual runs are in runs.csv.", "",
              "Reproduce from the project root: `python3 sensitivity/run_sensitivity.py`.", "",
              f"Protocol SHA-256: `{summary['metadata']['protocol_sha256']}`.", "",
              f"Implementation SHA-256: `{summary['metadata']['implementation_sha256']}`.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "results")
    args = parser.parse_args()
    manifest = checked_manifest()
    snapshots = {str(p.relative_to(ROOT)): sha(p) for p in [ROOT/"results/evaluation.csv", ROOT/"results/analysis.json", ROOT/"results/frozen_config.json"]}
    configs = [next(c for c in manifest["configs"] if c["name"] == p) for p in POLICIES]
    rows = []
    start = time.monotonic()
    with patch("economy.policies.make_policy", side_effect=equal_fee_policy):
        for scenario in SCENARIOS:
            for seed in SEEDS:
                world = World.make(seed, scenario)
                for budget in manifest["budgets"]:
                    for config in configs:
                        row = run(world, budget, config)
                        if abs(row["spent"] + row["unused"] - row["budget"]) > 1e-7:
                            raise AssertionError("Budget conservation failed")
                        rows.append(row)
            print(f"Completed {scenario.name}", flush=True)
    null = {}
    for row in rows:
        if row["scenario"] == "shared_progress_null":
            null.setdefault((row["seed"], row["budget"]), set()).add(row["completed"])
    if not all(len(values) == 1 for values in null.values()):
        raise AssertionError("Equal-cost shared-progress null differs by policy")
    groups = {"all": summarize(rows)}
    for budget in manifest["budgets"]:
        groups[f"budget:{budget}"] = summarize([r for r in rows if r["budget"] == budget])
    for scenario in SCENARIOS:
        groups[f"scenario:{scenario.name}"] = summarize([r for r in rows if r["scenario"] == scenario.name])
    summary = dict(metadata=dict(status="post-hoc fresh-seed exploratory sensitivity", total_runs=len(rows),
                                independent_seed_blocks=len(SEEDS), seeds=SEEDS, budgets=manifest["budgets"],
                                controller_fee=CONTROLLER_FEE, bootstrap_seed=BOOTSTRAP_SEED,
                                bootstrap_resamples=RESAMPLES, configs=configs, original_manifest_sha256=sha(ROOT/"results/frozen_config.json"),
                                original_source_hashes=manifest["source_hashes"], protocol_sha256=sha(HERE/"PROTOCOL.md"),
                                implementation_sha256=sha(Path(__file__)), primary_outputs_before=snapshots,
                                null_identical=True, elapsed_seconds=round(time.monotonic()-start, 3)), groups=groups)
    checked_manifest()
    for name, expected in snapshots.items():
        if sha(ROOT/name) != expected:
            raise AssertionError(f"Primary output changed during sensitivity: {name}")
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    with (output/"runs.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output/"summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True)+"\n")
    (output/"RESULTS.md").write_text(report(summary))
    print(json.dumps(groups["all"], indent=2), flush=True)


if __name__ == "__main__":
    main()

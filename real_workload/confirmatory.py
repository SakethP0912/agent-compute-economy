#!/usr/bin/env python3
"""Prospectively registered fresh-seed follow-up; no policy tuning or LLM calls."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import statistics
import time

import benchmark as b

ROOT = Path(__file__).resolve().parent
FROZEN_BENCHMARK_SHA256 = "e46835736fe3f16f374862266706ca7e1c19efdba6ce4ec13b4e3897e358450a"
SEEDS = tuple(range(10000, 10100))
BUDGETS = (40000, 120000, 240000)
CELLS = frozenset((family, budget) for family in b.FAMILIES for budget in BUDGETS)
PRIMARY_CONTROL = "explore_commit"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def integrity():
    if sha256(ROOT / "benchmark.py") != FROZEN_BENCHMARK_SHA256:
        raise RuntimeError("Frozen benchmark source changed; do not silently alter confirmatory methods")
    digest = sha256(ROOT / "CONFIRMATORY_PROTOCOL.md")
    if digest != (ROOT / "confirmatory_protocol.sha256").read_text().split()[0]:
        raise RuntimeError("Confirmatory protocol hash mismatch")
    return digest


def paired_clusters(rows, control, expected_cells=CELLS):
    groups = {}
    for policy in ("salary", control):
        subset = [row for row in rows if row["policy"] == policy]
        indexed = {(row["seed"], row["family"], row["budget"]): row["solved"] for row in subset}
        if len(indexed) != len(subset):
            raise ValueError("Duplicate seed/family/budget/policy cell")
        groups[policy] = indexed
    if set(groups["salary"]) != set(groups[control]):
        raise ValueError("Salary/control cell pairing is incomplete")
    seeds = sorted({seed for seed, family, budget in groups["salary"]})
    if not seeds:
        raise ValueError("No paired seed blocks")
    clusters = []
    for seed in seeds:
        actual = {(family, budget) for candidate_seed, family, budget in groups["salary"] if candidate_seed == seed}
        if actual != set(expected_cells):
            raise ValueError("Seed block must retain every expected family/budget cell")
        clusters.append([groups["salary"][seed, family, budget] - groups[control][seed, family, budget]
                         for family, budget in sorted(expected_cells)])
    return clusters


def comparison(rows, control, expected_cells=CELLS):
    clusters = paired_clusters(rows, control, expected_cells)
    # Equal-sized complete blocks: bootstrapping their means is exactly equivalent
    # to concatenating every cell from every sampled block and averaging them.
    block_means = [statistics.mean(cluster) for cluster in clusters]
    rng = random.Random(7621)
    boot = sorted(statistics.mean(rng.choices(block_means, k=len(block_means))) for _ in range(2000))
    diff = [value for cluster in clusters for value in cluster]
    return {"control": control, "paired_cells": len(diff), "independent_seed_blocks": len(clusters),
            "cells_per_block": len(expected_cells), "salary_wins": sum(d > 0 for d in diff),
            "ties": sum(d == 0 for d in diff), "salary_losses": sum(d < 0 for d in diff),
            "success_difference_percentage_points": 100 * statistics.mean(diff),
            "paired_seed_block_bootstrap_95_interval_percentage_points": [100 * boot[49], 100 * boot[1949]],
            "bootstrap_replicates": 2000, "bootstrap_seed": 7621}


def metrics(rows):
    result = {}
    for policy in b.POLICIES:
        subset = [row for row in rows if row["policy"] == policy]
        solved = sum(row["solved"] for row in subset)
        operations = sum(row["spent_operations"] for row in subset)
        result[policy] = {"runs": len(subset), "solved": solved,
                          "success_rate": solved / len(subset),
                          "total_charged_operations": operations,
                          "aggregate_operations_per_solved_task_including_failures": operations / solved if solved else None,
                          "candidate_count": sum(row["candidate_count"] for row in subset),
                          "false_training_matches": sum(row["false_training_matches"] for row in subset)}
    return result


def analyze(rows):
    keys = {(row["seed"], row["family"], row["budget"], row["policy"]) for row in rows}
    expected = {(seed, family, budget, policy) for seed in SEEDS for family in b.FAMILIES
                for budget in BUDGETS for policy in b.POLICIES}
    if len(rows) != len(expected) or keys != expected:
        raise ValueError("Registered run must contain all 6000 unique cells")
    summary = {"overall": metrics(rows), "primary_comparison": comparison(rows, PRIMARY_CONTROL),
               "secondary_comparisons": {policy: comparison(rows, policy) for policy in b.POLICIES
                                         if policy not in ("salary", PRIMARY_CONTROL)},
               "by_budget": {}, "by_family": {}, "by_budget_and_family": {}}
    for budget in BUDGETS:
        subset = [row for row in rows if row["budget"] == budget]
        cells = {(family, budget) for family in b.FAMILIES}
        summary["by_budget"][str(budget)] = {"policies": metrics(subset),
                                             "descriptive_primary_comparison": comparison(subset, PRIMARY_CONTROL, cells)}
        summary["by_budget_and_family"][str(budget)] = {
            family: metrics([row for row in subset if row["family"] == family]) for family in b.FAMILIES}
    for family in b.FAMILIES:
        subset = [row for row in rows if row["family"] == family]
        cells = {(family, budget) for budget in BUDGETS}
        summary["by_family"][family] = {"policies": metrics(subset),
                                        "descriptive_primary_comparison": comparison(subset, PRIMARY_CONTROL, cells)}
    return summary


def output_hash(values):
    return hashlib.sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest()


def compact_witness(witness, budget):
    assert witness["candidate_outputs"] == witness["reference_outputs"]
    return {key: witness[key] for key in ("seed", "family", "policy", "candidate", "candidate_text",
                                          "target_parameters", "training_indices", "verified_points")} | {
        "budget": budget, "candidate_outputs_sha256": output_hash(witness["candidate_outputs"]),
        "reference_outputs_sha256": output_hash(witness["reference_outputs"])}


def report(output, summary):
    primary = summary["primary_comparison"]
    lo, hi = primary["paired_seed_block_bootstrap_95_interval_percentage_points"]
    lines = ["# Confirmatory offline workload results", "",
             "Fresh randomized seeds from the existing finite expression-search workload. No LLM calls or policy tuning.", "",
             f"Primary salary-versus-explore-commit difference: **{primary['success_difference_percentage_points']:+.2f} percentage points**, descriptive 95% paired seed-block bootstrap interval **[{lo:+.2f}, {hi:+.2f}]**. Resampling uses 100 seeds, preserving all 12 family/budget cells per seed.", "",
             f"Paired discoveries: {primary['salary_wins']} salary wins, {primary['ties']} ties, {primary['salary_losses']} salary losses.", "",
             "The outcome is discovery of any independently verified correct candidate within budget. It does not establish that an allocator can choose that candidate using training feedback alone.", "",
             "| Policy | Correct discoveries / cells | Success rate | All charged operations / solved cell, including failures |", "|---|---:|---:|---:|"]
    for policy, item in summary["overall"].items():
        cost = item["aggregate_operations_per_solved_task_including_failures"]
        lines.append(f"| {policy} | {item['solved']} / {item['runs']} | {item['success_rate']:.2%} | {cost:,.1f} |")
    lines.extend(["", "## Descriptive budget slices", "", "The pooled comparison above is primary. These slices were prespecified and are not substitute primary endpoints.", "",
                  "| Operations budget | Salary solved | Explore-commit solved | Difference, percentage points | Seed-block interval |", "|---:|---:|---:|---:|---|"])
    for budget, item in summary["by_budget"].items():
        comp = item["descriptive_primary_comparison"]
        low, high = comp["paired_seed_block_bootstrap_95_interval_percentage_points"]
        policies = item["policies"]
        lines.append(f"| {int(budget):,} | {policies['salary']['solved']} / {policies['salary']['runs']} | {policies[PRIMARY_CONTROL]['solved']} / {policies[PRIMARY_CONTROL]['runs']} | {comp['success_difference_percentage_points']:+.2f} | [{low:+.2f}, {high:+.2f}] |")
    lines.extend(["", "## Descriptive family slices", "", "| Family | Salary solved | Explore-commit solved | Difference, percentage points | Seed-block interval |", "|---|---:|---:|---:|---|"])
    for family, item in summary["by_family"].items():
        comp = item["descriptive_primary_comparison"]
        low, high = comp["paired_seed_block_bootstrap_95_interval_percentage_points"]
        policies = item["policies"]
        lines.append(f"| {family} | {policies['salary']['solved']} / {policies['salary']['runs']} | {policies[PRIMARY_CONTROL]['solved']} / {policies[PRIMARY_CONTROL]['runs']} | {comp['success_difference_percentage_points']:+.2f} | [{low:+.2f}, {high:+.2f}] |")
    lines.extend(["", "## Scope and audit", "",
                  "All five policies, every budget/family combination, costs, secondary comparisons, and false training matches are included in summary.json and the raw CSVs. Budgets repeat the same task seed, and the bootstrap retains that dependence. The primary comparator was selected before these runs from the original exploratory suite. No new outcomes were used for tuning. The original results were preserved byte-for-byte.", "",
                  "This evaluates one fixed salary rule and deterministic enumerators on a known finite grammar. New seeds may still select repeated target functions. Correctness is exhaustive on 81 finite-domain inputs only. Hidden correctness never controls scheduling or stopping. Costs include candidate proposals and AST-node evaluations, including hidden verification and failed runs, but exclude scheduler overhead and Python constant factors. All runs continue spending after discovery. These costs are not tokens, dollars, energy, or deployment latency. Slice intervals are descriptive, with no multiple-comparison claim. Conclusions do not establish performance for LLM agents or other workloads.", "",
                  f"Protocol SHA-256: `{summary['protocol_sha256']}`", "",
                  f"Frozen benchmark SHA-256: `{summary['frozen_benchmark_sha256']}`", "",
                  f"Confirmatory harness SHA-256: `{summary['confirmatory_harness_sha256']}`", "",
                  f"Runtime: {summary['elapsed_seconds']:.3f} seconds. Execution deviations: {summary['deviations'] or 'none'}."])
    (output / "RESULTS.md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "confirmatory_results")
    args = parser.parse_args()
    protocol_hash = integrity()
    original_hashes = {path.name: sha256(path) for path in (ROOT / "results").iterdir() if path.is_file()}
    if args.output.resolve() == (ROOT / "results").resolve():
        parser.error("Refusing to overwrite original results directory")
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    rows, workers, witnesses = [], [], []
    for count, seed in enumerate(SEEDS, 1):
        for family in b.FAMILIES:
            for budget in BUDGETS:
                for policy in b.POLICIES:
                    row, allocation, witness = b.run_one(family, seed, policy, budget)
                    rows.append(row)
                    for worker in allocation:
                        worker["budget"] = budget
                    workers.extend(allocation)
                    if witness is not None:
                        witnesses.append(compact_witness(witness, budget))
        if count % 10 == 0:
            print(f"Completed {count}/100 seed blocks ({count * 60}/6000 runs)", flush=True)
    summary = analyze(rows)
    current_original_hashes = {path.name: sha256(path) for path in (ROOT / "results").iterdir() if path.is_file()}
    if original_hashes != current_original_hashes:
        raise RuntimeError("Original results changed during confirmatory execution")
    summary.update({"protocol_sha256": protocol_hash, "frozen_benchmark_sha256": FROZEN_BENCHMARK_SHA256,
                    "confirmatory_harness_sha256": sha256(Path(__file__)),
                    "configuration": {"seed_start": SEEDS[0], "seed_end_inclusive": SEEDS[-1],
                                      "budgets": BUDGETS, "families": b.FAMILIES, "policies": b.POLICIES,
                                      "runs": len(rows), "primary_control": PRIMARY_CONTROL},
                    "original_result_sha256": original_hashes, "original_results_unchanged": True,
                    "elapsed_seconds": time.monotonic() - started, "deviations": [],
                    "outcome": "Discovery of any independently verified correct candidate, not final policy selection",
                    "successful_witnesses": len(witnesses)})
    b.write_csv(args.output / "runs.csv", rows)
    b.write_csv(args.output / "workers.csv", workers)
    with (args.output / "witnesses.jsonl").open("w") as handle:
        for witness in witnesses:
            handle.write(json.dumps(witness, separators=(",", ":")) + "\n")
    summary["raw_file_sha256"] = {name: sha256(args.output / name) for name in ("runs.csv", "workers.csv", "witnesses.jsonl")}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    report(args.output, summary)
    print(json.dumps(summary["primary_comparison"], indent=2))
    print(f"Runtime: {summary['elapsed_seconds']:.3f}s. Results: {args.output}")


if __name__ == "__main__":
    main()

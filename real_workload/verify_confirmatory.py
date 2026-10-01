#!/usr/bin/env python3
"""Recompute confirmatory witnesses and statistics from saved raw artifacts."""
import argparse
import csv
import json
from collections import defaultdict

import benchmark as b
import confirmatory as c


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=c.Path, default=c.ROOT / "confirmatory_results")
    args = parser.parse_args()
    output = args.output
    summary = json.loads((output / "summary.json").read_text())
    assert c.integrity() == summary["protocol_sha256"]
    assert c.sha256(c.ROOT / "confirmatory.py") == summary["confirmatory_harness_sha256"]
    for filename, digest in summary["raw_file_sha256"].items():
        assert c.sha256(output / filename) == digest, filename
    for filename, digest in summary["original_result_sha256"].items():
        assert c.sha256(c.ROOT / "results" / filename) == digest, filename
    rows = list(csv.DictReader((output / "runs.csv").open()))
    ints = ("seed", "budget", "solved", "spent_operations", "unspent_operations", "candidate_count", "false_training_matches")
    for row in rows:
        for field in ints:
            row[field] = int(row[field])
        assert row["spent_operations"] + row["unspent_operations"] == row["budget"]
        assert row["unspent_operations"] >= 0
    key = lambda row: (int(row["seed"]), row["family"], int(row["budget"]), row["policy"])
    indexed = {key(row): row for row in rows}
    workers = list(csv.DictReader((output / "workers.csv").open()))
    allocations = defaultdict(list)
    for worker in workers:
        allocations[key(worker)].append(worker)
    assert set(allocations) == set(indexed)
    for cell, allocation in allocations.items():
        assert len(allocation) == 4 and {int(w["worker"]) for w in allocation} == set(range(4))
        assert sum(int(w["spent_operations"]) for w in allocation) == indexed[cell]["spent_operations"]
        assert sum(int(w["candidate_count"]) for w in allocation) == indexed[cell]["candidate_count"]
    verified = set()
    with (output / "witnesses.jsonl").open() as handle:
        for line in handle:
            witness = json.loads(line)
            cell = key(witness)
            assert cell not in verified and indexed[cell]["solved"] == 1
            predictions = [b.evaluate(witness["candidate"], x, y) for x, y in b.DOMAIN]
            reference = [b.reference(witness["family"], witness["target_parameters"], x, y) for x, y in b.DOMAIN]
            assert predictions == reference
            assert c.output_hash(predictions) == witness["candidate_outputs_sha256"]
            assert c.output_hash(reference) == witness["reference_outputs_sha256"]
            params, train, targets = b.task(witness["family"], witness["seed"])
            assert list(params) == witness["target_parameters"]
            assert sorted(train) == witness["training_indices"]
            assert list(targets) == reference
            assert witness["verified_points"] == 81
            verified.add(cell)
    assert verified == {cell for cell, row in indexed.items() if row["solved"]}
    recomputed = c.analyze(rows)
    for field, value in recomputed.items():
        assert summary[field] == value, field
    validation = {"raw_runs": len(rows), "worker_rows": len(workers),
                  "successful_witnesses_recomputed": len(verified), "points_per_witness": 81,
                  "all_statistics_recomputed": True, "all_budget_ledgers_reconciled": True,
                  "original_results_byte_identical": True,
                  "raw_file_sha256": summary["raw_file_sha256"]}
    (output / "validation.json").write_text(json.dumps(validation, indent=2) + "\n")
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()

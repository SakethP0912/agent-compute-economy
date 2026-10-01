import hashlib
from pathlib import Path
import unittest

import benchmark as b


class WorkloadTests(unittest.TestCase):
    def test_protocol_hash(self):
        self.assertEqual(hashlib.sha256((b.ROOT / "PROTOCOL.md").read_bytes()).hexdigest(),
                         (b.ROOT / "protocol.sha256").read_text().split()[0])

    def test_all_reference_implementations_agree_exhaustively(self):
        # Independently written arithmetic agrees with AST interpretation for the complete grammar.
        for family, params_list in b.CATALOGUE.items():
            for params in params_list:
                expr = b.make_expr(family, params)
                for x, y in b.DOMAIN:
                    self.assertEqual(b.reference(family, params, x, y), b.evaluate(expr, x, y))

    def test_training_heldout_partition(self):
        for family in b.FAMILIES:
            _, train, _ = b.task(family, 6)
            hidden = set(range(81)) - train
            self.assertEqual(len(train), 9)
            self.assertEqual(len(hidden), 72)
            self.assertFalse(train & hidden)
            self.assertEqual(train | hidden, set(range(81)))

    def test_node_cost_matches_instrumented_execution(self):
        def counted(expr, x, y):
            if expr[0] in ("const", "x", "y"):
                return 1
            return 1 + sum(counted(child, x, y) for child in expr[1:])
        for family in b.FAMILIES:
            expression = b.EXPRESSIONS[family][17]
            measured = 1 + sum(counted(expression, x, y) for x, y in b.DOMAIN)
            self.assertEqual(b.candidate_cost(expression), measured)

    def test_repeated_runs_and_policy_budget(self):
        for policy in b.POLICIES:
            first = b.run_one("piecewise", 2, policy, 24000)
            second = b.run_one("piecewise", 2, policy, 24000)
            self.assertEqual(first, second)
            row, workers, _ = first
            self.assertEqual(row["spent_operations"] + row["unspent_operations"], row["budget"])
            self.assertEqual(sum(w["spent_operations"] for w in workers), row["spent_operations"])
            self.assertGreaterEqual(row["unspent_operations"], 0)

    def test_hidden_results_cannot_change_allocation(self):
        for policy in b.POLICIES:
            ordinary, allocations, _ = b.run_one("affine", 3, policy, 30000)
            changed, changed_allocations, _ = b.run_one("affine", 3, policy, 30000, hidden_override=-1)
            self.assertEqual(ordinary["trace_sha256"], changed["trace_sha256"])
            self.assertEqual(allocations, changed_allocations)

    def test_salary_conservation_through_layoffs_and_rehire(self):
        scheduler = b.Scheduler("salary", 15000, 8)
        while True:
            costs = [730, 892, 811, 1054]
            chosen = scheduler.pick(costs)
            if chosen is None:
                break
            scheduler.observe(chosen, min(1.0, (scheduler.pulls[chosen] + 1) / 20), costs[chosen])
            scheduler.conservation()
        self.assertGreater(scheduler.layoffs, 0)
        self.assertGreater(scheduler.rehires, 0)
        self.assertLess(15000 - scheduler.spent, min(costs))

    def test_correct_program_has_disjoint_heldout_witness(self):
        # A full budget can exhaust every worker stream, so a known grammar target must be found.
        row, _, witness = b.run_one("modular", 1, "equal", 4000000)
        self.assertEqual(row["solved"], 1)
        self.assertEqual(witness["candidate_outputs"], witness["reference_outputs"])
        self.assertEqual(witness["verified_points"], 81)

    def test_bootstrap_preserves_seed_family_clusters_and_pairing(self):
        # Perfect dependence within a seed must not turn four copies into four samples.
        rows = []
        for seed in (0, 1):
            for family in b.FAMILIES:
                rows.append({"seed": seed, "family": family, "policy": "salary", "solved": 1 - seed})
                rows.append({"seed": seed, "family": family, "policy": "equal", "solved": seed})
        clusters = b.paired_seed_clusters(list(reversed(rows)), "equal")
        self.assertEqual(clusters, [[1, 1, 1, 1], [-1, -1, -1, -1]])
        self.assertEqual(b.bootstrap_cluster_interval(clusters), [-1, 1])
        self.assertEqual(b.paired_seed_clusters(rows, "equal"), clusters)
        with self.assertRaisesRegex(ValueError, "not aligned"):
            b.paired_seed_clusters(rows[:-1], "equal")
        with self.assertRaisesRegex(ValueError, "all four families"):
            b.paired_seed_clusters([r for r in rows if r["family"] != "modular"], "equal")

    def test_aggregate_cost_includes_failed_runs(self):
        rows = []
        for policy in b.POLICIES:
            for seed in (0, 1):
                for family in b.FAMILIES:
                    solved = int(policy == "salary" and seed == 0)
                    rows.append({"seed": seed, "family": family, "policy": policy,
                                 "solved": solved, "spent_operations": 100,
                                 "first_success_operations": 40 if solved else None,
                                 "false_training_matches": 0})
        summary = b.summarize(rows)
        salary = summary["policies"]["salary"]
        self.assertEqual(salary["total_spent_operations_including_failures"], 800)
        self.assertEqual(salary["aggregate_operations_per_solved_task_including_failures"], 200)
        self.assertEqual(salary["median_operations_to_success_conditional_on_success"], 40)
        self.assertIsNone(summary["policies"]["equal"]["aggregate_operations_per_solved_task_including_failures"])


if __name__ == "__main__":
    unittest.main()

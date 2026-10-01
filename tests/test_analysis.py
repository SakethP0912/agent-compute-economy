import unittest
from economy.analyze import bootstrap_weights, comparison, policy_summary, summarize_group


def row(seed, policy, completed, spent=10.):
    return dict(seed=seed, policy=policy, completed=completed, spent=spent,
                unused=0., steps=4., switches=1., resets=0., overhead=1., pruned=0.)


class AnalysisTests(unittest.TestCase):
    def test_cost_counts_failed_projects(self):
        result = policy_summary([row(0, "x", 0), row(1, "x", 2)])
        self.assertEqual(result["cost_per_completion"], 10.)
        self.assertEqual(result["zero_completion_rate"], .5)

    def test_pairing_preserves_constant_effect_with_variable_worlds(self):
        # A paired difference of one remains exactly one in every bootstrap draw,
        # even though the raw outcome levels vary substantially across seeds.
        rows = []
        for seed, baseline in enumerate((0, 5, 12)):
            for replicate in range(4):
                rows += [row(seed, "ucb", baseline), row(seed, "salary", baseline),
                         row(seed, "revised", baseline+1)]
        result = summarize_group(rows, ["ucb", "salary", "revised"], [0, 1, 2],
                                 bootstrap_weights(3), "ucb", True)
        comparison = result["comparisons"][0]
        self.assertAlmostEqual(comparison["mean_difference"], 1.)
        for endpoint in comparison["difference_ci95"]:
            self.assertAlmostEqual(endpoint, 1.)

    def test_zero_denominator_is_not_infinite_improvement(self):
        result = comparison("a", "b", {"a": 1., "b": 0.}, {"a": [1., 1.], "b": [0., 0.]})
        self.assertIsNone(result["relative_gain"])
        self.assertIsNone(result["relative_gain_ci95"])
        self.assertEqual(result["ratio_valid_resamples"], 0)

    def test_bootstrap_is_deterministic_and_conserves_cluster_count(self):
        a, b = bootstrap_weights(8), bootstrap_weights(8)
        self.assertEqual(a, b)
        self.assertTrue(all(sum(w for _, w in draw) == 8 for draw in a))


if __name__ == "__main__": unittest.main()

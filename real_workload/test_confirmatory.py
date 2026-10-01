import unittest

import confirmatory as c


class ConfirmatoryTests(unittest.TestCase):
    def test_registered_protocol_and_frozen_source(self):
        self.assertEqual(c.integrity(), "0bd3176bf3be899bd84abd278768181d576e503a9708ed5e538f2dbebad8aa3a")
        self.assertEqual(len(c.SEEDS), 100)
        self.assertEqual(len(c.CELLS), 12)
        self.assertTrue(set(c.SEEDS).isdisjoint(range(12)))

    def test_all_budgets_and_families_stay_in_seed_blocks(self):
        rows = []
        for seed in (10000, 10001):
            for family, budget in c.CELLS:
                for policy in ("salary", "explore_commit"):
                    solved = int((seed == 10000) == (policy == "salary"))
                    rows.append({"seed": seed, "family": family, "budget": budget, "policy": policy, "solved": solved})
        clusters = c.paired_clusters(list(reversed(rows)), "explore_commit")
        self.assertEqual(clusters, [[1] * 12, [-1] * 12])
        comp = c.comparison(rows, "explore_commit")
        self.assertEqual(comp["independent_seed_blocks"], 2)
        self.assertEqual(comp["paired_cells"], 24)
        self.assertEqual(comp["paired_seed_block_bootstrap_95_interval_percentage_points"], [-100, 100])
        with self.assertRaisesRegex(ValueError, "pairing is incomplete"):
            c.paired_clusters(rows[:-1], "explore_commit")
        with self.assertRaisesRegex(ValueError, "every expected"):
            c.paired_clusters([row for row in rows if row["budget"] != 40000], "explore_commit")

    def test_incomplete_registered_run_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "6000"):
            c.analyze([])


if __name__ == "__main__":
    unittest.main()

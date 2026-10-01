import dataclasses
import unittest
from economy.simulator import World, SCENARIOS, Environment, Observation, draw, run
from economy.policies import Salary
from economy.experiment import base_candidates, revised_candidates


class SimulatorTests(unittest.TestCase):
    def test_budget_conservation_and_termination(self):
        for s in SCENARIOS:
            for c in base_candidates() + revised_candidates():
                r = run(World.make(17, s), 40, c)
                self.assertLessEqual(r["spent"], 40 + 1e-8)
                self.assertAlmostEqual(r["spent"] + r["unused"], 40)
                self.assertLess(r["steps"], 100)
                self.assertLessEqual(r["completed"], 20)

    def test_exact_replay(self):
        w = World.make(71, SCENARIOS[-1])
        c = revised_candidates()[0]
        self.assertEqual(run(w, 80, c, True), run(w, 80, c, True))

    def test_exogenous_draws_ignore_order(self):
        a = {(i, j): draw(71, 3, i, j) for i in range(4) for j in range(20)}
        b = {(i, j): draw(71, 3, i, j) for j in reversed(range(20)) for i in reversed(range(4))}
        self.assertEqual(a, b)

    def test_observation_contains_no_hidden_dynamics(self):
        self.assertEqual({f.name for f in dataclasses.fields(Observation)},
                         {"task", "task_type", "remaining", "costs", "scores", "attempts", "completed"})
        w = World.make(4, SCENARIOS[0])
        obs = Environment(w, 40, .01).observe()
        self.assertFalse(hasattr(obs, "difficulty"))
        self.assertFalse(hasattr(obs, "skills"))

    def test_homogeneous_null_equalizes_productivity(self):
        w = World.make(9, SCENARIOS[0])
        self.assertEqual(w.skills, (1., 1., 1., 1.))

    def test_unaffordable_action_cannot_execute(self):
        env = Environment(World.make(1, SCENARIOS[0]), .01, .01)
        with self.assertRaises(ValueError): env.step(0)
        self.assertEqual(env.remaining, .01)

    def test_shared_progress_null_worker_choice_cannot_improve_work(self):
        w = World.make(9, SCENARIOS[-1])
        a, b = Environment(w, 40, .01), Environment(w, 40, .01)
        for step in range(20):
            a.step(0)
            b.step(step % 4)
            self.assertEqual(a.task, b.task)
            self.assertEqual(a.progress, b.progress)
            self.assertEqual(a.remaining, b.remaining)

    def test_wallet_conservation_every_step(self):
        env = Environment(World.make(31, SCENARIOS[2]), 80, .07)
        policy = Salary(dict(retention=.75, payday=8), 80)
        while env.task < 20:
            obs = env.observe()
            affordable = [i for i, c in enumerate(obs.costs) if c <= obs.remaining]
            if not affordable: break
            i = policy.choose(obs, affordable)
            self.assertAlmostEqual(sum(policy.wallets) + policy.treasury, env.remaining)
            if i is None: break
            policy.update(env.step(i))
            self.assertAlmostEqual(sum(policy.wallets) + policy.treasury, env.remaining)


if __name__ == "__main__": unittest.main()

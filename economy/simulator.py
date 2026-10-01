"""Hidden-state worker portfolio. Policies see Observation, never World.

Credits model costs; they are neither measured tokens nor measured dollars.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
import math
import random


@dataclass(frozen=True)
class Scenario:
    name: str
    heterogeneity: float = 0.0
    specialists: bool = False
    delay: float = 0.0
    noise: float = 0.025
    misleading: bool = False
    shift: bool = False
    context_growth: float = 0.015
    switch_cost: float = 0.08
    controller_multiplier: float = 1.0
    holdout: bool = False
    shared_progress: bool = False


SCENARIOS = (
    Scenario("homogeneous"),
    Scenario("heterogeneous", heterogeneity=1.0),
    Scenario("specialists", heterogeneity=.25, specialists=True),
    Scenario("delayed", heterogeneity=.8, delay=3.0),
    Scenario("noisy", heterogeneity=.8, noise=.23),
    Scenario("misleading", heterogeneity=.8, misleading=True),
    Scenario("regime_shift", heterogeneity=.8, shift=True),
    Scenario("costly_context", heterogeneity=.7, context_growth=.16, switch_cost=1.2),
    Scenario("delayed_misleading", heterogeneity=.8, delay=3.0, misleading=True, holdout=True),
    Scenario("shift_memory", heterogeneity=.8, shift=True, context_growth=.16, switch_cost=1.2, holdout=True),
    Scenario("high_overhead", heterogeneity=.7, controller_multiplier=8.0, holdout=True),
    Scenario("weak_signal", heterogeneity=.12, noise=.4, holdout=True),
    Scenario("shared_progress_null", context_growth=0., switch_cost=0., noise=0., holdout=True, shared_progress=True),
)


def draw(seed: int, task: int, worker: int, attempt: int, lane: int = 0) -> float:
    """Stateless SplitMix64 draw, independent of scheduling order and Python hash."""
    mask = (1 << 64) - 1
    z = (seed * 0x9E3779B97F4A7C15 + task * 0xBF58476D1CE4E5B9 +
         worker * 0x94D049BB133111EB + attempt * 0xD2B74407B1CE6E93 + lane * 0xCA5A826395121157) & mask
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & mask
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & mask
    z ^= z >> 31
    return ((z >> 11) + .5) / (1 << 53)


@dataclass(frozen=True)
class World:
    seed: int
    scenario: Scenario
    costs: tuple[float, ...]
    skills: tuple[float, ...]
    types: tuple[int, ...]
    difficulty: tuple[float, ...]
    specialists: tuple[int, ...]
    misleading_worker: int

    @classmethod
    def make(cls, seed: int, scenario: Scenario) -> "World":
        # Scenario names do not alter seed construction: cross-scenario pairing is retained.
        rng = random.Random(seed * 107 + 19)
        skills = [.35, .75, 1.25, 1.95]
        rng.shuffle(skills)
        skills = tuple(1 + scenario.heterogeneity * (x - 1) for x in skills)
        specs = list(range(4))
        rng.shuffle(specs)
        costs = (1.,) * 4 if scenario.shared_progress else (.7, 1., 1.3, 1.8)
        return cls(seed, scenario, costs, skills,
                   tuple(rng.randrange(4) for _ in range(20)),
                   tuple(rng.uniform(4.0, 9.0) for _ in range(20)), tuple(specs), rng.randrange(4))


@dataclass(frozen=True)
class Observation:
    task: int
    task_type: int
    remaining: float
    costs: tuple[float, ...]
    scores: tuple[float, ...]
    attempts: tuple[int, ...]
    completed: int


@dataclass(frozen=True)
class Feedback:
    worker: int
    task_type: int
    cost: float
    progress_delta: float
    solved: bool


class Environment:
    def __init__(self, world: World, budget: float, controller_cost: float, memory: bool = True):
        self._world = world
        self.budget = float(budget)
        self.remaining = float(budget)
        self.controller_cost = controller_cost
        self.memory = memory
        self.task = 0
        self.progress = [0.] * 4
        self.effort = [0.] * 4
        self.scores = [0.] * 4
        self.attempts = [0] * 4
        self.context = [0] * 4
        self.last = None
        self.steps = self.switches = self.resets = 0
        self.overhead = 0.
        self.trace = []

    def _cost(self, i: int) -> tuple[float, float, bool]:
        s = self._world.scenario
        compact = self.context[i] >= 12 and not s.shared_progress
        context = 2 if compact else self.context[i]
        work = self._world.costs[i] * (1 + s.context_growth * context)
        overhead = .08 + self.controller_cost * s.controller_multiplier
        if self.last is not None and self.last != i:
            overhead += s.switch_cost * (1 if self.memory else 3)
        if compact:
            overhead += .35 if self.memory else .9
        return work + overhead, overhead, compact

    def observe(self) -> Observation:
        return Observation(self.task, self._world.types[min(self.task, 19)], self.remaining,
                           tuple(self._cost(i)[0] for i in range(4)), tuple(self.scores),
                           tuple(self.attempts), self.task)

    def step(self, worker: int, record: bool = False) -> Feedback:
        if self.task >= 20:
            raise ValueError("Project already complete")
        w, s, task = self._world, self._world.scenario, self.task
        cost, overhead, compact = self._cost(worker)
        if cost > self.remaining + 1e-9:
            raise ValueError("Unaffordable action")
        before = self.scores[worker]
        if self.last is not None and self.last != worker:
            self.switches += 1
        if compact:
            self.context[worker] = 2
            self.resets += 1
            if not self.memory:
                self.progress[worker] *= .8
        self.remaining = max(0., self.remaining - cost)
        self.overhead += overhead
        self.context[worker] += 1
        self.steps += 1
        attempt = self.attempts[worker]
        self.attempts[worker] += 1
        self.effort[worker] += w.costs[worker]
        effective_worker = (worker + 2) % 4 if s.shift and self.budget-self.remaining > self.budget / 2 else worker
        rate = w.skills[effective_worker]
        if s.specialists:
            rate *= 2.1 if w.specialists[worker] == w.types[task] else .5
        # Warm-up is paid work. It yields no public or hidden progress until complete.
        warmup = s.delay * (1.6 if rate > 1.2 else .35)
        exog_worker = 0 if s.shared_progress else worker
        exog_attempt = sum(self.attempts)-1 if s.shared_progress else attempt
        work_gain = w.costs[worker] * rate * (.45 + 1.1 * draw(w.seed, task, exog_worker, exog_attempt))
        if self.effort[worker] <= warmup:
            work_gain = 0.
        elif s.delay and rate > 1.2:
            work_gain *= 1.65
        if s.misleading and worker == w.misleading_worker:
            work_gain *= .18
        self.progress[worker] += work_gain
        if s.shared_progress:
            self.progress = [self.progress[worker]] * 4
        solved = self.progress[worker] >= w.difficulty[task]
        score = self.progress[worker] / w.difficulty[task]
        if s.misleading and worker == w.misleading_worker:
            score += min(.8, .16 * self.attempts[worker])
        noise = s.noise * (2 * draw(w.seed, task, worker, attempt, 1) - 1)
        score = 1. if solved else min(.95, max(0., score + noise))
        delta = score - before
        self.scores[worker] = score
        if s.shared_progress:
            self.scores = [score] * 4
        self.last = worker
        if record:
            self.trace.append(dict(step=self.steps, task=task, worker=worker, cost=cost,
                                   overhead=overhead, public_score=score, solved=solved,
                                   remaining=self.remaining, compact=compact))
        if solved:
            self.task += 1
            self.progress = [0.] * 4
            self.effort = [0.] * 4
            self.scores = [0.] * 4
            self.attempts = [0] * 4
        return Feedback(worker, w.types[task], cost, delta, solved)


def run(world: World, budget: float, config: dict, record: bool = False) -> dict:
    from .policies import make_policy
    policy = make_policy(config, budget)
    env = Environment(world, budget, policy.overhead, config.get("memory", True))
    while env.task < 20:
        obs = env.observe()
        affordable = [i for i, cost in enumerate(obs.costs) if cost <= obs.remaining + 1e-9]
        if not affordable:
            break
        worker = policy.choose(obs, affordable)
        if worker is None:
            break
        fb = env.step(worker, record)
        policy.update(fb)
        if env.steps > 2000:
            raise AssertionError("No progress toward budget termination")
    result = dict(seed=world.seed, scenario=world.scenario.name, holdout=world.scenario.holdout,
                  budget=budget, policy=config["name"], completed=env.task,
                  spent=budget-env.remaining, unused=env.remaining, steps=env.steps,
                  switches=env.switches, resets=env.resets, overhead=env.overhead,
                  pruned=getattr(policy, "pruned", 0))
    if hasattr(policy, "wallets"):
        assert abs(sum(policy.wallets) + policy.treasury - env.remaining) < 1e-7
    if record:
        result["trace"] = env.trace
    assert result["spent"] <= budget + 1e-8
    return result

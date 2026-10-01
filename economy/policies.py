"""Policies use public observations only. No policy receives the hidden world."""
import math


class Policy:
    overhead = .01
    def update(self, fb):
        pass


class Fixed(Policy):
    def __init__(self, config):
        self.config = config
        self.turn = 0

    def choose(self, obs, affordable):
        kind = self.config["kind"]
        if kind == "single":
            i = self.config["worker"]
            return i if i in affordable else None
        if kind == "explore_commit":
            exploration = self.config.get("probes", 1)
            under = [i for i in affordable if obs.attempts[i] < exploration]
            if under:
                return min(under, key=lambda i: (obs.attempts[i], obs.costs[i]))
            return max(affordable, key=lambda i: obs.scores[i] / obs.costs[i])
        block = self.config.get("block", 1)
        choice = (self.turn // block) % 4
        self.turn += 1
        return choice if choice in affordable else min(affordable, key=lambda i: obs.costs[i])


class UCB(Policy):
    overhead = .04
    def __init__(self, config):
        self.config = config
        self.counts = [[0.] * 4 for _ in range(4)]
        self.gains = [[0.] * 4 for _ in range(4)]
        self.costs = [[0.] * 4 for _ in range(4)]
        self.turn = 0
        self.previous = None
        self.lease_left = 0
        self.previous_task = -1

    def choose(self, obs, affordable):
        t = obs.task_type
        revised = self.config["kind"] == "revised"
        # All arms know task IDs and public progress; no hidden rate/difficulty enters.
        if self.previous in affordable and self.lease_left > 0 and self.previous_task == obs.task:
            self.lease_left -= 1
            return self.previous
        unseen = [i for i in affordable if self.counts[t][i] < .5]
        if unseen:
            chosen = min(unseen, key=lambda i: obs.costs[i])
        else:
            total = sum(self.counts[t])
            explore = self.config.get("explore", .2)
            def score(i):
                mean = self.gains[t][i] / max(self.costs[t][i], 1e-9)
                bonus = explore * math.sqrt(math.log(2 + total) / max(self.counts[t][i], .25)) / obs.costs[i]
                continuity = self.config.get("continuity", 0) * obs.scores[i] / obs.costs[i]
                return mean + bonus + continuity
            chosen = max(affordable, key=score)
        self.previous = chosen
        self.previous_task = obs.task
        self.lease_left = self.config.get("lease", 1) - 1
        return chosen

    def update(self, fb):
        t, i = fb.task_type, fb.worker
        decay = self.config.get("decay", 1.)
        for j in range(4):
            self.counts[t][j] *= decay
            self.costs[t][j] *= decay
            self.gains[t][j] *= decay
        self.counts[t][i] += 1
        self.costs[t][i] += fb.cost
        self.gains[t][i] += float(fb.solved) + self.config.get("shaping", 1.) * fb.progress_delta
        self.turn += 1


class Salary(Policy):
    overhead = .07
    def __init__(self, config, budget):
        self.config = config
        grant = config.get("grant", .5)
        self.wallets = [budget * grant / 4] * 4
        self.treasury = budget * (1-grant)
        self.earned = [0.] * 4
        self.spent = [0.] * 4
        self.active = set(range(4))
        self.turn = 0
        self.pruned = 0
        self.last_payday = 0

    def _payday(self, obs, affordable):
        # Reclaim only unspent credits. Economic score never mints money.
        self.treasury += sum(self.wallets)
        self.wallets = [0.] * 4
        retention = self.config.get("retention", .75)
        count = max(1, math.ceil(len(self.active) * retention))
        ranked = sorted(self.active, key=lambda i: (self.earned[i] / max(self.spent[i], .1), -obs.costs[i]), reverse=True)
        keep = set(ranked[:count])
        self.pruned += len(self.active - keep)
        self.active = keep
        eligible = self.active.intersection(affordable)
        if not eligible:
            return
        weights = {i: .05 + self.earned[i] / max(self.spent[i], .1) for i in eligible}
        payout = self.treasury  # Remaining credits are committed, never new credits.
        for i in eligible:
            self.wallets[i] = payout * weights[i] / sum(weights.values())
        self.treasury = 0.
        self.last_payday = self.turn

    def choose(self, obs, affordable):
        ready = [i for i in affordable if i in self.active and self.wallets[i] >= obs.costs[i] - 1e-9]
        if self.turn - self.last_payday >= self.config.get("payday", 8) or not ready:
            self._payday(obs, affordable)
            ready = [i for i in affordable if i in self.active and self.wallets[i] >= obs.costs[i] - 1e-9]
        if not ready:
            # Fragmented wallets cannot spend a full next action. Reallocate existing
            # credits to the best surviving affordable worker instead of stranding them.
            eligible = self.active.intersection(affordable)
            if not eligible:
                return None
            i = max(eligible, key=lambda j: (self.earned[j] / max(self.spent[j], .1), -obs.costs[j]))
            total = self.treasury + sum(self.wallets)
            if total < obs.costs[i] - 1e-9:
                return None
            self.wallets = [0.] * 4
            self.wallets[i] = total
            self.treasury = 0.
            ready = [i]
        # Workers spend in turns; larger wallets permit more turns before exhaustion.
        return min(ready, key=lambda i: ((i - self.turn) % 4))

    def update(self, fb):
        i = fb.worker
        self.wallets[i] = max(0., self.wallets[i] - fb.cost)
        self.spent[i] += fb.cost
        reward = float(fb.solved)
        if self.config.get("milestones", False):
            reward += max(0., fb.progress_delta)
        self.earned[i] += reward
        self.turn += 1


def make_policy(config, budget):
    if config["kind"] in ("round_robin", "fixed_blocks", "single", "explore_commit"):
        return Fixed(config)
    if config["kind"] in ("ucb", "revised"):
        obj = UCB(config)
        if config["kind"] == "revised":
            obj.overhead = .06
        return obj
    if config["kind"] == "salary":
        return Salary(config, budget)
    raise ValueError(config["kind"])

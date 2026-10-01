#!/usr/bin/env python3
"""Deterministic offline synthesis benchmark; Python standard library only."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import time

ROOT = Path(__file__).resolve().parent
FAMILIES = ("affine", "quadratic", "piecewise", "modular")
POLICIES = ("equal", "random", "salary", "cost_ucb", "explore_commit")
DOMAIN = tuple((x, y) for x in range(-4, 5) for y in range(-4, 5))
N = len(FAMILIES)


def stable_seed(*parts):
    return int.from_bytes(hashlib.sha256(repr(parts).encode()).digest()[:8], "big")


def const(value):
    return ("const", value)


X, Y = ("x",), ("y",)


def add(a, b):
    return ("add", a, b)


def mul(a, b):
    return ("mul", a, b)


def scale(coefficient, expression):
    return mul(const(coefficient), expression)


def linear(a, b, c):
    return add(add(scale(a, X), scale(b, Y)), const(c))


def make_expr(family, params):
    if family == "affine":
        return linear(*params)
    if family == "quadratic":
        a, b, c, mode = params
        base = mul(X, X if mode == 0 else Y)
        return add(add(scale(a, base), scale(b, Y)), const(c))
    if family == "piecewise":
        kind, a, b, c = params
        if kind == "abs":
            return add(("abs", add(X, scale(a, Y))), const(c))
        return add((kind, add(X, const(a)), add(Y, const(b))), const(c))
    if family == "modular":
        a, b, c, m = params
        return ("mod", linear(a, b, c), const(m))
    raise ValueError(family)


def reference(family, params, x, y):
    """Independent reference; deliberately does not call the candidate interpreter."""
    if family == "affine":
        a, b, c = params
        return a * x + b * y + c
    if family == "quadratic":
        a, b, c, mode = params
        return a * (x * x if mode == 0 else x * y) + b * y + c
    if family == "piecewise":
        kind, a, b, c = params
        if kind == "abs":
            return abs(x + a * y) + c
        return (min(x + a, y + b) if kind == "min" else max(x + a, y + b)) + c
    if family == "modular":
        a, b, c, m = params
        return (a * x + b * y + c) % m
    raise ValueError(family)


def evaluate(expr, x, y):
    op = expr[0]
    if op == "const":
        return expr[1]
    if op == "x":
        return x
    if op == "y":
        return y
    a = evaluate(expr[1], x, y)
    if op == "abs":
        return abs(a)
    b = evaluate(expr[2], x, y)
    if op == "add":
        return a + b
    if op == "mul":
        return a * b
    if op == "min":
        return min(a, b)
    if op == "max":
        return max(a, b)
    if op == "mod":
        return a % b
    raise ValueError(op)


def node_count(expr):
    if expr[0] in ("const", "x", "y"):
        return 1
    return 1 + sum(node_count(child) for child in expr[1:])


def candidate_cost(expr):
    return 1 + len(DOMAIN) * node_count(expr)


def pretty(expr):
    op = expr[0]
    if op == "const":
        return str(expr[1])
    if op in ("x", "y"):
        return op
    if op == "abs":
        return "abs(" + pretty(expr[1]) + ")"
    a, b = pretty(expr[1]), pretty(expr[2])
    if op in ("min", "max"):
        return f"{op}({a}, {b})"
    symbol = {"add": "+", "mul": "*", "mod": "%"}[op]
    return f"({a} {symbol} {b})"


def catalogue():
    specs = {family: [] for family in FAMILIES}
    for a in range(-3, 4):
        for b in range(-3, 4):
            if a or b:
                for c in range(-2, 3):
                    specs["affine"].append((a, b, c))
    for a in (-2, -1, 1, 2):
        for b in range(-2, 3):
            for c in range(-1, 2):
                for mode in (0, 1):
                    specs["quadratic"].append((a, b, c, mode))
    for kind in ("min", "max"):
        for a in range(-2, 3):
            for b in range(-2, 3):
                for c in range(-1, 2):
                    specs["piecewise"].append((kind, a, b, c))
    for a in range(-2, 3):
        for c in range(-2, 3):
            specs["piecewise"].append(("abs", a, 0, c))
    for a in range(-2, 3):
        for b in range(-2, 3):
            if a or b:
                for c in range(-1, 2):
                    for m in (2, 3, 4):
                        specs["modular"].append((a, b, c, m))
    return specs


CATALOGUE = catalogue()
EXPRESSIONS = {family: tuple(make_expr(family, p) for p in params)
               for family, params in CATALOGUE.items()}


def task(family, seed):
    rng = random.Random(stable_seed("target", family, seed))
    params = rng.choice(CATALOGUE[family])
    train = frozenset(rng.sample(range(len(DOMAIN)), 9))
    targets = tuple(reference(family, params, x, y) for x, y in DOMAIN)
    return params, train, targets


def worker_streams(seed):
    streams = []
    for worker, family in enumerate(FAMILIES):
        rng = random.Random(stable_seed("stream", seed, worker))
        own = list(EXPRESSIONS[family])
        rest = [expr for other in FAMILIES if other != family for expr in EXPRESSIONS[other]]
        rng.shuffle(own)
        rng.shuffle(rest)
        streams.append(own + rest)
    return streams


class Scheduler:
    """Only training observations cross this allocator boundary."""
    def __init__(self, policy, budget, seed):
        self.policy, self.budget = policy, budget
        self.rng = random.Random(stable_seed("policy", policy, seed))
        self.best = [0.0] * N
        self.costs = [0] * N
        self.pulls = [0] * N
        self.spent = 0
        self.cursor = 0
        self.wallets = [budget // (2 * N)] * N
        self.reserve = budget - sum(self.wallets)
        self.live = set(range(N))
        self.layoffs = 0
        self.rehires = 0

    def conservation(self):
        if self.policy == "salary":
            assert self.spent + sum(self.wallets) + self.reserve == self.budget
            assert self.reserve >= 0 and min(self.wallets) >= 0

    def rank(self, worker):
        return self.best[worker], -self.costs[worker], -worker

    def pick(self, next_costs):
        eligible = [i for i, cost in enumerate(next_costs)
                    if cost is not None and cost <= self.budget - self.spent]
        if not eligible:
            return None
        if self.policy == "random":
            return self.rng.choice(eligible)
        if self.policy == "equal" or (self.policy == "explore_commit" and self.spent < self.budget // 4):
            for offset in range(N):
                i = (self.cursor + offset) % N
                if i in eligible:
                    self.cursor = (i + 1) % N
                    return i
        if self.policy == "explore_commit":
            return max(eligible, key=self.rank)
        if self.policy == "cost_ucb":
            unseen = [i for i in eligible if self.pulls[i] == 0]
            if unseen:
                return unseen[0]
            total = sum(self.pulls)
            return max(eligible, key=lambda i: self.best[i] * 1000 / self.costs[i]
                       + math.sqrt(2 * math.log(total) / self.pulls[i]))
        if self.policy != "salary":
            raise ValueError(self.policy)
        for i in tuple(self.live):
            if i not in eligible or self.wallets[i] < next_costs[i]:
                self.reserve += self.wallets[i]
                self.wallets[i] = 0
                self.live.remove(i)
                self.layoffs += 1
        if not self.live:
            # Reallocation uses observed training quality; no hidden verifier result.
            winner = max(eligible, key=self.rank)
            self.reserve += sum(self.wallets)
            self.wallets = [0] * N
            self.wallets[winner], self.reserve = self.reserve, 0
            self.live = {winner}
            self.rehires += 1
        self.conservation()
        return max(self.live, key=lambda i: (self.wallets[i] / next_costs[i], -i))

    def observe(self, worker, train_score, cost):
        improvement = max(0.0, train_score - self.best[worker])
        self.best[worker] = max(self.best[worker], train_score)
        self.costs[worker] += cost
        self.pulls[worker] += 1
        self.spent += cost
        if self.policy == "salary":
            self.wallets[worker] -= cost
            grant = min(self.reserve, int(improvement * self.budget / N))
            self.reserve -= grant
            self.wallets[worker] += grant
        self.conservation()


def run_one(family, seed, policy, budget, hidden_override=None):
    params, train, targets = task(family, seed)
    streams = worker_streams(seed)
    positions = [0] * N
    scheduler = Scheduler(policy, budget, seed)
    first_success_cost = None
    first_train_match_cost = None
    false_matches = 0
    successes = 0
    witness = None
    trace = []
    while True:
        next_costs = [candidate_cost(streams[i][positions[i]]) if positions[i] < len(streams[i]) else None for i in range(N)]
        worker = scheduler.pick(next_costs)
        if worker is None:
            break
        expression = streams[worker][positions[worker]]
        positions[worker] += 1
        cost = next_costs[worker]
        predictions = tuple(evaluate(expression, x, y) for x, y in DOMAIN)
        training_matches = sum(predictions[j] == targets[j] for j in train)
        train_score = training_matches / len(train)
        # Independent hidden observer. Its results never enter scheduler state.
        hidden_matches = sum(predictions[j] == targets[j] for j in range(len(DOMAIN)) if j not in train)
        if hidden_override is not None:
            hidden_matches = hidden_override
        scheduler.observe(worker, train_score, cost)
        trace.append((worker, cost, training_matches))
        if training_matches == len(train):
            if first_train_match_cost is None:
                first_train_match_cost = scheduler.spent
            if hidden_matches == len(DOMAIN) - len(train):
                successes += 1
                if first_success_cost is None:
                    first_success_cost = scheduler.spent
                    witness = {"seed": seed, "family": family, "policy": policy,
                               "target_parameters": params, "candidate": expression,
                               "candidate_text": pretty(expression), "training_indices": sorted(train),
                               "domain": list(DOMAIN), "reference_outputs": list(targets),
                               "candidate_outputs": list(predictions), "verified_points": len(DOMAIN)}
            else:
                false_matches += 1
    row = {"seed": seed, "family": family, "policy": policy, "budget": budget,
           "spent_operations": scheduler.spent, "unspent_operations": budget - scheduler.spent,
           "candidate_count": sum(positions), "solved": int(first_success_cost is not None),
           "first_success_operations": first_success_cost, "first_train_match_operations": first_train_match_cost,
           "false_training_matches": false_matches, "verified_candidates": successes,
           "best_training_fraction": max(scheduler.best), "layoffs": scheduler.layoffs,
           "rehires": scheduler.rehires,
           "trace_sha256": hashlib.sha256(repr(trace).encode()).hexdigest()}
    workers = [{"seed": seed, "family": family, "policy": policy, "worker": i,
                "specialization": FAMILIES[i], "candidate_count": positions[i],
                "spent_operations": scheduler.costs[i], "best_training_fraction": scheduler.best[i],
                "final_wallet": scheduler.wallets[i] if policy == "salary" else None}
               for i in range(N)]
    assert row["spent_operations"] <= budget
    assert sum(w["spent_operations"] for w in workers) == scheduler.spent
    return row, workers, witness


def bootstrap_interval(differences):
    rng = random.Random(7621)
    values = sorted(statistics.mean(rng.choices(differences, k=len(differences))) for _ in range(2000))
    return [values[49], values[1949]]


def summarize(rows):
    result = {"policies": {}, "salary_paired_comparisons": {}}
    for policy in POLICIES:
        subset = [r for r in rows if r["policy"] == policy]
        costs = [r["first_success_operations"] for r in subset if r["solved"]]
        result["policies"][policy] = {
            "runs": len(subset), "solved": sum(r["solved"] for r in subset),
            "success_rate": statistics.mean(r["solved"] for r in subset),
            "mean_spent_operations": statistics.mean(r["spent_operations"] for r in subset),
            "median_operations_to_success_conditional_on_success": statistics.median(costs) if costs else None,
            "false_training_matches": sum(r["false_training_matches"] for r in subset),
            "per_family": {family: {"solved": sum(r["solved"] for r in subset if r["family"] == family),
                                    "runs": sum(r["family"] == family for r in subset)} for family in FAMILIES}}
    salary = {(r["seed"], r["family"]): r for r in rows if r["policy"] == "salary"}
    for policy in POLICIES:
        if policy == "salary":
            continue
        subset = [r for r in rows if r["policy"] == policy]
        diff = [salary[r["seed"], r["family"]]["solved"] - r["solved"] for r in subset]
        result["salary_paired_comparisons"][policy] = {
            "wins": sum(d > 0 for d in diff), "ties": sum(d == 0 for d in diff),
            "losses": sum(d < 0 for d in diff), "success_rate_difference": statistics.mean(diff),
            "paired_bootstrap_95_interval": bootstrap_interval(diff)}
    return result


def write_csv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=12)
    parser.add_argument("--budget", type=int, default=120000)
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    if args.seeds < 1 or args.budget < 1:
        parser.error("seeds and budget must be positive")
    digest = hashlib.sha256((ROOT / "PROTOCOL.md").read_bytes()).hexdigest()
    registered = (ROOT / "protocol.sha256").read_text().split()[0]
    if digest != registered:
        raise RuntimeError("Protocol hash mismatch; do not silently alter registration")
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    rows, workers, witnesses = [], [], []
    for seed in range(args.seeds):
        for family in FAMILIES:
            for policy in POLICIES:
                row, allocation, witness = run_one(family, seed, policy, args.budget)
                rows.append(row)
                workers.extend(allocation)
                if witness is not None:
                    witnesses.append(witness)
        print(f"Completed seed {seed + 1}/{args.seeds}", flush=True)
    summary = summarize(rows)
    summary.update({"protocol_sha256": digest,
                    "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    "configuration": {"seeds": args.seeds, "budget": args.budget, "families": FAMILIES,
                                      "policies": POLICIES, "training_inputs": 9, "heldout_inputs": 72},
                    "registered_default_run": args.seeds == 12 and args.budget == 120000,
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                    "scope": "Offline deterministic expression search; no LLM performance inference",
                    "deviations": [] if args.seeds == 12 and args.budget == 120000 else ["Nondefault run parameters explicitly requested on CLI"]})
    write_csv(args.output / "runs.csv", rows)
    write_csv(args.output / "workers.csv", workers)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (args.output / "witnesses.json").write_text(json.dumps(witnesses, indent=2) + "\n")
    lines = ["# Offline executable workload results", "", "Actual finite-domain program synthesis, not an LLM benchmark.", "",
             f"Protocol SHA-256: `{digest}`", "", "| Policy | Solved / tasks | Success rate | Median operations to success, successful tasks only |", "|---|---:|---:|---:|"]
    for policy, item in summary["policies"].items():
        lines.append(f"| {policy} | {item['solved']} / {item['runs']} | {item['success_rate']:.1%} | {item['median_operations_to_success_conditional_on_success']} |")
    lines.extend(["", "## Paired salary comparisons", "", "Win/tie/loss refers to task correctness within budget, not speed.", ""])
    for policy, item in summary["salary_paired_comparisons"].items():
        lo, hi = item["paired_bootstrap_95_interval"]
        lines.append(f"- Versus {policy}: {item['wins']} wins, {item['ties']} ties, {item['losses']} losses; success difference {item['success_rate_difference']:+.1%}, descriptive paired bootstrap interval [{lo:+.1%}, {hi:+.1%}].")
    lines.extend(["", "## Limits", "", "Targets are sampled from the workers' known finite grammar. Family-specialized enumerators are a constructed allocation problem, not general-purpose agents. The full finite domain is exhaustively verified, but correctness beyond it is untested. Heldout observations never feed scheduling or stopping. All runs spend their available budget regardless of discovery; cost to first success is an offline diagnostic. A salary outcome depends on this specific reward and reallocation rule. Cost-UCB and explore-commit are simple untuned adaptive controls, not optimal algorithms. Operation accounting excludes scheduling, expression construction, reference construction, and Python constant-factor execution overhead. This does not estimate dollars, tokens, latency, learning, or LLM quality. Successful-task cost conditions on different success sets and is not a standalone policy ranking. Intervals describe the small constructed suite. Null and losing comparisons are retained.", "", f"Recorded wall time: {summary['elapsed_seconds']} seconds (diagnostic only).", "", f"Run deviations: {summary['deviations'] or 'none'}. "])
    (args.output / "RESULTS.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary["policies"], indent=2))
    print(f"Results: {args.output}")


if __name__ == "__main__":
    main()

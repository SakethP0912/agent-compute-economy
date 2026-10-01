"""Run development, freeze configurations, then evaluate untouched worlds."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import statistics
import time
from .simulator import SCENARIOS, World, run

ROOT = Path(__file__).resolve().parents[1]
BUDGETS = (40, 80, 160)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / "economy").glob("*.py"))}


def design_hashes():
    return {name: sha(ROOT / name) for name in ("PROTOCOL.md", "DEVELOPMENT_LOG.md")}


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def base_candidates():
    configs = [dict(name="round_robin", kind="round_robin")]
    configs += [dict(name=f"fixed_blocks_{b}", kind="fixed_blocks", block=b) for b in (2, 4, 8)]
    configs += [dict(name=f"single_{i}", kind="single", worker=i) for i in range(4)]
    configs += [dict(name=f"ucb_{x}_{lease}", kind="ucb", explore=x, lease=lease)
                for x in (.05, .2, .5) for lease in (1, 4, 8)]
    configs += [dict(name=f"explore_commit_{p}", kind="explore_commit", probes=p) for p in (1, 2)]
    configs += [dict(name=f"salary_{r}_{p}", kind="salary", retention=r, payday=p, milestones=False)
                for r in (.5, .75, 1.) for p in (8, 16)]
    configs += [dict(name=f"salary_milestones_{r}_{p}", kind="salary", retention=r, payday=p, milestones=True)
                for r in (.5, .75, 1.) for p in (8, 16)]
    return configs


def revised_candidates():
    return [dict(name=f"revised_{e}_{lease}_{decay}", kind="revised", explore=e,
                 lease=lease, decay=decay, continuity=.15, shaping=1.)
            for e in (.05, .2, .5) for lease in (2, 4, 8) for decay in (.9, 1.)]


def evaluate(configs, seeds, scenarios, budgets=BUDGETS):
    rows = []
    for scenario in scenarios:
        start = time.perf_counter()
        for seed in seeds:
            world = World.make(seed, scenario)
            for budget in budgets:
                for config in configs:
                    rows.append(run(world, budget, config))
        print(f"{scenario.name}: {len(seeds)} worlds × {len(budgets)} budgets × {len(configs)} policies ({time.perf_counter()-start:.1f}s)", flush=True)
    return rows


def rank(rows):
    names = sorted({r["policy"] for r in rows})
    return sorted([dict(name=n, mean_completed=statistics.mean(r["completed"] for r in rows if r["policy"] == n),
                        mean_spent=statistics.mean(r["spent"] for r in rows if r["policy"] == n)) for n in names],
                  key=lambda r: (-r["mean_completed"], r["mean_spent"], r["name"]))


def development(output, seeds):
    scenarios = [s for s in SCENARIOS if not s.holdout]
    candidates = base_candidates()
    rows = evaluate(candidates, seeds, scenarios)
    write_csv(output / "development.csv", rows)
    ranking = rank(rows)
    selected = []
    for arm in ("round_robin", "fixed_blocks", "single", "explore_commit", "ucb", "salary", "salary_milestones"):
        valid = [c for c in candidates if c["name"] == arm or
                 (arm == "salary" and c["kind"] == "salary" and not c["milestones"]) or
                 (arm == "salary_milestones" and c.get("milestones", False)) or
                 (arm not in ("salary", "salary_milestones") and c["kind"] == arm)]
        best = next(r["name"] for r in ranking if r["name"] in {c["name"] for c in valid})
        cfg = next(c.copy() for c in candidates if c["name"] == best)
        cfg["name"] = arm
        selected.append(cfg)
    control_kinds = {"round_robin", "fixed_blocks", "single", "explore_commit", "ucb"}
    primary_candidate = next(r["name"] for r in ranking if next(c for c in candidates if c["name"] == r["name"])["kind"] in control_kinds)
    primary_control = next(c for c in candidates if c["name"] == primary_candidate)["kind"]
    write_json(output / "development_summary.json", dict(ranking=ranking, selected=selected,
                                                       primary_control=primary_control, seeds=seeds,
                                                       protocol_sha256=sha(ROOT / "PROTOCOL.md"), design_hashes=design_hashes(), source_hashes=source_hashes()))
    print(json.dumps(dict(primary_control=primary_control, top=ranking[:5]), indent=2), flush=True)


def freeze(output, seeds):
    baseline = json.loads((output / "development_summary.json").read_text())
    assert baseline["seeds"] == seeds, "Baseline and revision must use the same declared development seeds"
    assert baseline["protocol_sha256"] == sha(ROOT / "PROTOCOL.md")
    assert baseline["design_hashes"] == design_hashes(), "Design amendments changed; rerun development"
    for file in ("economy/simulator.py", "economy/policies.py", "economy/experiment.py"):
        assert baseline["source_hashes"][file] == source_hashes()[file], "Rerun development after implementation changes"
    candidates = revised_candidates()
    rows = evaluate(candidates, seeds, [s for s in SCENARIOS if not s.holdout])
    write_csv(output / "revision_development.csv", rows)
    ranking = rank(rows)
    winner = next(c.copy() for c in candidates if c["name"] == ranking[0]["name"])
    winner["name"] = "revised"
    selected = baseline["selected"] + [winner]
    selected += [dict(winner, name="revised_no_memory", memory=False),
                 dict(winner, name="revised_no_lease", lease=1),
                 dict(winner, name="revised_terminal_only", shaping=0., continuity=0.)]
    manifest = dict(configs=selected, primary_control=baseline["primary_control"],
                    development_seeds=seeds, evaluation_seeds=list(range(10000, 10200)),
                    budgets=BUDGETS, scenarios=[s.__dict__ for s in SCENARIOS],
                    revision_ranking=ranking, protocol_sha256=sha(ROOT / "PROTOCOL.md"),
                    design_hashes=design_hashes(), source_hashes=source_hashes())
    write_json(output / "frozen_config.json", manifest)
    (output / "frozen_config.sha256").write_text(sha(output / "frozen_config.json") + "\n")
    print(json.dumps(dict(revised=winner, primary_control=manifest["primary_control"]), indent=2), flush=True)


def test(output, limit=None):
    manifest = json.loads((output / "frozen_config.json").read_text())
    assert manifest["source_hashes"] == source_hashes(), "Implementation changed after freeze; freeze again before evaluation"
    assert manifest["protocol_sha256"] == sha(ROOT / "PROTOCOL.md"), "Protocol changed after freeze"
    assert manifest["design_hashes"] == design_hashes(), "Design amendments changed after freeze"
    assert sha(output / "frozen_config.json") == (output / "frozen_config.sha256").read_text().strip()
    seeds = manifest["evaluation_seeds"][:limit]
    assert not set(seeds).intersection(manifest["development_seeds"])
    rows = evaluate(manifest["configs"], seeds, SCENARIOS)
    write_csv(output / ("evaluation.csv" if limit is None else "evaluation_smoke.csv"), rows)
    traces = [run(World.make(seeds[0], s), 80, c, record=True) for s in SCENARIOS for c in manifest["configs"]]
    write_json(output / "traces.json", traces)
    print(f"Saved {len(rows):,} paired evaluation runs", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("develop", "freeze", "evaluate"))
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    seeds = list(range(4 if args.smoke else 40))
    if args.stage == "develop": development(args.output, seeds)
    elif args.stage == "freeze": freeze(args.output, seeds)
    else: test(args.output, 4 if args.smoke else None)


if __name__ == "__main__":
    main()

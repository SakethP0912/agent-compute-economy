"""Analyze complete held-out runs with a paired project-seed block bootstrap.

No third-party dependencies. These costs are synthetic compute credits.
Run: python -m economy.analyze --results results
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

ROOT = Path(__file__).resolve().parents[1]
RESAMPLES = 2000
BOOTSTRAP_SEED = 734921
POLICY_ORDER = (
    "round_robin", "fixed_blocks", "single", "explore_commit", "ucb", "salary",
    "salary_milestones", "revised", "revised_no_memory",
    "revised_no_lease", "revised_terminal_only",
)
LABELS = {
    "round_robin": "Equal turns", "fixed_blocks": "Fixed blocks",
    "single": "Single worker", "ucb": "Adaptive UCB",
    "explore_commit": "Explore then greedy",
    "salary": "Completion salary", "salary_milestones": "Milestone salary",
    "revised": "Revised scheduler", "revised_no_memory": "Revised: no memory",
    "revised_no_lease": "Revised: no lease",
    "revised_terminal_only": "Revised: completion only",
}
NUMERIC_FIELDS = ("completed", "spent", "unused", "steps", "switches", "resets", "overhead", "pruned")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values, q):
    """Linearly interpolated percentile; callers pass sorted finite values."""
    if not values:
        return None
    position = (len(values) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def interval(values):
    ordered = sorted(values)
    return [percentile(ordered, .025), percentile(ordered, .975)] if ordered else None


def load_evaluation(output):
    manifest_path = output / "frozen_config.json"
    data_path = output / "evaluation.csv"
    manifest = json.loads(manifest_path.read_text())
    expected_hash_path = output / "frozen_config.sha256"
    if expected_hash_path.exists() and digest(manifest_path) != expected_hash_path.read_text().strip():
        raise ValueError("Frozen configuration checksum does not match")
    configs = manifest["configs"]
    names = [c["name"] for c in configs]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate policy names in frozen configuration")
    primary_control = manifest["primary_control"]
    if primary_control not in names or "revised" not in names or "salary" not in names:
        raise ValueError("Primary control, revised policy, and salary policy must be present")
    scenarios = {s["name"]: bool(s.get("holdout", False)) for s in manifest["scenarios"]}
    seeds = sorted(manifest["evaluation_seeds"])
    budgets = sorted(float(b) for b in manifest["budgets"])
    if len(seeds) != len(set(seeds)) or len(budgets) != len(set(budgets)):
        raise ValueError("Frozen seeds and budgets must be unique")
    if set(seeds).intersection(manifest["development_seeds"]):
        raise ValueError("Evaluation seeds overlap development seeds")
    rows, seen = [], set()
    with data_path.open(newline="") as stream:
        for raw in csv.DictReader(stream):
            row = {"seed": int(raw["seed"]), "scenario": raw["scenario"],
                   "budget": float(raw["budget"]), "policy": raw["policy"],
                   "holdout": raw["holdout"].lower() == "true"}
            if raw["holdout"].lower() not in ("true", "false"):
                raise ValueError("Invalid holdout indicator")
            row.update({key: float(raw[key]) for key in NUMERIC_FIELDS})
            if not all(math.isfinite(row[key]) and row[key] >= 0 for key in NUMERIC_FIELDS):
                raise ValueError("Nonfinite or negative metric")
            if row["seed"] not in seeds or row["scenario"] not in scenarios or row["budget"] not in budgets or row["policy"] not in names:
                raise ValueError("Evaluation row falls outside frozen experimental grid")
            if row["holdout"] != scenarios[row["scenario"]]:
                raise ValueError("Row and frozen scenario disagree about structural holdout")
            if row["completed"] > 20 or row["completed"] != int(row["completed"]):
                raise ValueError("Completed count must be an integer from 0 to 20")
            if abs(row["spent"] + row["unused"] - row["budget"]) > 1e-6 or row["overhead"] > row["spent"] + 1e-6:
                raise ValueError("Invalid all-in budget accounting")
            key = (row["seed"], row["scenario"], row["budget"], row["policy"])
            if key in seen:
                raise ValueError(f"Duplicate evaluation cell: {key}")
            seen.add(key)
            rows.append(row)
    expected_count = len(seeds) * len(scenarios) * len(budgets) * len(names)
    if len(rows) != expected_count:
        raise ValueError(f"Incomplete evaluation grid: expected {expected_count:,} rows, got {len(rows):,}")
    if len(seeds) < 2:
        raise ValueError("At least two independent seeds are needed for paired analysis")
    names = [n for n in POLICY_ORDER if n in names] + sorted(set(names).difference(POLICY_ORDER))
    return manifest, rows, names, scenarios, seeds, budgets


def bootstrap_weights(count):
    rng = random.Random(BOOTSTRAP_SEED)
    result = []
    for _ in range(RESAMPLES):
        weights = [0] * count
        for _ in range(count):
            weights[rng.randrange(count)] += 1
        result.append([(i, w) for i, w in enumerate(weights) if w])
    return result


def policy_summary(rows):
    totals = {key: math.fsum(r[key] for r in rows) for key in NUMERIC_FIELDS}
    count = len(rows)
    completed = totals["completed"]
    spent = totals["spent"]
    return {
        "runs": count,
        **{f"mean_{key}": value / count for key, value in totals.items()},
        "total_completed": int(completed), "total_spent": spent,
        "cost_per_completion": spent / completed if completed > 0 else None,
        "overhead_share": totals["overhead"] / spent if spent > 0 else None,
        "zero_completion_rate": sum(r["completed"] == 0 for r in rows) / count,
        "full_project_rate": sum(r["completed"] == 20 for r in rows) / count,
    }


def comparison(treatment, control, means, boot, confirmatory=False):
    treatment_mean, control_mean = means[treatment], means[control]
    diffs = [t - c for t, c in zip(boot[treatment], boot[control])]
    gains = [t / c - 1 for t, c in zip(boot[treatment], boot[control]) if c > 0]
    return {
        "treatment": treatment, "control": control,
        "status": "prespecified primary" if confirmatory else "exploratory",
        "mean_difference": treatment_mean - control_mean,
        "difference_ci95": interval(diffs),
        "relative_gain": treatment_mean / control_mean - 1 if control_mean > 0 else None,
        "relative_gain_ci95": interval(gains),
        "ratio_valid_resamples": len(gains), "resamples": RESAMPLES,
    }


def summarize_group(rows, names, seeds, weights, primary_control, primary=False):
    by_policy = {name: [] for name in names}
    by_policy_seed = {name: {seed: [] for seed in seeds} for name in names}
    for row in rows:
        by_policy[row["policy"]].append(row)
        by_policy_seed[row["policy"]][row["seed"]].append(row["completed"])
    summaries = {name: policy_summary(by_policy[name]) for name in names}
    # Each independent seed contributes one equal-weight mean across all selected
    # scenario/budget cells. Resampling individual rows would inflate precision.
    seed_means = {name: [statistics.fmean(by_policy_seed[name][seed]) for seed in seeds] for name in names}
    count = len(seeds)
    boot = {
        name: [sum(seed_means[name][i] * w for i, w in draw) / count for draw in weights]
        for name in names
    }
    means = {name: statistics.fmean(seed_means[name]) for name in names}
    pairs = [("revised", primary_control), ("salary", primary_control), ("revised", "salary")]
    pairs += [("salary_milestones", primary_control)] if "salary_milestones" in names else []
    pairs += [("revised", name) for name in ("revised_no_memory", "revised_no_lease", "revised_terminal_only") if name in names]
    comparisons = [comparison(t, c, means, boot, primary and i == 0) for i, (t, c) in enumerate(pairs)]
    for name in names:
        summaries[name]["mean_completed_ci95"] = interval(boot[name])
    return {"seed_blocks": count, "rows": len(rows), "policies": summaries, "comparisons": comparisons}


def build_analysis(output):
    manifest, rows, names, scenarios, seeds, budgets = load_evaluation(output)
    weights = bootstrap_weights(len(seeds))
    scopes = [
        ("all", "All 12 scenarios", set(scenarios)),
        ("development_families", "Development families · held-out seeds", {s for s, holdout in scenarios.items() if not holdout}),
        ("structural_holdouts", "Structural holdouts", {s for s, holdout in scenarios.items() if holdout}),
    ]
    scopes[0] = ("all", f"All {len(scenarios)} scenarios", set(scenarios))
    scopes += [(f"scenario:{name}", name.replace("_", " ").title(), {name}) for name in scenarios]
    groups = {}
    for scope, label, members in scopes:
        if not members:
            continue
        scope_rows = [r for r in rows if r["scenario"] in members]
        for budget in [None] + budgets:
            selected = scope_rows if budget is None else [r for r in scope_rows if r["budget"] == budget]
            key = f"{scope}|{'all' if budget is None else format(budget, 'g')}"
            group = summarize_group(selected, names, seeds, weights, manifest["primary_control"], key == "all|all")
            group.update(scope=scope, scope_label=label, budget=budget, scenarios=sorted(members),
                         cells_per_seed=len(members) * (len(budgets) if budget is None else 1))
            groups[key] = group
        print(f"Analyzed {label}", flush=True)
    return {
        "schema_version": 1,
        "experiment": "Synthetic compute allocation; no model API calls",
        "metadata": {
            "evaluation_sha256": digest(output / "evaluation.csv"),
            "frozen_config_sha256": digest(output / "frozen_config.json"),
            "analysis_source_sha256": digest(Path(__file__)),
            "total_runs": len(rows), "independent_seed_blocks": len(seeds),
            "evaluation_seeds": seeds, "budgets": budgets, "scenario_count": len(scenarios),
            "policies": names, "primary_control": manifest["primary_control"],
            "policy_configs": manifest["configs"], "bootstrap_resamples": RESAMPLES,
            "bootstrap_seed": BOOTSTRAP_SEED, "interval_method": "paired seed-block percentile bootstrap, 95%",
            "primary_estimand": "Equal-weight mean completed-task difference across the frozen scenario × budget cells",
            "scope_warning": "The stress-test mixture is chosen by the experimenters; it is not a customer population.",
            "cost_unit": "synthetic compute credits; not measured tokens or dollars",
            "cost_per_completion": "Sum of all run spending divided by sum of completions, including spending from zero-completion runs",
            "relative_gain": "Ratio of paired aggregate completion means minus one; resamples with zero control mean are excluded and counted",
        },
        "labels": LABELS,
        "scenarios": manifest["scenarios"],
        "scopes": [{"id": key, "label": label} for key, label, members in scopes if members],
        "groups": groups,
    }


def fmt(value, digits=2, signed=False):
    if value is None:
        return "n/a"
    return format(value, f"{'+' if signed else ''}.{digits}f")


def ci_text(ci, percent=False):
    if ci is None:
        return "n/a"
    scale = 100 if percent else 1
    return f"[{fmt(ci[0] * scale)}, {fmt(ci[1] * scale)}]" + ("%" if percent else "")


def effect_text(item):
    return f"{fmt(item['mean_difference'], signed=True)} ({ci_text(item['difference_ci95'])})"


def outcome_sentence(item):
    low, high = item["difference_ci95"]
    if low > 0:
        return "The interval favors the revised scheduler within this synthetic mixture."
    if high < 0:
        return "The interval favors the development-selected control within this synthetic mixture."
    return "The interval includes no difference; this experiment does not resolve an aggregate advantage."


def markdown_report(data):
    meta, groups = data["metadata"], data["groups"]
    primary = groups["all|all"]["comparisons"][0]
    control = meta["primary_control"]
    lines = [
        "# Synthetic compute economy: held-out analysis", "",
        f"**Primary result:** revised minus `{control}` = {effect_text(primary)} completed tasks per project; 95% paired percentile interval. " + outcome_sentence(primary), "",
        f"Relative completion gain: {fmt(None if primary['relative_gain'] is None else 100 * primary['relative_gain'], signed=True)}%; 95% interval {ci_text(primary['relative_gain_ci95'], True)}.", "",
        "This is a synthetic allocation experiment. No language model API was called. Compute credits are modeled units, not measured tokens, dollar savings, or wall-clock speedups. The result concerns the chosen simulator assumptions and stress-test mixture.", "",
        "## Design and analysis", "",
        f"- {meta['total_runs']:,} runs; {meta['independent_seed_blocks']} independent project seeds; {meta['scenario_count']} scenarios; {len(meta['budgets'])} budgets; {len(meta['policies'])} frozen policies.",
        f"- The primary control, `{control}`, was selected using development data before evaluation. It was not selected by held-out performance.",
        f"- Each seed is averaged equally across the selected scenario × budget cells before resampling. All policies use the same {RESAMPLES:,} paired seed-block bootstrap samples, generated with seed {BOOTSTRAP_SEED}.",
        "- Only revised versus the selected control over all scenarios/budgets is the prespecified primary comparison. Other intervals are exploratory and are not adjusted for multiple comparisons.",
        "- Cost per completion is total spending divided by total completions. Spending on zero-completion runs remains in the numerator. A zero total completion denominator is reported as n/a.",
        "- Relative gains use the ratio of aggregate means. Zero-denominator bootstrap resamples are omitted and their valid count is stored in analysis.json.", "",
        "Before held-out evaluation, the documented audit strengthened UCB with continuation leases, added an explore-commit control and a shared-progress null scenario, and removed both progress shaping and continuity preference from the completion-only ablation. These amendments are recorded in [DEVELOPMENT_LOG.md](../DEVELOPMENT_LOG.md). Controls and revision were frozen after rerunning development.", "",
        "## Every policy, equal-weight aggregate", "",
        "| Policy | Mean completed / 20 | 95% interval | Mean spent | Credits / completion | Overhead | Zero-completion runs |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in meta["policies"]:
        row = groups["all|all"]["policies"][name]
        lines.append(f"| `{name}` | {fmt(row['mean_completed'])} | {ci_text(row['mean_completed_ci95'])} | {fmt(row['mean_spent'])} | {fmt(row['cost_per_completion'])} | {fmt(100 * row['overhead_share'])}% | {fmt(100 * row['zero_completion_rate'])}% |")
    lines += ["", "## Development families and structural holdouts", "",
              "All rows below use new evaluation seeds. The structural scenarios were also excluded from parameter selection.", "",
              "| Scope | Revised mean | Selected control mean | Revised − control (95% interval) | Relative gain (95% interval) |",
              "|---|---:|---:|---:|---:|"]
    for scope in ("all", "development_families", "structural_holdouts"):
        group = groups[f"{scope}|all"]
        c = group["comparisons"][0]
        gain = None if c["relative_gain"] is None else c["relative_gain"] * 100
        lines.append(f"| {group['scope_label']} | {fmt(group['policies']['revised']['mean_completed'])} | {fmt(group['policies'][control]['mean_completed'])} | {effect_text(c)} | {fmt(gain, signed=True)}% ({ci_text(c['relative_gain_ci95'], True)}) |")
    lines += ["", "## Mechanism comparisons and ablations", "",
              "Positive values favor the treatment listed first. These comparisons are exploratory.", "",
              "| Treatment | Comparator | Completed-task difference (95% interval) | Relative gain |",
              "|---|---|---:|---:|"]
    for c in groups["all|all"]["comparisons"][1:]:
        lines.append(f"| `{c['treatment']}` | `{c['control']}` | {effect_text(c)} | {fmt(None if c['relative_gain'] is None else c['relative_gain'] * 100, signed=True)}% |")
    lines += ["", "## Each scenario and budget", "",
              "This table compares the frozen revised policy with the development-selected control. Complete means and costs for every policy in each cell are in [report.html](report.html) and [analysis.json](analysis.json). Intervals here are exploratory.", "",
              "| Scenario | Holdout family? | Budget | Revised mean | Control mean | Difference (95% interval) | Revised credits / completion | Control credits / completion |",
              "|---|---|---:|---:|---:|---:|---:|---:|"]
    for scenario in data["scenarios"]:
        for budget in meta["budgets"]:
            group = groups[f"scenario:{scenario['name']}|{budget:g}"]
            t, c = group["policies"]["revised"], group["policies"][control]
            lines.append(f"| {scenario['name']} | {'Yes' if scenario.get('holdout') else 'No'} | {budget:g} | {fmt(t['mean_completed'])} | {fmt(c['mean_completed'])} | {effect_text(group['comparisons'][0])} | {fmt(t['cost_per_completion'])} | {fmt(c['cost_per_completion'])} |")
    lines += ["", "## Interpretation boundaries", "",
              "Salary redistribution conserves the spending pool. Extra credits do not train worker model weights. If the revised conventional scheduler improves, that supports allocation changes; it does not establish that a currency mechanism is necessary.", "",
              "The memory ablation changes the simulator's explicit handoff/compaction behavior. Any gain is conditional on those assumed costs and retention rules. It does not measure the effectiveness of real summarization or retrieval.", "",
              "Outside the shared-progress null, workers have separate partial solutions and competing partial work is discarded after task completion. Public feedback can reveal useful progress. This structure makes concentration potentially valuable, so continuation-capable controls are necessary. Offline parameter-search costs are not charged to each evaluated project; candidate counts differ by policy family.", "",
              "A real-model validation should retain the same held-out tasks, full cost accounting, independently checked outcomes, repeated seeds, and strong adaptive controls. Prior art and product hypotheses are documented in [research_sources.md](../research_sources.md).", "",
              "## Reproducibility", "",
              "Run `python -m economy.analyze --results results` after the frozen evaluation. The analyzer checks that the CSV contains the complete frozen seed × scenario × budget × policy grid and validates budget accounting.", "",
              f"- Evaluation SHA-256: `{meta['evaluation_sha256']}`",
              f"- Frozen configuration SHA-256: `{meta['frozen_config_sha256']}`",
              f"- Analysis implementation SHA-256: `{meta['analysis_source_sha256']}`", ""]
    return "\n".join(lines)


HTML_TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent compute economy · experiment results</title>
<style>
:root{color-scheme:light;--ink:#172a38;--muted:#526475;--line:#dce4e9;--bg:#f3f6f8;--green:#13796b;--blue:#356fc1;--salary:#b36a40}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:1240px;margin:auto;padding:36px 28px 60px}h1{font-size:clamp(28px,4vw,44px);line-height:1.15;letter-spacing:-.04em;margin:8px 0 16px}h2{font-size:21px;line-height:1.3;margin:0 0 14px}h3{font-size:15px;margin:0 0 10px}.eyebrow{text-transform:uppercase;letter-spacing:.12em;color:var(--green);font-size:12px;font-weight:800}.lead{max-width:880px;font-size:17px;color:var(--muted);margin:0 0 20px}.notice{border-left:4px solid var(--salary);background:#fff7ef;padding:13px 18px;border-radius:0 9px 9px 0;margin-bottom:24px}.primary{background:#153c42;color:white;padding:25px;border-radius:16px;margin:24px 0}.primary p{color:#d5e6e8;margin-bottom:0}.primary strong{font-size:32px;letter-spacing:-.02em}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:20px 0}.card,.panel{background:white;border:1px solid var(--line);border-radius:13px;padding:20px}.card span{display:block;font-size:12px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}.card b{display:block;font-size:24px;margin-top:5px}.card small{display:block;color:var(--muted);line-height:1.4}.filters{display:flex;gap:18px;align-items:end;flex-wrap:wrap;margin-bottom:18px}label{display:flex;flex-direction:column;gap:5px;color:var(--muted);font-size:13px}select{font:inherit;color:var(--ink);border:1px solid #b7c6cf;background:white;border-radius:8px;padding:9px 34px 9px 10px;max-width:100%}.grid{display:grid;grid-template-columns:1fr 1.2fr;gap:18px;margin:18px 0}.panel p{margin:8px 0;color:var(--muted)}.small{font-size:12px;color:var(--muted)}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:13px;white-space:nowrap}th,td{padding:11px 10px;border-bottom:1px solid var(--line);text-align:right}th{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}th:first-child,td:first-child{text-align:left}tbody tr:last-child td{border-bottom:0}tr.featured{background:#eaf6f2}tr.control{background:#eef3fa}.badge{font-size:10px;padding:2px 5px;border-radius:4px;background:#dae7ef;display:inline-block;margin-left:6px}.bar-row{display:grid;grid-template-columns:150px 1fr 42px;align-items:center;gap:10px;margin:13px 0;font-size:12px}.bar-track{background:#edf1f4;border-radius:5px;height:15px}.bar{background:#93a5b5;height:100%;border-radius:5px}.bar.revised{background:var(--green)}.bar.control{background:var(--blue)}.bar.salary{background:var(--salary)}.bar-number{text-align:right;font-variant-numeric:tabular-nums}details{margin-top:20px}summary{cursor:pointer;font-weight:700}code{background:#edf2f5;padding:2px 5px;border-radius:4px;font-size:.9em}a{color:#226ba4}footer{margin-top:24px;font-size:13px;color:var(--muted)}.method{display:grid;grid-template-columns:1fr 1fr;gap:24px}.method p{font-size:14px}.interpret{padding:12px;background:#f4f7f9;border-radius:7px}#status{font-size:12px;color:var(--muted);margin:0 0 12px}.hash{overflow-wrap:anywhere;font-family:monospace;font-size:11px}.subtitle{font-size:12px;color:#c2dadd;text-transform:uppercase;letter-spacing:.08em}@media(max-width:850px){.grid,.method{grid-template-columns:1fr}.cards{grid-template-columns:repeat(2,1fr)}main{padding:24px 16px 40px}.bar-row{grid-template-columns:140px 1fr 40px}}@media(max-width:480px){.cards{grid-template-columns:1fr 1fr;gap:9px}.card{padding:13px}.card b{font-size:21px}.panel{padding:16px}.primary{padding:20px}.primary strong{font-size:27px}.filters{display:block}.filters label{margin-bottom:10px}select{width:100%}.bar-row{grid-template-columns:122px 1fr 35px;font-size:11px}}
</style></head><body><main>
<div class="eyebrow">Controlled, repeatable simulation</div><h1>Does an agent economy earn its keep?</h1>
<p class="lead">An allocation experiment with frozen controls, held-out project seeds, and adverse scenarios. Success means verified task completion within a shared budget.</p>
<div class="notice"><b>Scope:</b> these are synthetic compute credits. No LLM API calls, measured token savings, dollar savings, or market-demand measurements are represented here.</div>
<section class="primary"><div class="subtitle">Prespecified primary comparison · all scenarios and budgets</div><h2 id="primary-label"></h2><strong id="primary-effect"></strong><p id="primary-detail"></p></section>
<div class="filters"><label>Scenario scope<select id="scope" aria-label="Scenario scope"></select></label><label>Project budget<select id="budget" aria-label="Project budget"></select></label></div>
<p id="status" aria-live="polite"></p><div class="cards" id="cards"></div>
<div class="grid"><section class="panel"><h2>Verified completions</h2><p class="small">Mean completed tasks per 20-task project. Each scenario × budget cell has equal weight.</p><div id="bars"></div><p class="small">Green: revised scheduler · Blue: selected control · Brown: salary</p></section>
<section class="panel"><h2>Paired comparisons</h2><p class="small">Completed-task differences with 95% seed-block intervals. Positive values favor the first policy.</p><div class="table-wrap"><table><thead><tr><th>Comparison</th><th>Difference</th><th>95% interval</th></tr></thead><tbody id="comparisons"></tbody></table></div><p class="small" id="comparison-note"></p></section></div>
<section class="panel"><h2>All policies, full costs</h2><div class="table-wrap"><table><thead><tr><th>Policy</th><th>Completed</th><th>Mean spent</th><th>Credits / completion</th><th>Overhead</th><th>Zero completions</th><th>Switches</th><th>Resets</th><th>Pruned</th></tr></thead><tbody id="policies"></tbody></table></div><p class="small">Cost per completion = all spending ÷ all completed tasks, including spending from failed runs. Values are not averages restricted to successful runs.</p></section>
<section class="panel" style="margin-top:20px"><h2>What this experiment can establish</h2><div class="method"><div><h3>Mechanism evidence</h3><p>A result supports or weakens an allocation rule under explicitly modeled worker differences, feedback, switching costs, and progress dynamics. New evaluation seeds test repeatability. Structural holdouts test changes absent from tuning.</p><p>Salary balances redistribute an existing budget. They do not create compute or train model weights. If a conventional revised scheduler wins, currency is not shown to be necessary.</p></div><div><h3>What still needs real-world evidence</h3><p>Model behavior, verification reliability, actual memory transfer, API cost, latency, integration effort, and willingness to pay require real workloads. A synthetic benefit is not a commercial forecast.</p><p>Economic survival, bandit allocation, pruning, and memory have prior art. Read the <a href="../research_sources.md">source-backed novelty and product assessment</a>.</p></div></div></section>
<details class="panel"><summary>Statistical method and reproducibility</summary><div id="methods"></div><p>Before evaluation, the <a href="../DEVELOPMENT_LOG.md">documented audit</a> strengthened UCB with continuation leases and added explore-commit and a shared-progress null. Outside that null, worker progress is private and concentration can help by construction. Offline tuning costs and unequal candidate counts are separate from charged online overhead.</p><p><a href="evaluation.csv">Per-run CSV</a> · <a href="analysis.json">Complete analysis JSON</a> · <a href="analysis.md">Written analysis</a> · <a href="frozen_config.json">Frozen policies</a> · <a href="../PROTOCOL.md">Protocol</a></p><div id="hashes" class="hash"></div></details>
<footer>Every frozen arm and scenario is retained. Only the prespecified aggregate revised-versus-selected-control interval is primary; the other intervals are exploratory, without multiple-comparison adjustment.</footer>
</main><script id="result-data" type="application/json">__DATA__</script><script>
'use strict';
const D=JSON.parse(document.getElementById('result-data').textContent), M=D.metadata;
const $=id=>document.getElementById(id), esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const f=(v,d=2)=>v==null?'n/a':v.toFixed(d), sign=v=>v==null?'n/a':(v>=0?'+':'')+f(v), pct=v=>v==null?'n/a':f(v*100)+'%', ci=a=>a?'['+f(a[0])+', '+f(a[1])+']':'n/a', label=n=>D.labels[n]||n;
const primary=D.groups['all|all'].comparisons[0];
$('primary-label').textContent=label('revised')+' vs '+label(M.primary_control);
$('primary-effect').textContent=sign(primary.mean_difference)+' completed tasks';
const verdict=primary.difference_ci95[0]>0?'The interval favors the revised scheduler in this mixture.':primary.difference_ci95[1]<0?'The interval favors the selected control in this mixture.':'The interval includes no difference; an aggregate advantage is unresolved.';
$('primary-detail').textContent='95% interval '+ci(primary.difference_ci95)+' · Relative gain '+pct(primary.relative_gain)+'. '+verdict;
$('scope').innerHTML=D.scopes.map(s=>'<option value="'+esc(s.id)+'">'+esc(s.label)+'</option>').join('');
$('budget').innerHTML='<option value="all">All budgets, equal weight</option>'+M.budgets.map(b=>'<option value="'+b+'">'+b+' credits</option>').join('');
function render(){
 const key=$('scope').value+'|'+$('budget').value,g=D.groups[key],r=g.policies.revised,c=g.policies[M.primary_control],comp=g.comparisons[0];
 $('status').textContent=g.scope_label+' · '+g.seed_blocks+' independent seeds · '+g.cells_per_seed+' cells per seed · '+g.rows.toLocaleString()+' runs · '+(key==='all|all'?'Primary scope':'Exploratory scope');
 const cards=[['Revised completions',f(r.mean_completed),'out of 20 tasks per project'],['Control completions',f(c.mean_completed),label(M.primary_control)],['Paired difference',sign(comp.mean_difference),'95% interval '+ci(comp.difference_ci95)],['Revised unit cost',f(r.cost_per_completion),'synthetic credits per completion']];
 $('cards').innerHTML=cards.map(x=>'<div class="card"><span>'+esc(x[0])+'</span><b>'+esc(x[1])+'</b><small>'+esc(x[2])+'</small></div>').join('');
 const max=Math.max(1,...M.policies.map(p=>g.policies[p].mean_completed));
 $('bars').innerHTML=M.policies.map(p=>'<div class="bar-row"><span>'+esc(label(p))+'</span><div class="bar-track" role="img" aria-label="'+esc(label(p)+': '+f(g.policies[p].mean_completed)+' mean completions')+'"><div class="bar '+(p==='revised'?'revised':p===M.primary_control?'control':p==='salary'?'salary':'')+'" style="width:'+(g.policies[p].mean_completed/max*100).toFixed(2)+'%"></div></div><span class="bar-number">'+f(g.policies[p].mean_completed)+'</span></div>').join('');
 $('comparisons').innerHTML=g.comparisons.map(x=>'<tr><td>'+esc(label(x.treatment))+'<br><span class="small">vs '+esc(label(x.control))+'</span></td><td>'+sign(x.mean_difference)+'</td><td>'+ci(x.difference_ci95)+'</td></tr>').join('');
 $('comparison-note').textContent=key==='all|all'?'Only the first comparison is primary; all other rows are exploratory.':'All comparisons in this selected slice are exploratory.';
 $('policies').innerHTML=M.policies.map(p=>{const x=g.policies[p];return '<tr class="'+(p==='revised'?'featured':p===M.primary_control?'control':'')+'"><td>'+esc(label(p))+(p===M.primary_control?'<span class="badge">CONTROL</span>':'')+'</td><td title="95% interval '+ci(x.mean_completed_ci95)+'">'+f(x.mean_completed)+'</td><td>'+f(x.mean_spent)+'</td><td>'+f(x.cost_per_completion)+'</td><td>'+pct(x.overhead_share)+'</td><td>'+pct(x.zero_completion_rate)+'</td><td>'+f(x.mean_switches)+'</td><td>'+f(x.mean_resets)+'</td><td>'+f(x.mean_pruned)+'</td></tr>';}).join('');
}
$('scope').addEventListener('change',render);$('budget').addEventListener('change',render);
$('methods').innerHTML='<p>'+M.total_runs.toLocaleString()+' runs from '+M.independent_seed_blocks+' independent project seeds. The same seeds recur across scenarios, budgets, and policies; rows are therefore not treated as independent observations.</p><p>For each scope, first average every seed across its scenario × budget cells. Resample these paired seed blocks '+M.bootstrap_resamples.toLocaleString()+' times with fixed RNG seed '+M.bootstrap_seed+'. Report the 2.5th and 97.5th percentiles using linear interpolation.</p><p>The control <code>'+esc(M.primary_control)+'</code> was selected on development data. Development-family results here still use held-out seeds. Structural holdout scenarios were excluded from tuning. The full mixture is equally weighted and does not represent measured customer demand.</p><p>Ratio intervals use the ratio of paired aggregate means; zero-denominator draws are excluded and counted in JSON. The input loader rejects duplicate cells, incomplete frozen grids, nonfinite metrics, and inconsistent budget accounting.</p>';
$('hashes').textContent='Evaluation SHA-256: '+M.evaluation_sha256+' | Frozen configuration SHA-256: '+M.frozen_config_sha256;
render();
</script></body></html>'''


def html_report(data):
    # Escape characters that can end an HTML script element in JSON strings.
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return HTML_TEMPLATE.replace("__DATA__", payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", "--output", dest="output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    data = build_analysis(args.output)
    (args.output / "analysis.json").write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (args.output / "analysis.md").write_text(markdown_report(data))
    (args.output / "report.html").write_text(html_report(data))
    primary = data["groups"]["all|all"]["comparisons"][0]
    print(f"Primary revised − {data['metadata']['primary_control']}: {effect_text(primary)}", flush=True)
    print(f"Wrote analysis.json, analysis.md, and report.html under {args.output}", flush=True)


if __name__ == "__main__":
    main()

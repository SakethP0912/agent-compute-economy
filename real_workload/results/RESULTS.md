# Offline executable workload results

Actual finite-domain program synthesis, not an LLM benchmark.

Original protocol SHA-256: `2b61095e08ece763dcb1001be5aa767ec70ffdd9ff358957eec685d8ba9c9af9`

Analysis correction after independent review: intervals now resample whole seed clusters, retaining all four families and policy pairs. Original task-level intervals are superseded. No raw outcomes or allocation rules changed. See `../ANALYSIS_ADDENDUM.md`; original artifacts are retained alongside this report.

| Policy | Solved / tasks | Success rate | Median discovery cost, successful tasks only | Aggregate operations / solved task, including failures |
|---|---:|---:|---:|---:|
| equal | 15 / 48 | 31.2% | 25790 | 382,728.8 |
| random | 14 / 48 | 29.2% | 23154.0 | 410,274.6 |
| salary | 20 / 48 | 41.7% | 33699.5 | 287,137.2 |
| cost_ucb | 15 / 48 | 31.2% | 24249 | 382,712.9 |
| explore_commit | 23 / 48 | 47.9% | 47525 | 249,948.7 |

Aggregate operations include all charged work, including failed runs and work after discovery in successful runs. This is not a stop-on-success deployment estimate.

## Paired salary comparisons

Win/tie/loss refers to correctness within budget, not speed. Bootstrap resampling uses the seed as the independent unit and retains all four families per sampled seed.

- Versus equal: 5 wins, 43 ties, 0 losses; success difference +10.42 percentage points, descriptive paired seed-cluster bootstrap interval [+2.08, +20.83] percentage points (12 seed clusters).
- Versus random: 6 wins, 42 ties, 0 losses; success difference +12.50 percentage points, descriptive paired seed-cluster bootstrap interval [+4.17, +22.92] percentage points (12 seed clusters).
- Versus cost_ucb: 5 wins, 43 ties, 0 losses; success difference +10.42 percentage points, descriptive paired seed-cluster bootstrap interval [+2.08, +20.83] percentage points (12 seed clusters).
- Versus explore_commit: 4 wins, 37 ties, 7 losses; success difference -6.25 percentage points, descriptive paired seed-cluster bootstrap interval [-20.83, +10.42] percentage points (12 seed clusters).

## Limits

Targets are sampled from the workers' known finite grammar. Family-specialized enumerators are a constructed allocation problem, not general-purpose agents. The full finite domain is exhaustively verified, but correctness beyond it is untested. Heldout observations never feed scheduling or stopping. All runs spend their available budget regardless of discovery; cost to first success is an offline diagnostic. A salary outcome depends on this specific reward and reallocation rule. Cost-UCB and explore-commit are simple untuned adaptive controls, not optimal algorithms. Operation accounting excludes scheduling, expression construction, reference construction, and Python constant-factor execution overhead. This does not estimate dollars, tokens, latency, learning, or LLM quality. Successful-task cost conditions on different success sets and is not a standalone policy ranking. Only 12 seed clusters are available in the default run; intervals are exploratory descriptions of this small constructed suite. Null and losing comparisons are retained.

Recorded execution wall time: 2.237 seconds (diagnostic only).

Execution implementation SHA-256: `f7e5ef33e92502a5f4bae7626e12f0bf81c2ea2b1745ceb015eea74d651b98b6`

Analysis implementation SHA-256: `e46835736fe3f16f374862266706ca7e1c19efdba6ce4ec13b4e3897e358450a`

Execution deviations: none. Analysis-only correction is disclosed above.

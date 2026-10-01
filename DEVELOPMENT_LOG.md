# Development and audit log

## Before held-out evaluation

The original protocol and initial candidate families were written before running development. The revised scheduler family (continuation leases, uncertainty, discounting, and a public-progress preference) was proposed before observing development outcomes; it was not invented after seeing evaluation data.

The first development batch used seeds 0–39, eight scenarios, three budgets, and 23 candidate configurations (22,080 runs). It is preserved in `results/preliminary_development.csv` and its summary. UCB with exploration 0.05 was the best control on the registered aggregate (9.711 completed tasks/project); the strongest milestone salary candidate scored 9.416. In the specialist scenario, that milestone salary candidate scored 6.692 while UCB scored 12.967. This suggested that permanent elimination discarded workers useful to later task types. These are exploratory development observations.

An independent reviewer requested: (1) a clean no-progress ablation, (2) provenance checks between baseline development and freezing, (3) an actual null scenario, and (4) explicit disclosure that private trajectories and informative progress favor continuity.

Before any held-out run, we made the following declared protocol amendments:

- Strengthened the UCB control by tuning continuation leases of 1, 4, and 8, so continuation is not reserved for the proposed revision. Added a two-parameter explore-commit control based on public task progress. The primary control remains selected only on development outcomes.
- Added `shared_progress_null` as a fifth structural holdout. All workers have equal cost and productivity, progress is fully shared, switching/compaction impose no cost, and work draws depend on total task attempts. With equal controller overhead, changing worker choices cannot alter the work trajectory. Extra bookkeeping should not help.
- Aligned revision exploration candidates with the control (0.05, 0.2, 0.5). The revision additionally tests discounting and public-progress preference. No evaluation outcomes were available for these choices.
- Set both shaping and continuity preference to zero in `revised_terminal_only`.
- Required development seed and behavioral-source hash agreement before freezing. All development is rerun after these changes, with previous results preserved.

The final simulator has **13 scenarios, 11 frozen arms, three budgets, and 200 held-out seed blocks**: 85,800 evaluation runs. All13 remains the equal-weight primary mixture. This mixture was amended before evaluation and is not a population estimate. Primary uncertainty resamples 200 seed blocks, not 85,800 rows.

The baseline family, environment assumptions, and revision search are all engineering choices. The number of candidate configurations differs across model families; this study does not claim equal hyperparameter-search compute. It charges online controller costs, while offline tuning cost is reported separately as run counts.

## Structural limits

Outside the explicit null, workers maintain private partial solutions. Completing a task discards other workers' partial work. Public scores are noisy or misleading proxies for true fractional progress; solutions and tasks are sequential. Consequently, concentrating compute can help by construction. Strong fixed-worker and continuation-capable controls are necessary to avoid calling that structural effect a currency benefit. The memory advantage is also stipulated in the cost and state-loss model, not an empirical discovery.

No configured API key or running local model was available. These experiments execute local code only. They do not measure LLM behavior, tokens, API spend, throughput, or wall-clock parallel speedups.

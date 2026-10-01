# Exploratory equal-controller-cost sensitivity

This post-hoc sensitivity uses fresh seeds to test an assumed bookkeeping cost. It does not replace the frozen primary experiment.

All four policies pay 0.04 modeled credits per action for controller bookkeeping. All other costs, rules, and frozen configurations remain unchanged.

15,600 runs: 100 independent paired seed blocks, 13 scenarios, three budgets, four policies. Intervals use 2,000 paired seed-block resamples. Synthetic credits are not dollars or LLM tokens.

- ucb: 8.906667 completed tasks/project; 10.0410 modeled credits/completion.
- salary: 8.092051 completed tasks/project; 11.1945 modeled credits/completion.
- salary_milestones: 9.044615 completed tasks/project; 9.8839 modeled credits/completion.
- revised: 7.980769 completed tasks/project; 11.3938 modeled credits/completion.

## Paired comparisons against UCB

- salary: -0.814615 tasks/project, 95% interval [-0.918212, -0.714609]; relative difference -9.146%, interval [-10.244%, -8.069%].
- salary_milestones: +0.137949 tasks/project, 95% interval [+0.048455, +0.226929]; relative difference +1.549%, interval [+0.542%, +2.558%].
- revised: -0.925897 tasks/project, 95% interval [-0.980532, -0.870763]; relative difference -10.396%, interval [-10.967%, -9.784%].

## Per-budget relative differences

- 40 credits: salary -30.396%; salary_milestones -4.178%; revised -20.288%.
- 80 credits: salary -11.848%; salary_milestones +3.560%; revised -16.527%.
- 160 credits: salary -3.563%; salary_milestones +1.738%; revised -5.457%.

## Interpretation limits

Controller costs in both the original experiment and this sensitivity are assumptions. Equalizing them tests robustness to that assumption; it does not establish the actual overhead of any implementation. New seeds differ from the original evaluation, so the difference between these two reported effect sizes is not a paired causal estimate of the fee change. The main all-in experiment and this sensitivity must both be retained.

All comparisons and subgroup intervals are exploratory, with no family-wise coverage guarantee. The chosen scenario mixture is not a deployment population. A favorable result would not establish LLM performance, market value, or that a currency system is necessary. The shared-progress null has identical completion outcomes across all four policies, as required when controller fees are equal.

Full per-scenario estimates and intervals are in summary.json; individual runs are in runs.csv.

Reproduce from the project root: `python3 sensitivity/run_sensitivity.py`.

Protocol SHA-256: `4bd63a60a95da72272bbde7a81ad070886a0b0a1d5a5e9a48f405b92278475c2`.

Implementation SHA-256: `b7e57bae8c3c21d29c96bf3bd298a12961f161844b1babf0c7ff3453cf29f41f`.

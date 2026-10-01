# Synthetic compute economy: held-out analysis

**Primary result:** revised minus `ucb` = -1.12 ([-1.16, -1.09]) completed tasks per project; 95% paired percentile interval. The interval favors the development-selected control within this synthetic mixture.

Relative completion gain: -12.60%; 95% interval [-13.00, -12.22]%.

This is a synthetic allocation experiment. No language model API was called. Compute credits are modeled units, not measured tokens, dollar savings, or wall-clock speedups. The result concerns the chosen simulator assumptions and stress-test mixture.

## Design and analysis

- 85,800 runs; 200 independent project seeds; 13 scenarios; 3 budgets; 11 frozen policies.
- The primary control, `ucb`, was selected using development data before evaluation. It was not selected by held-out performance.
- Each seed is averaged equally across the selected scenario × budget cells before resampling. All policies use the same 2,000 paired seed-block bootstrap samples, generated with seed 734921.
- Only revised versus the selected control over all scenarios/budgets is the prespecified primary comparison. Other intervals are exploratory and are not adjusted for multiple comparisons.
- Cost per completion is total spending divided by total completions. Spending on zero-completion runs remains in the numerator. A zero total completion denominator is reported as n/a.
- Relative gains use the ratio of aggregate means. Zero-denominator bootstrap resamples are omitted and their valid count is stored in analysis.json.

Before held-out evaluation, the documented audit strengthened UCB with continuation leases, added an explore-commit control and a shared-progress null scenario, and removed both progress shaping and continuity preference from the completion-only ablation. These amendments are recorded in [DEVELOPMENT_LOG.md](../DEVELOPMENT_LOG.md). Controls and revision were frozen after rerunning development.

## Every policy, equal-weight aggregate

| Policy | Mean completed / 20 | 95% interval | Mean spent | Credits / completion | Overhead | Zero-completion runs |
|---|---:|---:|---:|---:|---:|---:|
| `round_robin` | 4.19 | [4.12, 4.27] | 92.72 | 22.10 | 17.01% | 2.15% |
| `fixed_blocks` | 6.36 | [6.26, 6.46] | 92.72 | 14.57 | 9.45% | 0.36% |
| `single` | 8.68 | [8.41, 8.95] | 90.29 | 10.41 | 5.74% | 1.18% |
| `explore_commit` | 7.03 | [6.96, 7.09] | 92.65 | 13.19 | 13.76% | 1.81% |
| `ucb` | 8.91 | [8.83, 9.00] | 89.38 | 10.03 | 14.98% | 0.13% |
| `salary` | 7.81 | [7.70, 7.91] | 90.82 | 11.63 | 18.26% | 2.08% |
| `salary_milestones` | 8.73 | [8.63, 8.82] | 89.83 | 10.29 | 15.91% | 0.88% |
| `revised` | 7.79 | [7.71, 7.87] | 91.10 | 11.69 | 15.66% | 0.62% |
| `revised_no_memory` | 7.23 | [7.15, 7.32] | 91.73 | 12.68 | 21.08% | 1.04% |
| `revised_no_lease` | 8.75 | [8.66, 8.84] | 89.75 | 10.26 | 16.28% | 1.01% |
| `revised_terminal_only` | 6.52 | [6.41, 6.62] | 92.10 | 14.13 | 16.75% | 1.04% |

## Development families and structural holdouts

All rows below use new evaluation seeds. The structural scenarios were also excluded from parameter selection.

| Scope | Revised mean | Selected control mean | Revised − control (95% interval) | Relative gain (95% interval) |
|---|---:|---:|---:|---:|
| All 13 scenarios | 7.79 | 8.91 | -1.12 ([-1.16, -1.09]) | -12.60% ([-13.00, -12.22]%) |
| Development families · held-out seeds | 8.46 | 9.59 | -1.13 ([-1.17, -1.09]) | -11.79% ([-12.21, -11.38]%) |
| Structural holdouts | 6.73 | 7.84 | -1.11 ([-1.16, -1.06]) | -14.18% ([-14.71, -13.62]%) |

## Mechanism comparisons and ablations

Positive values favor the treatment listed first. These comparisons are exploratory.

| Treatment | Comparator | Completed-task difference (95% interval) | Relative gain |
|---|---|---:|---:|
| `salary` | `ucb` | -1.11 ([-1.20, -1.03]) | -12.43% |
| `revised` | `salary` | -0.01 ([-0.10, 0.07]) | -0.19% |
| `salary_milestones` | `ucb` | -0.18 ([-0.26, -0.12]) | -2.07% |
| `revised` | `revised_no_memory` | +0.56 ([0.54, 0.58]) | +7.75% |
| `revised` | `revised_no_lease` | -0.95 ([-1.00, -0.91]) | -10.91% |
| `revised` | `revised_terminal_only` | +1.27 ([1.21, 1.34]) | +19.53% |

## Each scenario and budget

This table compares the frozen revised policy with the development-selected control. Complete means and costs for every policy in each cell are in [report.html](report.html) and [analysis.json](analysis.json). Intervals here are exploratory.

| Scenario | Holdout family? | Budget | Revised mean | Control mean | Difference (95% interval) | Revised credits / completion | Control credits / completion |
|---|---|---:|---:|---:|---:|---:|---:|
| homogeneous | No | 40 | 2.19 | 2.29 | -0.10 ([-0.19, -0.01]) | 18.12 | 17.29 |
| homogeneous | No | 80 | 5.50 | 5.71 | -0.21 ([-0.33, -0.10]) | 14.46 | 13.92 |
| homogeneous | No | 160 | 13.61 | 13.94 | -0.33 ([-0.48, -0.17]) | 11.73 | 11.45 |
| heterogeneous | No | 40 | 3.28 | 4.60 | -1.32 ([-1.44, -1.20]) | 12.07 | 8.61 |
| heterogeneous | No | 80 | 8.67 | 11.45 | -2.78 ([-2.94, -2.63]) | 9.18 | 6.95 |
| heterogeneous | No | 160 | 19.95 | 20.00 | -0.04 ([-0.09, -0.00]) | 7.01 | 6.17 |
| specialists | No | 40 | 3.52 | 5.34 | -1.82 ([-1.95, -1.71]) | 11.27 | 7.42 |
| specialists | No | 80 | 9.49 | 13.04 | -3.54 ([-3.67, -3.41]) | 8.38 | 6.10 |
| specialists | No | 160 | 20.00 | 20.00 | +0.00 ([0.00, 0.00]) | 6.52 | 5.55 |
| delayed | No | 40 | 2.21 | 2.69 | -0.48 ([-0.57, -0.39]) | 17.89 | 14.70 |
| delayed | No | 80 | 5.59 | 6.53 | -0.93 ([-1.08, -0.79]) | 14.22 | 12.20 |
| delayed | No | 160 | 13.78 | 14.86 | -1.08 ([-1.31, -0.82]) | 11.58 | 10.72 |
| noisy | No | 40 | 2.90 | 3.81 | -0.91 ([-1.02, -0.80]) | 13.65 | 10.39 |
| noisy | No | 80 | 7.62 | 9.38 | -1.75 ([-1.92, -1.58]) | 10.44 | 8.49 |
| noisy | No | 160 | 19.11 | 19.70 | -0.59 ([-0.77, -0.41]) | 7.98 | 7.21 |
| misleading | No | 40 | 2.51 | 3.47 | -0.96 ([-1.07, -0.84]) | 15.76 | 11.41 |
| misleading | No | 80 | 6.68 | 8.95 | -2.27 ([-2.46, -2.08]) | 11.92 | 8.90 |
| misleading | No | 160 | 17.75 | 18.75 | -1.00 ([-1.23, -0.79]) | 8.60 | 7.49 |
| regime_shift | No | 40 | 2.73 | 3.43 | -0.70 ([-0.81, -0.58]) | 14.48 | 11.54 |
| regime_shift | No | 80 | 6.42 | 8.02 | -1.59 ([-1.76, -1.41]) | 12.38 | 9.93 |
| regime_shift | No | 160 | 15.45 | 17.27 | -1.83 ([-2.04, -1.64]) | 10.29 | 8.93 |
| costly_context | No | 40 | 1.52 | 1.95 | -0.43 ([-0.50, -0.35]) | 25.41 | 20.02 |
| costly_context | No | 80 | 3.60 | 4.34 | -0.74 ([-0.85, -0.63]) | 21.90 | 18.20 |
| costly_context | No | 160 | 8.87 | 10.58 | -1.71 ([-1.89, -1.53]) | 17.92 | 15.03 |
| delayed_misleading | Yes | 40 | 1.25 | 1.71 | -0.45 ([-0.55, -0.35]) | 31.52 | 23.23 |
| delayed_misleading | Yes | 80 | 3.31 | 4.37 | -1.06 ([-1.23, -0.89]) | 24.04 | 18.21 |
| delayed_misleading | Yes | 160 | 9.06 | 11.21 | -2.15 ([-2.47, -1.83]) | 17.60 | 14.23 |
| shift_memory | Yes | 40 | 1.40 | 1.82 | -0.42 ([-0.50, -0.34]) | 27.76 | 21.45 |
| shift_memory | Yes | 80 | 3.17 | 3.88 | -0.71 ([-0.81, -0.60]) | 24.86 | 20.38 |
| shift_memory | Yes | 160 | 7.43 | 8.76 | -1.32 ([-1.49, -1.16]) | 21.38 | 18.16 |
| high_overhead | Yes | 40 | 2.08 | 3.10 | -1.01 ([-1.08, -0.93]) | 18.89 | 12.77 |
| high_overhead | Yes | 80 | 5.34 | 7.68 | -2.33 ([-2.46, -2.21]) | 14.86 | 10.34 |
| high_overhead | Yes | 160 | 14.37 | 18.27 | -3.91 ([-4.09, -3.74]) | 11.10 | 8.60 |
| weak_signal | Yes | 40 | 1.99 | 2.46 | -0.48 ([-0.56, -0.40]) | 19.95 | 16.05 |
| weak_signal | Yes | 80 | 5.08 | 6.05 | -0.97 ([-1.08, -0.85]) | 15.66 | 13.15 |
| weak_signal | Yes | 160 | 13.02 | 14.60 | -1.58 ([-1.73, -1.41]) | 12.25 | 10.93 |
| shared_progress_null | Yes | 40 | 4.62 | 4.62 | +0.00 ([0.00, 0.00]) | 8.63 | 8.48 |
| shared_progress_null | Yes | 80 | 9.56 | 9.67 | -0.11 ([-0.15, -0.06]) | 8.35 | 8.22 |
| shared_progress_null | Yes | 160 | 19.21 | 19.39 | -0.18 ([-0.23, -0.12]) | 8.16 | 8.00 |

## Interpretation boundaries

Salary redistribution conserves the spending pool. Extra credits do not train worker model weights. If the revised conventional scheduler improves, that supports allocation changes; it does not establish that a currency mechanism is necessary.

The memory ablation changes the simulator's explicit handoff/compaction behavior. Any gain is conditional on those assumed costs and retention rules. It does not measure the effectiveness of real summarization or retrieval.

Outside the shared-progress null, workers have separate partial solutions and competing partial work is discarded after task completion. Public feedback can reveal useful progress. This structure makes concentration potentially valuable, so continuation-capable controls are necessary. Offline parameter-search costs are not charged to each evaluated project; candidate counts differ by policy family.

A real-model validation should retain the same held-out tasks, full cost accounting, independently checked outcomes, repeated seeds, and strong adaptive controls. Prior art and product hypotheses are documented in [research_sources.md](../research_sources.md).

## Reproducibility

Run `python -m economy.analyze --results results` after the frozen evaluation. The analyzer checks that the CSV contains the complete frozen seed × scenario × budget × policy grid and validates budget accounting.

- Evaluation SHA-256: `4e4a084026a544c74340267089b905d740222c45c8b28d19b4f3f20cb901fa2b`
- Frozen configuration SHA-256: `2e4c256aaa50640d1c211315f4402b208514442cef57147b96c789fc435cdc92`
- Analysis implementation SHA-256: `f1658c9875c4f3bbd382354f6af7e1e3a8b82aa80e808aec81f263d8f92b083f`

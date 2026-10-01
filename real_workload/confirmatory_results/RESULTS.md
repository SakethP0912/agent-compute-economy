# Confirmatory offline workload results

Fresh randomized seeds from the existing finite expression-search workload. No LLM calls or policy tuning.

Primary salary-versus-explore-commit difference: **-5.75 percentage points**, descriptive 95% paired seed-block bootstrap interval **[-8.17, -3.33]**. Resampling uses 100 seeds, preserving all 12 family/budget cells per seed.

Paired discoveries: 73 salary wins, 985 ties, 142 salary losses.

The outcome is discovery of any independently verified correct candidate within budget. It does not establish that an allocator can choose that candidate using training feedback alone.

| Policy | Correct discoveries / cells | Success rate | All charged operations / solved cell, including failures |
|---|---:|---:|---:|
| equal | 388 / 1200 | 32.33% | 411,258.4 |
| random | 384 / 1200 | 32.00% | 415,657.1 |
| salary | 498 / 1200 | 41.50% | 320,512.9 |
| cost_ucb | 389 / 1200 | 32.42% | 410,214.5 |
| explore_commit | 567 / 1200 | 47.25% | 281,594.4 |

## Descriptive budget slices

The pooled comparison above is primary. These slices were prespecified and are not substitute primary endpoints.

| Operations budget | Salary solved | Explore-commit solved | Difference, percentage points | Seed-block interval |
|---:|---:|---:|---:|---|
| 40,000 | 74 / 400 | 75 / 400 | -0.25 | [-3.25, +2.50] |
| 120,000 | 160 / 400 | 201 / 400 | -10.25 | [-14.75, -5.75] |
| 240,000 | 264 / 400 | 291 / 400 | -6.75 | [-11.50, -2.00] |

## Descriptive family slices

| Family | Salary solved | Explore-commit solved | Difference, percentage points | Seed-block interval |
|---|---:|---:|---:|---|
| affine | 74 / 300 | 72 / 300 | +0.67 | [-3.67, +5.00] |
| quadratic | 98 / 300 | 106 / 300 | -2.67 | [-8.33, +3.00] |
| piecewise | 167 / 300 | 171 / 300 | -1.33 | [-6.67, +3.67] |
| modular | 159 / 300 | 218 / 300 | -19.67 | [-23.67, -15.67] |

## Scope and audit

All five policies, every budget/family combination, costs, secondary comparisons, and false training matches are included in summary.json and the raw CSVs. Budgets repeat the same task seed, and the bootstrap retains that dependence. The primary comparator was selected before these runs from the original exploratory suite. No new outcomes were used for tuning. The original results were preserved byte-for-byte.

This evaluates one fixed salary rule and deterministic enumerators on a known finite grammar. New seeds may still select repeated target functions. Correctness is exhaustive on 81 finite-domain inputs only. Hidden correctness never controls scheduling or stopping. Costs include candidate proposals and AST-node evaluations, including hidden verification and failed runs, but exclude scheduler overhead and Python constant factors. All runs continue spending after discovery. These costs are not tokens, dollars, energy, or deployment latency. Slice intervals are descriptive, with no multiple-comparison claim. Conclusions do not establish performance for LLM agents or other workloads.

Protocol SHA-256: `0bd3176bf3be899bd84abd278768181d576e503a9708ed5e538f2dbebad8aa3a`

Frozen benchmark SHA-256: `e46835736fe3f16f374862266706ca7e1c19efdba6ce4ec13b4e3897e358450a`

Confirmatory harness SHA-256: `290476f2e6b49d54d09252d3ba31eb79671b5bcce7fa87db7a0d7c9e881a874b`

Runtime: 67.286 seconds. Execution deviations: none.

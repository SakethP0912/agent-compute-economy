# Confirmatory offline expression-synthesis allocation protocol

Written on 2026-09-30, before executing any of the new seeds. This is a separate prospective follow-up to the original 48-task exploratory suite and its disclosed analysis correction. Original results will remain untouched.

## Frozen method and question

Use the existing `benchmark.py` implementation exactly, with SHA-256 `e46835736fe3f16f374862266706ca7e1c19efdba6ce4ec13b4e3897e358450a`. Do not change any worker stream, candidate grammar, scheduler, salary rule, training feedback, reference evaluator, or operation accounting. The primary comparison is salary versus explore-commit, selected because explore-commit had the strongest success rate on the original exploratory suite. No policy or parameter will be tuned using the new outcomes. Report a salary win, loss, or null result without selecting favorable budgets or families after the fact.

The question is whether salary allocation improves the probability of discovering an exhaustively correct expression within budget relative to that simple adaptive policy, on fresh randomized task seeds from this same constructed workload. Seeds are new; target functions still come from the same finite grammar and can repeat. This is not an LLM benchmark or a test of generalization to new task distributions.

## Registered execution

- Seeds: every integer from 10000 through 10099 (100 seeds).
- Families: affine, quadratic, piecewise, modular, unchanged.
- Budgets: 40,000; 120,000; 240,000 charged operations.
- Policies: equal, random, salary, cost-UCB, explore-commit, unchanged.
- Total: 100 × 4 × 3 × 5 = 6,000 runs, with 1,200 paired seed/family/budget task cells per policy.
- All policies use the same target, training inputs, candidate streams, and operation budget for a paired cell. All budgets reuse a seed/family task, so budget outcomes are dependent.
- Primary outcome: any candidate discovered within budget that matches the independent reference on all 81 domain inputs. This is an offline discovery metric; it is not a claim that a deployed policy can select that candidate without a verifier. The allocator sees only training scores and operation costs, not heldout correctness, and it continues spending after a successful discovery.

## Registered analysis

Compute the mean salary-minus-explore-commit success difference across all 1,200 paired cells, weighting all three budgets and four families equally. Report it in percentage points with a descriptive paired percentile bootstrap 95% interval. Resample 100 seed blocks with replacement, keeping all 12 family/budget cells and policy pairings within each sampled seed. Use exactly 2,000 bootstrap resamples and fixed bootstrap random seed 7621. The 100 seeds, not the 1,200 cells, are the independent resampling units.

Report every policy's success count, success rate, total charged operations, and aggregate operations per solved task including failed runs. An undefined ratio with zero successes is null. Also report success and failure-inclusive cost for every budget, every family, and every family/budget combination. Per-budget and per-family primary comparisons are descriptive slices and are not replacement primary endpoints. Auxiliary comparisons against equal, random, and cost-UCB are explicitly secondary. No multiple-comparison claim will be made from these slices.

## Artifacts and integrity

Hash this exact protocol before execution and record its hash, the frozen benchmark source hash, the confirmatory harness hash, registered settings, and actual runtime. Save new raw run CSVs, worker CSVs, compact successful-candidate witness records, summary JSON, and a Markdown report under `confirmatory_results/`. Witnesses include the candidate AST, target parameters, training indices, and hashes of full independently computed reference and candidate outputs. Preserve the original results byte-for-byte and report any execution deviations. Tests must verify paired cluster construction across budgets/families, incomplete-cell rejection, and frozen-source/protocol integrity. The run uses Python's standard library without network or LLM calls.

Costs are abstract expression-node evaluation and proposal operations, not tokens, dollars, energy, or actual CPU time. Scheduler overhead and Python constant factors remain unmetered, as in the original experiment. Conclusions apply to this finite deterministic expression-search workload and its chosen salary rule only.

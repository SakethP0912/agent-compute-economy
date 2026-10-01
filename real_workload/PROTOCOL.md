# Offline expression synthesis allocation experiment

Protocol written before executing the benchmark. This is a real executable search workload, not an LLM experiment. No model, network, token, or dollar measurements are involved.

## Hypothesis and scope

Test whether a compute-salary allocator improves finite-domain program synthesis success under a fixed operation budget relative to equal allocation, random allocation, and two simple adaptive schedulers. A losing or null salary result is retained. This experiment cannot establish performance for LLM agents, language tasks, or open-ended work.

## Workload

Each task is an unknown integer function of x and y on the exhaustive domain {-4,...,4} squared (81 inputs). Four target families are affine, quadratic, piecewise, and modular expressions. A target is sampled uniformly within its family. Nine seeded inputs supply training examples; the remaining 72 are disjoint heldout inputs. The target's reference implementation uses independent family-specific Python arithmetic rather than the candidate interpreter. Correctness means exact agreement on all 81 inputs, not generalization beyond this finite domain.

Four deterministic workers enumerate a shared finite grammar. Each searches its own family first, with seeded ordering, then all remaining families. Each candidate is an actual expression tree evaluated by a recursive interpreter. The allocator sees only each worker's training-match fraction, its history, and charged operation cost. It does not receive the target family, heldout score, success flag, target expression, or target identity. Heldout results are logged by the harness and never feed selection or stopping. Every policy continues until no next candidate fits the remaining budget. Workers do not learn or alter model weights.

## Fairness and cost

Every policy gets the same target, training examples, initial state, per-worker candidate streams, and total budget within each paired seed/family task. A proposal costs one operation. Each visited expression-tree node on each of the 81 inputs costs one operation. Therefore a candidate costs 1 + 81 * tree_node_count. All candidates, including duplicates and failures, pay this cost. Training and hidden verification work are both included. These are abstract operation counts, not CPU time, tokens, or money. Interpreter constant factors, allocator computation, candidate construction, and reference construction are excluded and this limitation will be reported. No worker cache is shared across candidates or policies.

## Policies

1. Equal: round-robin among workers whose next candidate fits the remaining total budget.
2. Random: seeded uniform choice among those workers.
3. Salary/survivor: half the total budget starts in equal worker wallets; half is a central reserve. Select the live worker with the largest wallet relative to its next cost. A positive improvement in a worker's best training fraction transfers up to improvement * total_budget / 4 from reserve to its wallet. An unfunded worker is laid off and its residual wallet returns to reserve. If every live worker becomes unfunded, consolidate all remaining funds into the worker with the highest observed training fraction, breaking ties by least spent and then worker index. That worker can be rehired. Every transfer conserves the fixed total budget. No credits are minted.
4. Cost-UCB: first sample each eligible worker once. Then choose the largest index consisting of accumulated positive training-fitness improvement per charged cost, scaled by 1000, plus sqrt(2 log(total_pulls) / worker_pulls). This exploratory baseline is intentionally simple, without tuning on results.
5. Explore-commit: use round-robin for the first 25% of spent budget, then select the worker with the highest observed training fraction, breaking ties by least spent and then worker index. If it cannot fit the remaining budget, choose the next ranked eligible worker.

## Registered run and reporting

Default run: seeds 0 through 11, four families, all five policies, and 120,000 operations per run: 48 paired tasks and 240 policy runs. No parameter search or post-result tuning. One command writes one CSV row per run, one CSV row per worker/run, successful candidate witnesses with independent reference and heldout outcomes, summary JSON, and a Markdown results report. Include all policy results, per-family success, operation usage, successful-task cost, paired salary win/tie/loss counts, and a paired bootstrap 95% interval for salary success-rate differences (2,000 resamples with fixed seed). Intervals are descriptive over this small constructed suite, not evidence about real deployment distributions. Successful-task cost is conditioned on success and must not be used alone to rank policies.

Before execution, save the SHA-256 of this exact protocol. Each summary records that hash and the implementation hash. Tests must verify target/reference agreement, exhaustive heldout separation, deterministic results, independent heldout observation, cost accounting, and salary budget conservation. Report any execution deviations explicitly.

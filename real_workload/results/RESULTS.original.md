# Offline executable workload results

Actual finite-domain program synthesis, not an LLM benchmark.

Protocol SHA-256: `2b61095e08ece763dcb1001be5aa767ec70ffdd9ff358957eec685d8ba9c9af9`

| Policy | Solved / tasks | Success rate | Median operations to success, successful tasks only |
|---|---:|---:|---:|
| equal | 15 / 48 | 31.2% | 25790 |
| random | 14 / 48 | 29.2% | 23154.0 |
| salary | 20 / 48 | 41.7% | 33699.5 |
| cost_ucb | 15 / 48 | 31.2% | 24249 |
| explore_commit | 23 / 48 | 47.9% | 47525 |

## Paired salary comparisons

Win/tie/loss refers to task correctness within budget, not speed.

- Versus equal: 5 wins, 43 ties, 0 losses; success difference +10.4%, descriptive paired bootstrap interval [+2.1%, +18.8%].
- Versus random: 6 wins, 42 ties, 0 losses; success difference +12.5%, descriptive paired bootstrap interval [+4.2%, +22.9%].
- Versus cost_ucb: 5 wins, 43 ties, 0 losses; success difference +10.4%, descriptive paired bootstrap interval [+2.1%, +18.8%].
- Versus explore_commit: 4 wins, 37 ties, 7 losses; success difference -6.2%, descriptive paired bootstrap interval [-20.8%, +6.2%].

## Limits

Targets are sampled from the workers' known finite grammar. Family-specialized enumerators are a constructed allocation problem, not general-purpose agents. The full finite domain is exhaustively verified, but correctness beyond it is untested. Heldout observations never feed scheduling or stopping. All runs spend their available budget regardless of discovery; cost to first success is an offline diagnostic. A salary outcome depends on this specific reward and reallocation rule. Cost-UCB and explore-commit are simple untuned adaptive controls, not optimal algorithms. Operation accounting excludes scheduling, expression construction, reference construction, and Python constant-factor execution overhead. This does not estimate dollars, tokens, latency, learning, or LLM quality. Successful-task cost conditions on different success sets and is not a standalone policy ranking. Intervals describe the small constructed suite. Null and losing comparisons are retained.

Recorded wall time: 2.237 seconds (diagnostic only).

Run deviations: none. 

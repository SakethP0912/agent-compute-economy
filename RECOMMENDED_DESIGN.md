# Revised product and mechanism

## Recommendation after this experiment

Retain conserved budgets, independent verification, public cost accounting, and persistent task artifacts. Use the ordinary adaptive controller as the current reference implementation. Remove mandatory salaries, accumulated wealth as the main priority signal, permanent bankruptcy, and fixed continuation commitments from the default design.

This is a simplification suggested by the evidence, not a new winning algorithm. The reference configuration is the `ucb` control selected on development data before the held-out experiment. It already exists in `economy/policies.py`. The `revised` experimental arm remains in the repository under its original name, including its negative results. We do not relabel the winning control as the original invention.

Keep milestone-based redistribution as an optional experimental contender: its aggregate result changes from −2.07% to +1.55% when the simulator assigns it the same bookkeeping fee as UCB. That small gain is not robust evidence for a full economic layer, but it makes real overhead measurement essential. The reference controller is a conservative starting point and benchmark, not a universal winner.

## Separate responsibilities

**Budget ledger:** Own the user's finite spending cap. Reserve the maximum authorized cost before a model/tool call; settle actual use afterward; reclaim unspent reservations on cancellation. Count model calls, tool work, verification, coordination, and memory operations. A worker's request cannot increase the total pool.

**Allocator:** Estimate whether another bounded unit of work is worthwhile using current task type, observed progress, uncertainty, cost, and independent results. A worker can receive another turn without owning permanent wealth. Reconsider at each useful checkpoint. Benchmark any more complicated policy against the simplest competitive adaptive controller.

**Task state:** Store verified artifacts, decisions, sources, failed approaches, and outstanding obligations independently of the worker's context window. Retiring a process need not discard its task state. Real memory transfer needs separate tests: the simulator's memory advantage is only a stated assumption.

**Verifier:** Define success before execution. Keep hidden acceptance tests independent of the worker and progress scoring. Intermediate scores may help allocate effort, but are not final correctness. Program discovery and final-answer selection are separate metrics.

## What changes in the original idea

| Original mechanism | Evidence-informed version |
|---|---|
| Pay successful agents more tokens | Authorize another bounded spend when it is likely to help the current task |
| Wealthy agents survive | Keep reusable worker configurations and task artifacts; do not treat historical wealth as competence |
| Lay off agents permanently | Pause unproductive trajectories; keep the option to revisit a specialist |
| Let salaries handle context turnover | Manage compaction/handoff with an independently measured quality and cost tradeoff |
| Additional RL happens automatically | Add policy training only as a separate, evaluated learning mechanism |
| More sophisticated scheduler should win | Complexity must beat the strongest simple controller on untouched workloads |

The delayed-payoff scenarios do not validate a universal probation window. The tested two-step continuation rule hurt performance overall. Exploration and continuation should be justified by task evidence; another fixed heuristic is not automatically an improvement.

## Narrow product hypothesis

An execution and verification layer for teams with repeated, expensive, machine-checkable workflows might be useful. The promised outcome should be lower all-in cost per accepted result with a hard spend ceiling and inspectable evidence. Cross-provider accounting, dependable state transfer, and workflow integration could matter commercially even if the scheduling algorithm is conventional.

This experiment does not demonstrate demand or a defensible moat. Existing economic-agent, bandit-allocation, pruning, memory, and budget-enforcement work limits broad novelty claims. See `research_sources.md`.

## Next decision gate

Run a prospectively specified live-model study on independently sourced repository repairs or data transformations. Use at least two model families, multiple task sources, repeated runs, a blind acceptance verifier, a per-call reservation ledger, actual billed usage, and a completion deadline. Compare the ordinary adaptive control, one strong agent, and any new mechanism at matched all-in cost.

Choose the worthwhile effect before execution. For example, a buyer might require at least 15% lower all-in cost at comparable verified completion and latency, with the paired interval excluding no saving. This is a proposed commercial threshold, not a result or industry standard. Passing it across several workloads and paid pilots would justify expansion; failing it would favor integrating a simpler budget feature into an existing agent platform.

No live study was run here: no provider API key was configured and no local model server was running. The current results should not be used as an API savings claim.

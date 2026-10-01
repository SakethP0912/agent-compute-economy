# Agent compute economy: experimental protocol

Protocol written before executing development or evaluation runs, 2026-09-30.

## Scope and claims

This repository tests resource allocation, not reinforcement learning of model weights. The main experiment is a synthetic sequential portfolio: four worker configurations attempt the current task in a project. A project contains 20 ordered tasks with varying difficulty and type. A worker can make hidden progress toward a solution; only verified completed tasks count toward the outcome. Alternative worker trajectories are separate. No model API is called. A second, independently implemented experiment executes actual symbolic program search. Its operations are not LLM tokens or dollars.

Neither experiment can establish real-model savings, market demand, or breakthrough novelty. All modeled costs and feedback dynamics must remain visible in source and reports.

## Question and primary outcome

Does an allocation policy inspired by agent salaries improve verified completed tasks at the same **all-in project budget**, compared with an ordinary adaptive scheduling control?

The primary effect is the revised policy minus a development-selected strong control, averaged equally over the preregistered scenario × budget cells. The independent sampling unit is a project seed, paired across policies. Secondary outcomes are spending, completed-task cost (aggregate spending divided by aggregate completions, including failed runs), worker switches, wallet pruning, context resets, and overhead share. Survival itself is not success.

## Arms

- `round_robin`: equal turns, with identical task order and memory facilities.
- `fixed_blocks`: predetermined uninterrupted worker blocks; block size selected on development data.
- `single`: one worker for every task; worker selected on development data, not hindsight.
- `ucb`: cost-aware upper-confidence allocation, using public progress and verified completion feedback. Parameters selected on development data.
- `salary`: bounded wallets, initial equal grants, completion-linked redistribution and bankruptcy. Wallets and treasury must sum to the unspent budget. No reward creates compute.
- `salary_milestones`: same wallet mechanism with milestone-linked redistribution; included to expose sensitivity to cheap progress signals.
- `revised`: uncertainty-aware allocation with bounded exploration, discounted observations, and short continuation leases; parameters selected on development data after the first-stage results.
- Ablations of the frozen revised policy: no persistent memory; no continuation lease; no public-progress shaping (only completion rewards). The common controls have the same persistent-memory option as the full revised policy.

The revised policy is allowed to resemble a conventional scheduler. Improvement from removing the currency mechanism must not be described as evidence that currency is essential.

## Information boundary and cost accounting

Policies receive public costs, worker/type labels, public milestone scores, and verified completion notifications. They do not receive hidden productivity, remaining work, task solution thresholds, noise draws, or future returns. This is an interface boundary rather than a security sandbox.

All worker execution, scheduled verification, dispatch, controller bookkeeping, context compaction, and memory rehydration charges count against the same budget. Costs are **synthetic compute credits**, not estimates of actual API prices. All policies use the same environment-cost formulas; only explicitly declared policy overhead differs. Unaffordable operations cannot run. There is no wall-clock/parallel-speedup claim.

Common exogenous draws are keyed by world seed, task, worker, and that worker's attempt number. Policy-dependent RNG consumption must not change the latent world.

## Scenarios, budgets, and splits

Budgets: 40, 80, and 160 credits. Four workers; 20 tasks per project.

Development scenario families: homogeneous workers; stable heterogeneous workers; task specialists; delayed useful progress; noisy milestone feedback; misleading milestone feedback; changing worker effectiveness; context growth with expensive switches.

Structural holdouts, never used for parameter selection: combined delayed rewards plus misleading feedback; combined regime shift plus expensive memory; high controller overhead; and very noisy feedback with weak worker differences.

Development seeds: 0–39. Evaluation seeds: 10000–10199, reused as **paired blocks** across scenarios and policies. The evaluation set is not accessed until configuration selection is complete and a frozen configuration manifest has been saved. All policy parameters, code hashes, seeds, and scenario definitions are retained.

First run development for the original arms. Record the observed failure modes. Then tune the revised policy on development only. Freeze it. Evaluate every locked policy on new seeds and the additional structural holdouts. Any subsequent behavior changes require a new evaluation split; mechanical correctness fixes invalidate and replace previous outputs and must be logged.

## Analysis

Report each scenario and budget, the prespecified equal-weight aggregate, and the structural holdouts separately. The aggregate represents this chosen stress-test mixture, not a customer population.

Use a paired seed-block bootstrap with 2,000 fixed-seed resamples for the primary mean difference and a 95% percentile interval. Also report a paired aggregate ratio where its denominator is positive. Treat secondary comparisons and per-scenario intervals as exploratory, without family-wise coverage claims. No post-hoc best-on-test control is the primary comparator. Report every preregistered policy and scenario, including failures.

The simulation has no factual industry effect-size calibration. A positive result supports a mechanism under these assumptions; a negative result is retained. A market recommendation must incorporate independent prior-art research and clearly distinguish evidence from hypotheses.

## Reproducibility checks

Tests cover budget conservation, wallet conservation, exact replay, policy-independent exogenous draws, public observation boundaries, termination, negative/null-control behavior, and the independent program-search verifier. Save per-run CSV, summaries, representative event traces, selected configurations, and checksums. A fresh replay must reproduce substantive results; elapsed execution time and generated-at timestamps are excluded from bit-for-bit requirements.

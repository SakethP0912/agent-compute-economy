# Does an agent compute economy improve useful work?

Experiment completed 2026-09-30. Source, protocols, raw outcomes, controls, and reproduction commands are included in this repository.

## Decision

**The tested salary and survival mechanisms do not establish a robust advantage over simple adaptive allocation. A small milestone-salary gain appears when modeled bookkeeping costs are equalized, but it is sensitive to the cost assumption. The evidence does not justify calling the proposed broad idea a new or market-changing mechanism.** There is a plausible product opportunity in reliable budget enforcement, independent verification, and persistent task state, but this experiment does not demonstrate customer demand or real LLM savings.

This is a conclusion about the implementations and constructed workloads tested here, not a proof that every possible agent economy fails. One salary variant wins in several simulated settings. The missing property is a robust advantage over competitive controls across the preregistered mixture and the executable follow-up.

## What was built and run

Two independent tests approach the question from different directions:

1. **Controlled synthetic projects.** Four workers attempt a sequence of 20 tasks. We ran 11 frozen policies across 13 scenarios, three budget levels, and 200 held-out seed blocks: **85,800 policy runs**. Seeds were paired across policies, scenarios, and budgets. Development used disjoint seeds 0–39; evaluation used 10000–10199. Five structural holdouts were absent from tuning. Wallets conserve the original budget; work, verification, scheduling, context, and switching costs all count.
2. **Actual executable program search.** Four deterministic workers enumerate integer-expression programs. A separate reference implementation checks each candidate on all 81 inputs in a finite domain; only nine training inputs are visible to the allocator. After a 48-task exploratory suite, we froze the algorithms and ran **6,000 policy runs** on 100 fresh seeds, four program families, and budgets of 40,000, 120,000, and 240,000 charged operations. Each policy faced the same 1,200 seed/family/budget cells.

The row counts are not independent sample counts. Simulator uncertainty resamples **200 seed blocks**, retaining their scenario/budget cells; program-search uncertainty resamples **100 seed blocks**, retaining all 12 family/budget cells. Both use 2,000 deterministic bootstrap resamples. Secondary slices are exploratory, without a multiple-comparison coverage claim.

**No LLM was called and no model weights were trained.** The simulator uses modeled compute credits. The executable workload uses candidate and AST-evaluation operations. Neither unit is a token, dollar, GPU cycle, or deployment latency measurement. There was no configured provider API key or running local model server.

## Synthetic project results

Primary comparison: the development-selected revised scheduler versus the development-selected ordinary adaptive control, UCB. Each scenario/budget cell has equal weight.

| Policy | Mean completed tasks / project | Modeled credits / completed task, including failures |
|---|---:|---:|
| Equal worker turns | 4.195 | 22.105 |
| Fixed worker blocks | 6.362 | 14.575 |
| Development-selected single worker | 8.676 | 10.407 |
| Explore then greedy | 7.027 | 13.186 |
| Adaptive UCB control | **8.915** | **10.026** |
| Completion-paid salary / survival | 7.807 | 11.633 |
| Milestone-paid salary / survival | 8.730 | 10.290 |
| Tested revised scheduler | 7.792 | 11.692 |

The **primary revision loses 1.123 completed tasks per project**, 95% paired seed-block interval **[−1.161, −1.086]**. That is **12.60% fewer completions**, with relative interval **[−13.00%, −12.22%]**, under the common budget ceilings. It loses at all three budget levels and in both the held-out development-family and structural-holdout aggregates. These are completion differences, not measured dollar savings.

The completion-paid salary rule is **12.43% below UCB**. The milestone-paid rule is closer, **2.07% below UCB**, exploratory interval **[−2.87%, −1.40%]**. Comparing only with equal turns would make the salary methods look dramatically successful; the adaptive control changes that interpretation.

The salary results are heterogeneous. Milestone salary gains **16.45%** in the combined delayed/misleading scenario and **1.56%** over the structural-holdout mixture, but loses **52.25%** in the specialist scenario. In that scenario it completes 6.108 tasks versus UCB's 12.792. Permanent elimination can discard workers useful for later task types. These slices identify hypotheses, not separate confirmatory wins.

The shared-progress null removes any benefit from choosing one worker over another. Equal-overhead tests prove identical work trajectories regardless of worker choice. Policies with more modeled bookkeeping do not gain a free advantage there.

Full slices and every ablation appear in [the interactive report](results/report.html), [analysis tables](results/analysis.md), and [raw evaluation data](results/evaluation.csv).

## A cost assumption changes the smaller salary result

The main simulator assigns per-action bookkeeping fees of 0.04 credits to UCB, 0.07 to salary, and 0.06 to the revision. These are assumptions, not observed implementation costs. Because the milestone salary deficit was small, we registered an **exploratory, post-hoc sensitivity** before running 15,600 additional policy runs on fresh seeds 20000–20099. All four policies paid 0.04; every other policy rule and cost formula stayed frozen.

With equal bookkeeping fees, milestone salary completes **9.045 tasks versus UCB's 8.907**, a **1.55% gain**, exploratory paired interval **[+0.54%, +2.56%]**. Completion salary still loses **9.15%**, and the revision still loses **10.40%**. Equal-fee outcomes in the shared-progress null are exactly identical across policies.

This means the original **2.07% milestone-salary loss is not robust to the overhead assumption**. The correct takeaway is a small, cost-sensitive allocation effect worth measuring on real workloads, not that salary is uniformly ineffective. Conversely, equal overhead has not been demonstrated in a real implementation. Fresh seeds differ from the primary run, so subtracting the two reported effect sizes is not a paired causal estimate of changing the fee. Both results remain in the report; the sensitivity does not replace the primary endpoint. See [sensitivity results](sensitivity/results/RESULTS.md) and [its protocol](sensitivity/PROTOCOL.md).

## Executable workload results

The primary follow-up comparator, explore-commit, was chosen from the initial exploratory suite before the fresh-seed study. Policies, grammar, and feedback rules stayed unchanged.

| Policy | Cells with a fully correct candidate discovered | Discovery rate | Charged operations / successful cell, including failures |
|---|---:|---:|---:|
| Equal allocation | 388 / 1,200 | 32.33% | 411,258 |
| Random allocation | 384 / 1,200 | 32.00% | 415,657 |
| Salary / survival | 498 / 1,200 | 41.50% | 320,513 |
| Simple cost-UCB | 389 / 1,200 | 32.42% | 410,215 |
| Explore-commit control | **567 / 1,200** | **47.25%** | **281,594** |

Salary trails explore-commit by **5.75 percentage points**, 95% paired seed-block interval **[−8.17, −3.33]**. It has 73 paired wins, 985 ties, and 142 losses. The difference is effectively unresolved at the lowest budget, then negative at both larger budgets. Much of the deficit is in modular-expression tasks; the full family breakdown is retained.

This measures **discovery of a correct candidate anywhere in the search**, not whether the scheduler can select a correct final answer from training feedback alone. Hidden correctness does not affect scheduling or stopping; all policies keep spending after discovery. First-success cost is consequently an offline diagnostic. The cost ratio includes failed runs and post-discovery work; it is not a stop-on-success deployment estimate. Costs include hidden verification but exclude scheduler computation and Python constant factors.

We independently rechecked all **2,226 successful candidate witnesses** in the confirmatory run on all 81 inputs and reconciled all 24,000 worker-budget records. See [the executable study report](real_workload/confirmatory_results/RESULTS.md), [protocol](real_workload/CONFIRMATORY_PROTOCOL.md), and [raw data](real_workload/confirmatory_results/runs.csv).

## What the revision taught us

The predefined revision family removed permanent bankruptcy and added short continuation leases, a public-progress preference, and optional discounted competence estimates. Development selected a two-step lease, exploration 0.05, and no discounting. It was already behind UCB during development and remained behind on held-out cases.

The ablations narrow the explanation:

- Removing the two-step lease raises completion from **7.792 to 8.746**. The full revision is 10.91% below that ablation. A fixed continuation commitment was harmful in this configuration; this does not mean continuity is always harmful.
- Removing persistent memory lowers completion to **7.232**. That is a sensitivity result under stipulated reconstruction costs and compaction loss, not empirical proof that a real “digital brain” saves 7.75%.
- Removing both progress reward shaping and progress preference lowers completion to **6.519**. The result depends on the modeled progress signal; it does not establish that actual agent milestones are trustworthy.
- The full revision and completion-salary arm are essentially tied on the aggregate: difference −0.015 tasks, with an interval crossing zero.

The recommended implementation therefore keeps the **existing development-selected UCB control** as the reference allocator and treats currency as budget accounting. A cheap milestone-allocation variant remains a candidate for a live-cost comparison, given the sensitivity result. We do not relabel the control as a new winning invention. The failed experimental revision remains available. [Recommended design](RECOMMENDED_DESIGN.md) and [reference configuration](recommended_config.json) specify the simplified direction.

## Novelty and market assessment

The broad ingredients have close precedents. [Economy of Minds](https://arxiv.org/html/2606.02859v1) already studies economic survival and replacement. [Strategic Scaling](https://arxiv.org/abs/2506.12721v2) studies bandit compute allocation. [LiteLLM](https://docs.litellm.ai/docs/proxy/users) implements budget enforcement. The repository contains an [eight-source primary literature review](research_sources.md), with precise overlap and limitations. This is a targeted review, not an exhaustive novelty or patent search.

The plausible commercial direction is a narrow, measurable execution service: hard spending ceilings, verified acceptance, useful task-state handoffs, and lower cost per accepted result. Its advantage would have to come from production performance and integration, not the salary metaphor. Research novelty, commercial usefulness, and defensibility are different questions; this study establishes none of the latter two.

**Recommendation:** do not build a broad autonomous-currency product on the strength of these results. A small live-model pilot is justified only around a concrete workflow and a buyer's cost problem. Compare with the strongest simple controller, account for every model/tool/verifier/memory call, and fix the success threshold before running. A proposed gate is at least 15% lower all-in cost at comparable verified quality and latency across independently sourced workloads; that is a future decision criterion, not a demonstrated result.

## Validity, corrections, and reproducibility

The simulator assumes sequential tasks, private alternative trajectories, and public scores related to hidden progress. Concentrating work can therefore help by construction. There is no measured parallel speedup, collaboration synergy, imperfect terminal verifier, or model-learning effect. Cost coefficients are explicit assumptions rather than calibrated industry values. The mixture weights do not represent a customer population. Tight bootstrap intervals quantify seed variation within these models, not uncertainty about whether the models describe real AI systems.

Executable targets come from a known finite grammar. New seeds can select repeated target functions. Exhaustive correctness on a finite input domain is stronger than a few examples but weaker than unrestricted program correctness. The simulator and executable suite use different salary implementations; neither reproduces an existing paper.

The original small executable suite's bootstrap was corrected after review to resample shared seed clusters. Its raw outcomes and original source/report were preserved. The subsequent confirmatory study used the corrected method from the outset. Simulator amendments, including stronger controls and a true null, occurred before evaluation and are documented in [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md). Source hashes and disjoint seeds guard the development/evaluation boundary.

Run the complete experiment with `python3 run_all.py --output results/my-replay`. It runs tests and both studies, then compares substantive raw outputs byte-for-byte with the retained evidence. See [README.md](README.md) for commands and [VALIDATION.md](VALIDATION.md) for the completed verification record.

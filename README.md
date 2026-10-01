# Agent compute economy experiment

A repeatable investigation of whether salary, bankruptcy, and compute redistribution improve useful work under fixed budgets. This is research code with retained negative results, not a production agent framework.

**Start with [FINDINGS.md](FINDINGS.md)** for conclusions, [results/report.html](results/report.html) for interactive results, and [PROTOCOL.md](PROTOCOL.md) plus [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) for the registered design and changes made before evaluation.

## Research inspiration and what we tested differently

The motivating idea was to treat computational workers like a small economy: give them finite budgets, reward useful work, and redirect resources when they stop contributing. The [project literature review](research_sources.md) connects that idea to economic-agent systems, adaptive compute allocation, and budget-aware evaluation. The closest conceptual precedent is **Economy of Minds**.

### Previous research

| Research | What it studied | Connection to this project |
|---|---|---|
| **Qi et al., Economy of Minds (2026)** — [paper](https://arxiv.org/html/2606.02859v1) | LLM agents bid for action rights, exchange payments, and undergo economic selection and prompt mutation. Evaluation freezes the population and disables economic and evolutionary updates. | Motivates examining rewards and survival. Here, salary rules redistribute a conserved execution budget during a run; workers do not evolve prompts, and there are no auctions or LLM calls. |
| **Zuo and Zhu, Strategic Scaling of Test-Time Compute (2025; revised 2026)** — [paper](https://arxiv.org/abs/2506.12721v2) | Bandit algorithms adapt compute across queries using estimates of difficulty and solvability. | Establishes adaptive allocation as a serious alternative. We compare our economic rules against a local cost-aware UCB scheduler, which balances observed returns with exploration of uncertain workers. This is not an implementation of their algorithm. |
| **Xing et al., Compute Allocation for Self-Evolving LLMs / BaSE (2026)** — [paper](https://arxiv.org/abs/2605.29268) | Allocates LLM calls across parallel evolutionary trajectories with a multi-armed bandit, examining performance across repeated runs. | Closely related allocation work. Our executable benchmark instead schedules fixed symbolic search workers, with exhaustive verification on a finite input domain and no model or prompt evolution. |
| **Wang et al., Reasoning in Token Economies (EMNLP 2024)** — [paper](https://aclanthology.org/2024.emnlp-main.1112/) | Shows that simpler reasoning baselines can match or outperform elaborate methods when given comparable compute. | Informs the evaluation standard: compare capable alternatives at matched budget ceilings and include unsuccessful work in cost metrics. Its “token economies” refers to compute-aware evaluation, not worker salaries. |

### Our specific experiment

The question was: **does salary-based allocation improve verified useful work enough to justify its complexity under a fixed budget?** We tested:

1. **A conserved resource budget.** Salary payments move existing credits between workers; rewards cannot create more compute. The simulator charges work, verification, switching, memory, and controller overhead. The separate program-search benchmark charges candidate proposals and expression evaluations, but excludes scheduler overhead and Python runtime factors.
2. **Alternative allocation mechanisms.** We compare completion-based salaries, milestone-based salaries, and a revised scheduler that retains workers and tests brief continuation commitments, progress signals, and discounting of older observations. The comparison set includes equal turns, fixed blocks, a development-selected single worker, and adaptive controls. Ablations remove memory, continuation, or progress shaping to examine their effects separately.
3. **Stress tests and a second test bed.** Held-out simulation scenarios include delayed rewards, misleading feedback, changing worker effectiveness, costly switching, and a null where worker choice cannot help. The separate executable benchmark searches for integer programs and checks candidate correctness on all 81 inputs without revealing hidden correctness to the scheduler.
4. **A check on the cost assumptions.** After the primary evaluation, a separately labeled exploratory study equalizes bookkeeping fees. Its small milestone-salary gain shows why the original loss cannot be generalized into a claim that economic allocation never helps.

The contribution is the implemented comparison, retained evidence, and analysis of when this particular mechanism fails or depends on assumptions. These design choices are not claimed as research firsts. We did not reproduce the cited systems or run their benchmarks, so our negative results neither refute their findings nor establish performance for real LLM agents. The full [prior-art review](research_sources.md) also covers team construction, communication pruning, context management, and existing budget-enforcement tools.

## Results at a glance

- **Simulator:** the proposed revised scheduler completed 7.792 tasks per project versus 8.915 for the development-selected adaptive UCB control: **12.60% fewer completions**. The paired 95% interval for the difference was −1.161 to −1.086 tasks.
- **Executable program search:** salary allocation discovered correct programs in **41.50%** of cells versus **47.25%** for explore-commit. The difference was **−5.75 percentage points**, with a paired 95% interval of −8.17 to −3.33.
- **Sensitivity:** equalizing assumed bookkeeping fees produced a small **1.55% milestone-salary gain** in a separate exploratory simulation. The conclusion is that any benefit depends on the method and cost assumptions; these experiments do not establish a robust general advantage.

The useful result is the decision: retain the competitive adaptive control as the reference allocator and require measured workload evidence before adopting the more complex mechanism. Full results, including favorable slices and losing comparisons, are retained.

## Reviewer guide

1. Read [the application summary](APPLICATION.md) for the problem, approach, and validation.
2. Read [FINDINGS.md](FINDINGS.md) for effect sizes, ablations, and limits.
3. Open `results/report.html` locally for the interactive simulator results, or read [the static analysis](results/analysis.md).
4. Check [VALIDATION.md](VALIDATION.md), then use the reproduction command below. The data are generated by the included code; no external dataset is needed.

## What actually runs

1. A hidden-state simulator compares fixed allocation, a fixed worker, ordinary adaptive controls, two wallet/survival rules, a revised scheduler, and ablations. It contains 13 scenarios, three budget levels, and 200 untouched evaluation seeds. It charges explicitly synthetic work, verification, switching, context, and controller costs.
2. An independent executable workload searches for integer programs from examples. Four deterministic symbolic workers enumerate actual expression trees. An independently implemented reference checks them over an exhaustive finite domain. It measures correct-candidate discovery under a bounded number of charged operations. An exploratory 48-task run is followed by 6,000 unchanged-policy runs on 100 fresh seeds, four families, and three budgets.

**Neither experiment calls an LLM.** Credits and AST operations are not tokens, API prices, or measured GPU compute. The code does not train model weights. Strong performance here is not evidence of real-model savings or product-market fit.

A separately recorded post-hoc sensitivity runs 15,600 additional fresh-seed comparisons with equal controller bookkeeping fees. Its small milestone-salary gain qualifies the primary result; read it alongside the main findings.

## Reproduce

Python 3.10 or later; standard library only. The recorded run used Python 3.13.7. No API key, package installation, or network access is needed.

```sh
# From the extracted or cloned project directory:
python3 run_all.py --output results/my-replay
```

Choose an empty output directory. This runs tests, baseline development, revision selection, configuration freezing, held-out evaluation, statistical analysis, both independent program-search phases, and the equal-cost sensitivity. It retains code hashes, protocol hashes, all raw policy-run rows, and sample traces, then compares raw outcomes byte-for-byte with the retained evidence. Expect a few minutes depending on the machine. Do not treat timing differences as a result; allocation decisions and substantive results should replay exactly.

Individual stages:

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s real_workload -p 'test_*.py' -v
python3 -m economy.experiment develop --output results/new-run
python3 -m economy.experiment freeze --output results/new-run
python3 -m economy.experiment evaluate --output results/new-run
python3 -m economy.analyze --results results/new-run
python3 real_workload/benchmark.py --output results/search-replay
python3 real_workload/confirmatory.py --output results/search-confirmatory-replay
python3 sensitivity/run_sensitivity.py --output results/overhead-replay
```

The simulator refuses to evaluate if its frozen implementation or protocol has changed. Rerun development and freeze after changing behavior. Use a new untouched seed split for scientific claims after examining held-out outcomes; a deterministic replay is reproducibility evidence, not a new validation set.

## Layout

- `economy/simulator.py`: hidden dynamics, public observation interface, cost ledger, scenario definitions.
- `economy/policies.py`: fixed, adaptive, wallet/survival, revised, and ablation policies.
- `economy/experiment.py`: development-only selection, provenance checks, configuration freeze, evaluation.
- `economy/analyze.py`: paired seed-block bootstrap, complete-grid checks, machine-readable and visual reports.
- `results/evaluation.csv`: every held-out simulator policy run.
- `results/frozen_config.json`: selected parameters, seeds, source hashes, and scenario definitions.
- `results/traces.json`: representative public event traces.
- `real_workload/`: separately preregistered executable search benchmark and results.
- `sensitivity/`: fresh-seed equal-bookkeeping-cost sensitivity, explicitly exploratory.
- `research_sources.md`: primary-source prior-art review and product hypotheses.

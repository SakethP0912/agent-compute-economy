# Application project summary

## Brief description

I investigated whether rewarding computational workers with “salaries” and reallocating their budgets improves useful work under a fixed compute budget. I built a controlled simulator and a separate executable program-search benchmark, comparing economic allocation rules with fixed allocation and adaptive scheduling. I chose this approach to isolate the proposed mechanism, account for failed work, and test against competitive baselines before making claims about real AI systems.

I separated development and evaluation seeds, froze policy configurations, and evaluated 85,800 simulation runs across 13 scenarios, plus 6,000 follow-up program-search runs. Validation included paired seed-block bootstrap intervals, budget-conservation tests, exhaustive program checks over an 81-input domain, and deterministic replay of retained outcomes.

The result challenged the hypothesis: the revised simulator policy completed 12.60% fewer tasks than the adaptive control. In program search, salary allocation achieved 41.50% correct-candidate discovery versus 47.25% for explore-commit. An exploratory equal-overhead simulation found a small milestone-salary gain, showing sensitivity to cost assumptions. I retained the negative results and recommended the simpler adaptive control pending real-workload evidence.

## Evidence and interpretation

- [Simulator results](results/analysis.md): 11 frozen policies × 13 scenarios × 3 budgets × 200 evaluation seeds. The 200 paired seed blocks, rather than all 85,800 rows, are the uncertainty units.
- [Program-search results](real_workload/confirmatory_results/RESULTS.md): five policies × four families × three budgets × 100 fresh seeds. Salary minus explore-commit was −5.75 percentage points, with a 95% paired seed-block interval of [−8.17, −3.33].
- [Cost sensitivity](sensitivity/results/RESULTS.md): 15,600 separate exploratory runs. Equal assumed bookkeeping costs changed milestone salary from a small loss to a 1.55% gain; this does not replace the primary evaluation.
- [Validation record](VALIDATION.md): tests, replay commands, and independent checks of the retained program witnesses.

This is an algorithmic research and data-analysis project. It does not train model weights or call an LLM. Budgets are synthetic credits or charged expression operations, not measured API dollars or hardware compute. The search result measures discovery of a correct candidate, not final-answer selection by an agent. Protocols and source hashes are retained locally; they are not an external preregistration or independent timestamped proof of chronology.

## Reproduce

Use Python 3.10+ from the project directory:

```sh
python3 run_all.py --output results/my-replay
```

Choose an empty output directory. The runner executes the tests, development and frozen evaluation, both program-search studies, and the sensitivity analysis. It compares four raw outcome files byte-for-byte with the retained evidence. A replay verifies reproducibility; it does not create new independent validation data.

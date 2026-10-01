# What the equal-cost sensitivity changes

**The milestone-salary conclusion depends on the controller-fee assumption.** Giving all four policies the same 0.04-credit bookkeeping fee changes milestone salary from a small loss in the original experiment to a small gain on fresh seeds. The original result should remain visible, but its negative sign is not robust evidence that milestone salaries are intrinsically worse than UCB.

This exploratory run used 100 fresh paired seed blocks, 13 scenarios, three budgets, and four frozen policies: 15,600 runs. No policy was retuned. All costs other than the controller fee remained unchanged.

- UCB: **8.906667** completed tasks/project.
- Milestone salary: **9.044615**, a **+1.549%** relative gain over UCB, with a paired 95% bootstrap interval of **[+0.542%, +2.558%]**.
- Completion salary: **8.092051**, **−9.146%**, interval **[−10.244%, −8.069%]**.
- Revised scheduler: **7.980769**, **−10.396%**, interval **[−10.967%, −9.784%]**.

The milestone result remains uneven. It loses **4.18%** at the 40-credit budget, gains **3.56%** at 80 credits, and gains **1.74%** at 160 credits. In the specialist scenario it still loses **50.80%**. This is neither a large nor a broadly reliable advantage. All policies produce identical completion outcomes in the shared-progress null when their fees are equal.

The appropriate revised assessment is that completion-only salary and the tested revision remain inferior under this sensitivity, while milestone salary has a small conditional advantage whose sign depends on assumed overhead. Actual controller costs and worker specialization therefore deserve measurement before making a production superiority claim. A 1.55% synthetic average with severe scenario failures does not establish a market-changing product.

This is post-hoc, exploratory evidence. Intervals quantify variability across generated seed blocks within the chosen model; they do not include model misspecification or establish effects for LLM agents. Because these seeds differ from the original evaluation, the change in point estimates between experiments is not a paired estimate of the fee effect.

The [protocol](PROTOCOL.md) was hashed before execution. The [generated report](results/RESULTS.md), [full summaries](results/summary.json), and [individual runs](results/runs.csv) are retained. The harness verifies original source, design, and primary-output checksums before and after running. No frozen code or original result was changed.

Reproduce from the project root:

```sh
python3 sensitivity/run_sensitivity.py
```

To replay into a separate directory without overwriting the original evidence:

```sh
python3 sensitivity/run_sensitivity.py --output /private/tmp/economy-overhead-replay
```

The output-directory option was added after the initial run without changing the method. The exact original harness is preserved as `run_sensitivity.initial.py`, matching the implementation hash in the original results. A full replay produced a byte-identical raw CSV and exactly identical group summaries; see `replay_verification.json`.

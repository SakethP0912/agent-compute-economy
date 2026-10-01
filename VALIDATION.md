# Completed validation

Validated on 2026-09-30 using Python 3.13.7 on macOS. Both experiment implementations require only the Python standard library.

## Tests and independent checks

- **25 unit tests passed:** 12 simulator/statistics tests and 13 executable-workload tests.
- Checked resource conservation, salary-wallet conservation, termination, rejection of unaffordable operations, policy-independent randomness, exact replay, and absence of hidden dynamics in public observations.
- Confirmed the shared-progress null produces identical work trajectories for different worker sequences at equal controller overhead.
- Tested that paired bootstrap differences retain their pairing, failed-run costs remain in cost/completion, and zero denominators do not produce fictitious infinite gains.
- Verified target/reference agreement, disjoint public and hidden examples, unchanged scheduling when hidden correctness is altered, AST operation accounting, seed-block grouping, and complete confirmatory grids.
- Independently audited all **85,800** simulator cells, all **704** policy/group summaries, all comparison point estimates, and the primary bootstrap interval.
- Independently checked all **2,226** successful confirmatory program witnesses on the full 81-input domain and reconciled **24,000** worker-level records.

## Full clean replay

Executed `python3 run_all.py --output /private/tmp/economy-complete-replay` from a clean output directory. This reran development, freezing, held-out simulation, analysis, the original executable suite, and the 6,000-run executable follow-up.

The following raw outcomes reproduced **byte-for-byte**:

- `results/evaluation.csv` — all 85,800 simulator policy runs.
- `real_workload/results/runs.csv` — all 240 original executable policy runs.
- `real_workload/confirmatory_results/runs.csv` — all 6,000 fresh-seed executable runs.

The replay is verification of determinism, not additional independent evidence. Retained hashes, commands, platform details, and run time appear in `results/replay_manifest.json` and `results/validation.json`. Execution times can vary and are not a policy-performance claim.

After adding the exploratory overhead sensitivity, ran its CLI separately against another empty output directory: `python3 sensitivity/run_sensitivity.py --output /private/tmp/economy-overhead-replay`. All **15,600** raw rows reproduced byte-for-byte, and every group summary matched. The original sensitivity harness, its CLI-only update, and `sensitivity/replay_verification.json` preserve that provenance. The one-command runner now includes this independently verified stage as well.

## Report verification

Opened `results/report.html` in the browser and inspected its rendered layout. Changed the scenario scope to Specialists and budget to 80 credits, verified the displayed results updated, then restored the full aggregate. The browser reported no JavaScript errors. The report is self-contained and uses no external resources.

## Scope of validation

This confirms the behavior and reproducibility of these implementations. It does not validate the simulator's assumptions as a model of actual language-model agents, establish unrestricted correctness of synthesized programs, demonstrate live API savings, or establish market demand.

## Application preparation recheck — 2026-10-01

A fresh full run of `run_all.py` completed successfully under Python 3.13.7. All 25 unit tests passed. All four raw outcome files reproduced byte-for-byte, including the 15,600-run sensitivity stage now included in the runner. The complete replay took approximately two minutes on this machine; this is reproduction timing, not an algorithm-performance result.

Then ran `python3 real_workload/verify_confirmatory.py --output <replay-directory>/confirmatory` against the freshly generated confirmatory artifacts. It recomputed all 2,226 successful witnesses over 81 inputs, reconciled 24,000 worker records, and reproduced every summary statistic across 6,000 runs. Commands, hashes, and check results are retained in [application_validation.json](results/application_validation.json).

Application preparation changed only presentation and packaging: the README, application summary, validation record, and ignore rules. The frozen experimental implementations, protocols, configurations, and original outcomes were preserved. This recheck is reproducibility evidence, not another independent experiment.

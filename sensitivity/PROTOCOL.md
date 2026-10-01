# Equal-controller-cost sensitivity

Written before this sensitivity was executed. This is an **exploratory, post-hoc sensitivity**, motivated by the primary experiment's milestone-salary result and the possibility that assumed controller bookkeeping fees affect its sign. It is not a replacement primary analysis or a new product-validation claim.

## Question

Does the comparison with UCB change when every policy pays the same modeled controller cost of 0.04 credits per action? The frozen experiment charges UCB 0.04, salary variants 0.07, and the revision 0.06. Those differences were assumptions rather than measured costs. This sensitivity removes that assumed difference; it does not measure actual implementation overhead.

## Fixed design

- Reuse the original frozen policy configurations for `ucb`, `salary`, `salary_milestones`, and `revised`.
- Set each created policy object's `overhead` to 0.04 using a wrapper around the existing policy factory. Change no policy decision rules, environmental dynamics, memory settings, verification fees, switching costs, context costs, or scenario overhead multipliers. In the high-overhead scenario, the common controller fee is multiplied by eight for every policy.
- Use all 13 frozen scenarios and all three frozen budgets (40, 80, 160).
- Use fresh seeds 20000 through 20099, disjoint from development and original evaluation. The same seed/scenario/budget world is paired across all four policies. Total: 15,600 runs; 100 independent seed blocks.
- Run no parameter search or subsequent tuning. Keep all outcomes, including unfavorable and null results.
- Verify frozen source/configuration hashes before and after execution. Do not edit the frozen implementation or primary outputs.

## Analysis and limits

The sensitivity's planned comparisons are completion salary and milestone salary versus UCB; revised versus UCB is also reported. The outcome is verified completed tasks at the same all-in budget. Give each scenario/budget cell equal weight in the aggregate. Compute paired 95% percentile bootstrap intervals using 2,000 resamples of the 100 seed blocks, with random seed 734922. Each resampled seed retains all scenarios and budgets. Report the absolute difference and ratio of aggregate means minus one. Per-budget and per-scenario summaries are exploratory. No multiplicity correction is applied; no interval has a family-wise coverage claim.

The null scenario should have identical completion outcomes across policies when fees are equal; check this invariant. Check every run's budget conservation. Save raw rows, configuration and source provenance, summary JSON, and a short Markdown report. Save a SHA-256 of this protocol before running.

This is still a synthetic model. Its result concerns sensitivity to an assumed accounting rule; it does not estimate tokens, dollars, real overhead, LLM task performance, or market value. New seeds differ from the original evaluation, so any numerical change from that earlier run must not be interpreted as a precise paired causal effect of controller fees. A favorable equal-fee result establishes neither superiority under measured all-in costs nor a general currency advantage.

## Reproduce

From the project root, run:

```sh
python3 sensitivity/run_sensitivity.py
```

No external dependencies, API calls, or paid services are used.

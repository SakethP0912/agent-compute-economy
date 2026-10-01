# Offline executable expression-search benchmark

This benchmark actually synthesizes and verifies small integer programs. It uses deterministic algorithmic workers, not LLMs. Costs are charged search/evaluation operations, not tokens or dollars. It is an additional constructed test bed for allocation ideas, not evidence of agent-product performance.

Requires Python 3.10+ and no third-party packages, model credentials, or network access.

From this directory, run the registered benchmark:

```sh
python3 benchmark.py
```

Validate the implementation:

```sh
python3 -m unittest -v
```

`PROTOCOL.md` was written and SHA-256 hashed before execution. The harness refuses to run if it differs from `protocol.sha256`. The default run evaluates 48 paired tasks and five policies, writing `results/runs.csv`, `results/workers.csv`, `results/summary.json`, `results/witnesses.json`, and `results/RESULTS.md`. Each witness contains the synthesized AST, domain, independently computed reference outputs, and actual candidate outputs. Each run has a trace hash for reproducibility. The salary ledger asserts budget conservation at every allocation and observation.

Optional smaller or alternate runs use `--seeds`, `--budget`, and `--output`; nondefault parameters are explicitly marked as deviations. Example:

```sh
python3 benchmark.py --seeds 2 --budget 20000 --output smoke-results
```

The benchmark always completes its budget instead of stopping on hidden correctness, preserving identical information across policies. The hidden verifier is included in the operation charge but is observational: changing its results cannot change scheduling. Correctness is exhaustive only on the stated finite domain. See the protocol and generated results for all limits, including abstract operation accounting and untuned adaptive controls.

Independent review identified shared-seed dependence across the four families. `ANALYSIS_ADDENDUM.md` transparently records the postregistration correction: bootstrap whole seeds, retaining all four families, and report total operations per solved task including failed runs. Original results and execution source are retained under `results/`. To recompute only derived analysis while preserving raw files:

```sh
python3 benchmark.py --reanalyze
```

The separately preregistered confirmatory suite uses fresh seeds 10000–10099, three budgets, all four families, and all five unchanged policies (6,000 runs). Its primary comparison is salary versus explore-commit. See `CONFIRMATORY_PROTOCOL.md`; the harness verifies both its preregistration hash and the frozen benchmark source. Run it without touching original results:

```sh
python3 confirmatory.py
```

Outputs go to `confirmatory_results/`. Its bootstrap resamples 100 whole seed blocks, keeping all 12 family/budget cells together. Both suites report discovery of a verified correct candidate; they do not measure an allocator's ability to select that candidate using training feedback alone.

Independently recompute saved witnesses, paired statistics, and run/worker budgets:

```sh
python3 verify_confirmatory.py
```

# Prior art and product assessment

Research checked on **2026-09-30**. These are primary research papers and official product documentation. This is a targeted literature review, not an exhaustive novelty search or a patent opinion. Published performance figures below are the authors' claims, not results reproduced by this project.

## Assessment

The broad idea of rewarding useful agents, withdrawing resources from unsuccessful agents, and reallocating compute is **not new**. Economic survival and replacement are particularly close to *Economy of Minds*. Budget-aware composition, pruning, adaptive inference allocation, and persistent context also have substantial prior work.

A positive result in this project's simulator would establish that a particular allocation rule helps under the simulator's assumptions. It would not establish that language models learn from salaries, that a real deployment saves the same amount of money, that the mechanism is novel, or that customers will buy it. A poor result is useful evidence for revising the mechanism rather than adding more favorable assumptions.

The plausible product opportunity is an accountable compute manager: independent verification, measured cost accounting, task-aware allocation, and useful handoffs integrated into an existing workflow. The defensible asset would have to be demonstrated deployment performance and the accumulated evidence needed to predict the value of another unit of compute. That is a product hypothesis, not a finding from the literature or the simulation.

## Verified sources

### 1. Economy of Minds — closest conceptual overlap

**Zhenting Qi et al.**, *Economy of Minds: Emerging Multi-Agent Intelligence with Economic Interactions*. Preprint submitted **2026-06-01**. [Primary paper, v1](https://arxiv.org/html/2606.02859v1).

Agents bid for action rights, earn environmental rewards, exchange payments, pay rent, go bankrupt, and undergo replacement or prompt mutation. The backbone is frozen; behavior differs through prompts. Its formal wealth accounting concerns bids, rewards, and rent. That mechanism is not equivalent to measuring an API bill. Section 2.4 states that evaluation disables evolutionary and economic updates.

**Implication:** Currency, selection, and survival are substantial prior art. A production scheduler using actual resource costs and online verification may differ operationally, but that alone does not establish research novelty. Do not claim this project reproduces or defeats EoM without implementing its procedure and matching its evaluation.

### 2. BAMAS — budget-aware team construction

**Liming Yang et al.**, *BAMAS: Structuring Budget-Aware Multi-Agent Systems*. Preprint **2025-11-26**; AAAI proceedings published **2026-03-14**. [AAAI paper page](https://ojs.aaai.org/index.php/AAAI/article/view/40226), [preprint](https://arxiv.org/abs/2511.21572).

BAMAS selects a set of models using integer linear programming, then uses reinforcement learning to choose a collaboration topology. The paper reports comparable performance at reduced cost on three tasks, with up to 86% cost reduction in its tested settings.

**Implication:** Budget-aware agent composition and reward-driven orchestration already exist. Its emphasis is team construction and topology selection; that is distinct from paying individual workers during an ongoing task. The reported maximum saving is not a forecast for this project.

### 3. Reasoning in Token Economies — evaluation discipline

**Junlin Wang et al.**, *Reasoning in Token Economies: Budget-Aware Evaluation of LLM Reasoning Strategies*. EMNLP **November 2024**; preprint **2024-06-10**. [ACL publication](https://aclanthology.org/2024.emnlp-main.1112/).

The paper compares reasoning strategies while accounting for compute. Simpler chain-of-thought self-consistency often matches or exceeds more elaborate strategies when given comparable resources; extra computation can worsen some methods.

**Implication:** A fixed team alone is an insufficient control. Include simple capable alternatives, compare equal all-in budgets, count coordination and evaluation overhead, and publish unfavorable results. This paper's use of “token economies” describes budget-aware evaluation; it is not a salary-and-bankruptcy system.

### 4. AgentPrune — communication pruning

**Guibin Zhang et al.**, *Cut the Crap: An Economical Communication Pipeline for LLM-based Multi-Agent Systems*. Preprint **2024-10-03**; official repository identifies acceptance at **ICLR 2025**. [Primary paper](https://arxiv.org/abs/2410.02506), [authors' implementation](https://github.com/yanweiyue/AgentPrune).

AgentPrune removes redundant or harmful messages from the spatial and temporal communication graph. The paper reports large token reductions while retaining comparable performance in its evaluated tasks.

**Implication:** Pruning unnecessary multi-agent activity is established. Communication pruning is different from dismissing an entire worker. A gain from reducing context or communication should be separated from a gain caused by economic allocation.

### 5. Strategic Scaling of Test-Time Compute — adaptive control to take seriously

**Bowen Zuo and Yinglun Zhu**, *Strategic Scaling of Test-Time Compute: A Bandit Learning Approach*. First submitted **2025-06-15**, revised **2026-04-23**; arXiv lists **ICLR 2026**. [Primary paper, v2](https://arxiv.org/abs/2506.12721v2).

The authors formulate compute allocation as a bandit problem, estimating difficulty during execution and prioritizing solvable hard queries over unproductive ones. They provide theoretical results and math/code experiments comparing adaptive and uniform allocation.

**Implication:** Giving compute to the highest estimated future opportunity is established research. An economic scheduler should beat a competitive adaptive allocation control, not merely uniform round-robin. A simple UCB implementation is a useful local baseline but should not be described as a reproduction of this paper.

### 6. BaSE — allocation across parallel improvement trajectories

**Sixue Xing et al.**, *Compute Allocation for Self-Evolving LLMs: From Depth-Breadth to Multi-Armed Bandits*. First submitted **2026-05-28**, latest inspected revision **2026-09-12**. [Primary paper, v3](https://arxiv.org/abs/2605.29268v3).

BaSE allocates LLM calls across parallel evolutionary trajectories through a multi-armed bandit. The authors emphasize run-to-run variation and report a 12.3% mean-fitness improvement over their strongest island-protocol baseline across eight model/task combinations, without changing the model, prompt, or evaluator.

**Implication:** Adaptive allocation among competing workers or search trajectories is also close prior art. Mean fitness is not equivalent to production task completion or dollar savings. Repeated runs and comparison against adaptive controls are essential.

### 7. Anthropic context engineering — persistent memory and handoff

**Anthropic Applied AI**, *Effective context engineering for AI agents*, **2025-09-29**. [Official engineering article](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents).

The article discusses compaction, structured external notes, selective retrieval, and subagent architectures. It also explains that excessive compaction can discard details whose importance becomes clear later.

**Implication:** The proposed “digital brain” resembles established context-management practice. Treat memory as its own intervention: measure write/read/summary costs, failed transfers, and downstream quality. Terminating a worker and preserving its useful state are separate decisions.

### 8. LiteLLM — existing budget enforcement infrastructure

**LiteLLM**, *Budgets, Rate Limits*. Living documentation, inspected **2026-09-30**. [Official documentation](https://docs.litellm.ai/docs/proxy/users).

The documentation describes budgets for users, teams, and virtual keys; requests are blocked after limits are reached. It also describes reserving estimated request cost before concurrent work begins, then reconciling actual cost.

**Implication:** Wallets, caps, and basic spend enforcement already have implementation paths. A new product should integrate with these components and differentiate through verified outcome improvement, rather than present accounting itself as the breakthrough. Current behavior is version-dependent and should be rechecked when integrating.

## Changes suggested by the evidence

These are design recommendations to test, not observed experiment results.

1. Use a conserved spending pool denominated in cost credits. Pay for model work, verification, memory, tools, and coordination from the same pool; salary transfers do not create additional compute.
2. Keep worker competence estimates separate from worker balances. Historical success is evidence, but the next decision should consider the current task, uncertainty, remaining budget, and expected future gain.
3. Retain an exploration allowance and a probation period. Immediate dismissal after a few failures can eliminate a specialist before a difficult task becomes solvable.
4. Prefer pausing and resuming when useful state can be retained. Permanent elimination should be an explicit experimental condition, not an assumed requirement.
5. Verify results independently. Visible milestones can guide scheduling; final evaluation must be withheld from the policy and must not be replaced by self-reported confidence.
6. Keep memory identical across allocation controls before testing memory separately. Otherwise a handoff improvement can masquerade as an economic improvement.
7. Describe learning precisely. Budget reallocation changes execution. Persistent policy training or prompt evolution is an additional mechanism that requires its own evaluation.

## What would justify developing a product

The next evidence should come from a narrow real workload with cheap, independently checkable outcomes, such as bounded repository repairs or a validated data-transformation queue. Run the strongest simple controller and the proposed controller on the same held-out tasks and multiple seeds. Charge all coordination, verification, model, tool, and memory work. Measure verified completion, cost, latency, regressions, and operational failure rates.

A practical advancement gate could be a preregistered reduction of at least 15% in all-in cost at comparable verified quality against the strongest adaptive control, with a paired confidence interval excluding no benefit, repeated across several independently selected workloads. This is a proposed business threshold, not an industry standard. If savings disappear against a simple adaptive scheduler, the economic layer is probably unnecessary.

An initial buyer hypothesis is a team already paying for repeated agent workflows with verifiable outputs. Validate it through design partners and paid trials: establish their existing cost per accepted result, integration effort, failure tolerance, and willingness to pay. A simulator cannot answer those questions. Net value must exceed the new system's service fee and operating burden.

**Current conclusion:** There is enough related evidence to justify disciplined experimentation, but not a claim of a new category or a “game changer.” A strong result would support a narrowly defined execution and verification advantage. The claim should become broader only after real deployments demonstrate that the advantage survives stronger baselines, changing models, unreliable feedback, and full cost accounting.

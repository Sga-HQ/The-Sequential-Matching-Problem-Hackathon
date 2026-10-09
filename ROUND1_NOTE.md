# The One Introduction Problem: Round 1 Research Note

| | |
|---|---|
| **Team** | solo |
| **Version date** | 9 October 2026 |
| **Repository** | https://github.com/Sga-HQ/The-Sequential-Matching-Problem-Hackathon |
| **Code and results behind every number** | commit `d86ff40ecc561157a6c9b15f6b977acc0e556752` |
| **Organiser kit** | participant specification 1.0.0, kit commit `a8e26b35118cfa8e886a02f93984923e43ab64f6` |

**How to read the claims.** Each claim is labelled by the kind of evidence behind it:
- **[rule]**: the organisers' specification.
- **[code]**: behaviour we read in the public simulator source (`kit.py` at the kit commit above).
- **[dev]**: an empirical result on our development seeds.
- **[oracle]**: an offline diagnostic that uses hidden simulator values (never available to the policy).
- **[motivation]**: a literature result that motivates a choice without proving it applies here.
- **[plan]**: a Round 2 experiment.

All uncertainties written ± are **one paired standard error (SE) across episodes**: both policies are run on the same simulated worlds and we measure the spread of their differences. Where marked *cluster-robust*, episodes that share a world are grouped so that their correlation is not mistaken for extra evidence. 95% intervals are about ±2 SE.

**Terms used in this note.**

| Term | Meaning |
|---|---|
| Simulator, kit | The organisers' public Python package (`kit.py`). It generates synthetic members, plays out each introduction, and includes baseline policies. |
| Policy | Our program. Each simulated day it chooses which questions to ask and which pairs to introduce. |
| Member | One synthetic person in the simulator, about 200 per world. |
| World, seed, episode | A *seed* is a number that generates one *world* (a population of about 200 synthetic members). An *episode* is one run of a policy in one world: 60 decision days plus 40 follow-up days for late outcomes. The same seed gives the same world, so policies can be compared on identical worlds. |
| Scenario family | One of the six public world types: development (standard), sparse geography, cold start (fewer answers known at arrival), delayed dates, shift (different preferences matter), drift (response conditions change on day 35). The official score averages all six equally. |
| Block | A set of consecutive seeds used for one experiment, named by its first seed (block 7400 = seeds 7400–7419). |
| MSMI | *Mutual Second-Meeting Intention*, the official outcome. An introduction counts when the first date happens within 30 days of the introduction and both people say "yes" to a second meeting within 3 days of the date. Score = 100 × qualifying introductions ÷ members who arrived. *Realised* MSMI is what actually happened in a run. |
| Expected wins | The sum, over all introductions a policy made, of each one's exact chance of qualifying, computed offline from hidden simulator values. It has the same average as realised MSMI but much less luck in it (§1.4). |
| Hard fields (dealbreakers) | 11 preferences that must pass in both directions before two people may be introduced: age range, genders, zones, schedule, smoking, children and similar. |
| Soft fields | 7 preference answers, such as relationship goal and pace, that change how likely a "yes" is but never forbid an introduction. A *blank clue* is a soft field that is unknown for one of the two people. |
| Asking (clarification), points | Each day the policy may spend 12 points on questions: all of one member's hard fields at once costs 3 points; one named soft field costs 1 point. |
| Feasible pair | Two available members whose known hard fields pass in both directions and who have never been introduced to each other: a pair the policy may introduce today. (An *allowed pair*, §1.4, is a different, offline count over the whole episode.) |
| Matching | A set of introductions in which nobody appears twice. |
| Greedy baseline | The kit's reference policy. It asks hard bundles in the order members are listed, then introduces the highest-scoring allowed pairs one at a time. |
| Coverage | Share of arrived members who received at least one introduction. It only breaks ties after MSMI and mutual acceptances. |
| Mutual acceptance | Both people answered "yes" to an introduction. |
| Scorer | The part of the policy that estimates how likely each person is to say "yes" to a given partner. |
| Prototype, candidate | The *prototype* is our first complete policy. The *candidate* is the simpler version the experiments support (labelled R1 in §9.6). |
| Coverage boost, degree boost | Multipliers on a pair's score: the coverage boost favours people never introduced; the degree boost favours people with few allowed partners (§6). |
| Online learner, Thompson sampling | A prototype scorer that updated its estimates from replies during the episode, and a way of choosing randomly among plausible estimates to explore. Both were tested and dropped (§9.5–9.6). |
| Oracle | An offline diagnostic that may see hidden simulator values. It measures what is possible; it is never a policy we could submit. |
| Headroom | The most extra improvement an oracle finds when one imperfect part of the policy is replaced by an idealised one. |
| Round 1, Round 2 | Round 1 is this research note. Round 2 (12–18 October) is the build and submission of the policy itself. |

Short labels such as A0–A4, B, C1, S1, S2, R0, R1, F1, F2, V and D0 name policy variants within one results table; each is defined in its table.

---

## 0. Summary

We treat the challenge as **sequential constrained allocation** rather than pair-by-pair compatibility prediction. Each day the policy must:
- decide which unknown fields are worth clarifying;
- then build a valid, non-overlapping matching using only what it can observe.

**What we measured.**
- **Reciprocal feasibility and information availability dominate.** Removing clarification reduced realised MSMI by about **72%** [dev, 240 episodes].
- **Reciprocally eligible alternatives are few** (about 3 per person over an episode; definition in §1.4). The kit's greedy baseline already introduces about **75%** of those pairs [oracle].
- So better ranking has limited opportunity unless clarification first exposes the relevant information. Much of the remaining pair-level variation comes from hidden random factors that the policy cannot see [code, oracle].

**Status: prototype vs evidence-supported candidate.**

| | Tested prototype (first build) | **Evidence-supported Round 2 candidate** |
|---|---|---|
| Feasibility | strict two-way filtering, batch validation | same |
| Hard clarification | dealbreaker bundles, in the order the kit lists members | same |
| Soft clarification | 1-point questions, broad | **broad** (anyone with ≥ 1 feasible partner); the margin rule (ask only when a person's two best options are close) was tested and rejected (§9.6) |
| Scorer | online Beta learner, Thompson draws, personal reply and yes terms | **fixed offline scorecard** (posterior means, no online updates, no personal terms) |
| Matching | most pairs first, then best total, × coverage boost 1.5 × degree boost | most pairs first, then best total; **no coverage boost**; degree boost provisional (no measured effect) |
| Feedback | updates the learner | **effectively unused**: the code still counts replies, but the fixed scorecard is weighted as 10⁶ pseudo-replies, so an episode's few hundred replies cannot change any score materially, and personal terms are off. Availability and past pairs are read from the observable `available` flag and `introductions` list. (Learning changed decisions without improving them, §9.6.) |

> **The current proposal in one box (evidence-supported Round 2 starting candidate).** Exact reciprocal hard-constraint filtering · dealbreaker bundles, then broad soft-field questions for members with ≥ 1 feasible partner · fixed offline directional scorecard · no person-specific online learning · no Thompson sampling · most pairs first, then highest total score · no multiplicative coverage boost · degree-based scarcity adjustment provisional · complete batch validation before output · feedback events effectively unused (availability and introduction history come from the observable state).

**Development results** (hidden-information expected-wins diagnostic, §1.4: not the official metric, but shown there to have the same expectation) [dev].
- **Prototype vs greedy on three disjoint blocks:** +2.7%, +6.3% and +0.2%. Episode-weighted paired mean over 180 episodes: +0.0113 ± 0.0028 per 100 (95% CI +0.0057 to +0.0168). Random-effects estimate: +0.0104 ± 0.0048. The blocks clearly differ (Q = 7.8, 2 degrees of freedom; Q tests whether effects vary between seed blocks more than sampling noise would predict).
- **Principal result.** On a new 120-episode development block (seeds 7400–7419), the candidate improved the validated expected-MSMI diagnostic by **+0.0205 per 100 (+5.5%)**, ± 0.0051 cluster-robust SE, a rough 95% interval of **+2.8% to +8.2%**. This is development evidence, because the block influenced policy selection. Realised MSMI did not confirm the gain at that sample size. The frozen Round 2 candidate will be evaluated once on pre-declared participant-controlled seeds, while realised MSMI on the organisers' held-out worlds remains the official competition outcome.
- **Complexity was active but unhelpful.** Online learning altered 9–15% of daily matchings without improving expected outcomes, so the candidate uses a fixed scorecard (§9.6).
- **The one scenario family with a gain in every block is cold start** (+0.023 ± 0.006 over the first three blocks), where information is scarcest.
- **Realised MSMI does not yet confirm any gain**, and on 120 episodes it cannot resolve one this size: on block 7400 greedy scored higher on realised MSMI (−0.096 ± 0.050). We tested whether the diagnostic was at fault. The formula is the simulator's exact success probability (source derivation; 360,000 replays agree within sampling error), and the realised-minus-expected gap over all 1,980 development episodes is within chance (§1.4). Under the variance observed, realised MSMI over 120 episodes detects only gains near 38% (80% power), against about 4% for paired expected wins (§9.7).

**What remains open.**
- A relaxed offline oracle suggests limited remaining opportunity from ranking alone. We treat it as an optimistic, simulator-specific diagnostic, **not a formal bound** on all sequential policies.
- **Late headroom diagnostic [oracle, dev; new seeds 7500–7519, used for no tuning].** After the candidate was chosen, offline oracles measured how much several idealised mechanisms could still add over it (expected wins per 100, ± one cluster-robust SE; percentages of the greedy baseline):
  - perfect pair-success probabilities: about +0.6% (+0.0021 ± 0.0027);
  - every hard and soft answer revealed free: about +0.7% (+0.0023 ± 0.0039);
  - both together: about +1.2% (+0.0042 ± 0.0041);
  - a 10-day look-ahead that also knew the real future arrivals and departures, compared with the same perfect information decided one day at a time: no measurable gain (+0.0001 ± 0.0027; seeds 7500–7509).
  
  No material headroom was found in the tested scoring, clarification or 10-day timing mechanisms. This bounds those mechanisms; it does not prove that every sequential policy is equivalent, or that the organisers' worlds have the same ceiling. On the same block the candidate itself was +4.2% over greedy (+0.0149 ± 0.0040), replicating the direction of the 7400 result. Round 2 therefore prioritises reliability, runtime safety and the frozen confirmation run over more planning complexity. Code and data: `experiments/headroom.py`, `HEADROOM.md`.
- **Feedback.** Online learning from replies changed 9–15% of daily matchings but did not improve expected wins (H7). Population-level shift detection is deferred; in the late diagnostic, even the true shifted weights added nothing measurable in the shift scenario (−0.0022 ± 0.0064).
- Round 2 will freeze the policy, then evaluate it once on a pre-declared, participant-controlled seed block (§9.7), reporting realised MSMI, coverage, mutual acceptances, clarification cost, waiting time, runtime and invalid-episode counts.

> **What this note does not claim.**
> - That the candidate has already beaten the kit on the organisers' held-out realised MSMI.
> - That expected wins is available to the submitted policy (it uses hidden values and exists only offline).
> - That the relaxed oracle is a formal upper bound on every sequential policy.
> - That all feedback learning is useless: only that the tested online learners did not improve decisions.
> - That no sequential policy could beat the candidate: the late diagnostic bounds only the mechanisms it tested.
> - That synthetic outcomes are evidence about real relationship success.

**Contents.** Terms (above) · 0 Summary · 1 Problem interpretation · 2 Hypotheses · 3 Reciprocal feasibility · 4 Clarification policy · 5 Probability model · 6 Allocation · 7 Missing and delayed data · 8 Existing work · 9 Baselines, ablations and results · 10 Failure cases · 11 Observations on the problem framing · 12 Reproducibility and provenance · References · Appendices A–D

---

## 1. Problem interpretation

### 1.1 Daily decision [rule]
Each day the policy makes two decisions.

**Ask.** Spend up to 12 points: the dealbreaker bundle costs 3 (all hard fields at once); a named soft field costs 1. Answers arrive immediately.

**Introduce.** Return a batch of pairs. Every pair must satisfy:
- all reciprocal hard constraints;
- availability of both people;
- no repeated pair;
- no person used twice in the batch.

The whole batch is validated atomically. An empty batch is valid. One invalid assessed episode makes the submission ineligible for technical ranking, so **validity comes first**.

### 1.2 One introduction's journey [code: `Simulator.advance`]
```
Day t        Introduced; both occupied.
Day t+1..t+7 Each person replies yes/no on a random day, or not at all (a per-person reply probability, 0.55–0.98).
   ├─ any "no" or no reply → ends; the pair can never be repeated; both available again from day t+8
   └─ both "yes" → date 1–14 days after the later reply (+5–12 days in the delayed scenario);
                   both occupied until 6 days after the date
        ├─ the date does not happen (22%) → ends
        └─ the date happens → each answers "second date?" 1–5 days later, or not at all
             (same per-person reply probability as above)
             └─ both "yes" → both paused. Counts for MSMI only if both answers arrive within 3 days
                and the date is ≤ 30 days after the introduction [rule].
```
The 8-day occupancy is set at introduction for both people, whatever their answer.

### 1.3 The pool (development scenario, 10 worlds) [dev]
| Group | People per world | Can be introduced? |
|---|---|---|
| All hard fields known on arrival | 69.9 | yes |
| Hard fields unknown but askable (each misses 7–11 of 11; none misses only 1–2) | 65.4 | after one 3-point ask |
| Declined at least one hard field | 64.6 | never (declined answers are never inferred) [rule] |

About 70% arrive on day 0 and the rest by day 20. About 12% leave on a day drawn uniformly from 22–60, fixed when the person is generated and independent of their profile [code: `generate`].

### 1.4 Binding constraints
**Definition (used in §0 and here).** An **allowed pair** is a unique unordered pair that satisfies:
- both people arrived by day 59;
- neither declined a hard field;
- the pair satisfies all reciprocal hard constraints **after full revelation of hidden hard answers**;
- *regardless* of whether both people are ever simultaneously available.

This is an offline diagnostic [oracle], computed for the development scenario on 10 worlds (`experiments/theory_ceilings.py`).

| Constraint | Measurement | Consequence |
|---|---|---|
| Unknown hard fields | no-asks baseline: realised MSMI −72% (240 episodes) [dev] | Clarification is essential |
| Few allowed pairs | 124 per world, ≈ 3 per person; greedy introduces 92 of them (75%; 98% in sparse) [oracle] | Ranking matters only where a choice exists |
| Choice exists mainly early | after day 20, ~105 people are free and fully known each day, but only ~1–2 currently feasible pairs exist among them [dev] | Ranking matters on day 0 and while newcomers arrive |
| Why allowed pairs go unused | 53% one person already paused · 27% one person left · 20% one person was occupied [oracle] | Only the last two are addressable (timing, option value) |
| Outcome noise | ~1 qualifying outcome per episode; detecting 1.0 → 1.5 needs ~79 episodes per policy [dev] | Compare with a low-variance diagnostic (below), then confirm on MSMI |

**Expected wins (development diagnostic, not the official metric).**
- **In plain words.** Each introduction is like a lottery ticket with its own chance of winning. Realised MSMI records which tickets happened to win. Expected wins adds up each ticket's exact chance, as the simulator defines it. Over hundreds of introductions both give the same average, but expected wins removes the luck of which particular tickets won. The formal argument follows.
- For each introduced pair, we compute its success probability from the simulator's outcome formula, using hidden per-person values and integrating over the shared pair term with 5-point Gauss–Hermite quadrature. We then sum these probabilities.
- **Numerical check:** the 5-point integration was compared with a 60-point Gauss–Hermite reference on 3,000 random pairs from development worlds. Maximum absolute difference 4.1 × 10⁻⁷; mean relative difference 0.001% [dev, `checks_v3.py`]. This validates the numerical integration; the completeness of the formula is checked next.
- **Delayed scenario: 30-day date rule.** The date delay is max(two reply delays U{1..7}) + U{1..14} + U{5..12}, drawn independently of the pair, the day and the policy [code]. So P(date within 30 days) is an exact constant: 5,368 / 5,488 = 0.9781. The diagnostic multiplies by it from the fourth block (7400) onwards. Earlier blocks overstate delayed-scenario expected wins, and their differences, by exactly 2.2%. Relative comparisons are unaffected.
- **Check against outcomes:** over 840 episodes of the fourth block (7400), mean expected wins 0.386 vs realised MSMI 0.357 per 100. Per-policy realised minus expected values vary in sign across blocks for every policy, including greedy, so we see no sign of a policy-specific bias in the diagnostic.
- **Exactness check against the simulator** [dev, `experiments/pwin_check.py`]. We replayed the kit's own `advance()` and `metrics()` code on 1,200 random pairs (eligibility does not enter the outcome code, so it was bypassed; 200 per scenario family, assignment days 0, 10 and 40), each under 300 independent outcome seeds: 360,000 introductions. Simulated wins 3,756 vs formula 3,743.4 (ratio 1.003). Per family, the ratios were 0.97–1.03 and every |z| < 0.9. **Exactness comes from the derivation; the replay validates it.** Reading the source [code] shows that outcomes are drawn once at assignment from a stream keyed on seed, pair and day, that leaving after an introduction does not affect its outcome, and that every outcome lands before day 100. So the formula is the simulator's exact conditional success probability at the kit commit above. The replays agree with it within sampling error, with no significant family-level discrepancy.
- **Scope of the replay check.** It validates the probability of qualifying *given that an introduction was assigned*. It does not validate eligibility, clarification, allocation or which pairs a policy selects; those are tested in complete simulator episodes (§3, §9).
- **Why that makes it an unbiased estimate of MSMI** [code + algebra]. Write realised MSMI as a sum over introductions of win indicators W_i. Each introduction's luck is a fresh random stream that the policy cannot have seen when it chose the pair (no pair can be repeated). So E[W_i | everything up to assignment] = p_i, the formula's value, even though the policy adapts to earlier feedback. By the tower property (the average of conditional averages equals the overall average), E[Σ p_i] = E[Σ W_i] for any policy, adaptive or not. The episode score is 100 · Σ W_i / N, where N (members arrived by day 59) is fixed by arrivals, not by outcome luck, so E[100 · Σ p_i / N] = E[100 · Σ W_i / N]. Averaging episodes within a family and then the six family means is linear, so the equality carries through to the ranking statistic's expectation. Expected wins is therefore not the official metric, but a validated, unbiased, lower-noise estimate of its expectation under the inspected public simulator. It uses hidden values, so it exists only offline. It removes only the outcome-luck variance, which is why its paired standard errors are about 10× smaller. Across all 1,980 development episodes the realised-minus-expected gap is −0.037 ± 0.039 per 100 (cluster-robust over the 50 seeds, z = −1.0), consistent with this.
- It is unavailable to the policy. We use it only to reduce outcome noise when selecting candidates. Claims of improvement are judged on untouched seeds (§9.7).

---

## 2. Hypotheses
- **H1 (clarification).** Spending otherwise-unused budget on soft-field questions reduces blank clues and improves scorer discrimination. It improves wins only where a choice exists.
- **H2 (reply behaviour).** Because each person's reply probability applies at both the introduction and the second-date stage [code], down-weighting people with a record of non-reply should improve expected wins. *Not supported so far (§9.5).*
- **H3 (global allocation).** Lexicographic maximum-cardinality, maximum-weight matching avoids known same-day failures of best-pair-first selection. Whether this produces measurable episode-level gains in the thin public simulator is an empirical question.
- **H4 (limited discounting).** For stationary public scenarios, equal weighting minimises variance. The drift scenario shifts the common intercept on day 35, so equal weighting can bias absolute probabilities. γ = 1 is a default, not a proved optimum (§5.5). It is moot for the candidate, which does not learn online.
- **H5 (headroom).** Under our relaxed oracle, sequential scarcity leaves roughly ≤ 40% improvement over the public baseline; oracle soft-field ranking alone leaves about 8%. Stronger oracles were run later (§0, late headroom diagnostic) and found little remaining headroom in the tested mechanisms.
- **H6 (dynamic option value, provisionally unsupported).** Accounting for what an introduction takes from other people's future options (8+ day occupancy, departures, arrivals) would beat same-day matching. A 10-day oracle with the real future arrivals and departures found no measurable gain over same-day matching on seeds 7500–7509 (§0). This bounds the tested look-ahead; it does not establish that every sequential policy is equivalent.
- **H7 (closed-loop feedback, tested and unsupported for the tested mechanisms).** Post-introduction events help only if their updates change later decisions for the better before the horizon ends. Population and personal online learners changed 9% and 15% of daily matchings without improving expected wins (§9.6), so the candidate does not learn from feedback. Population-level shift detection remains a deferred experiment, not part of the candidate.

---

## 3. Reciprocal feasibility
**Definition.** For hard rule *k*, let c_k(i→j) ∈ {0,1}. A pair is feasible on day *t* when

  e_ij(t) = ∏_k c_k(i→j) · c_k(j→i) · [both available, arrived, fully known, same pool] · [never introduced].

- Unknown values never pass. Declined values are never inferred [rule].
- **Implementation:** each rule is evaluated as a 0/1 column over all people (numpy), and the columns are combined with logical AND.
- **At the evaluated scale (200 people)** the daily filter takes ≤ 26 ms, and the slowest full simulated day took 45 ms in-process [dev]. A scaling benchmark (Appendix A) shows the column method is the fastest of four equivalent implementations, at no cost at small scale.

**Batch validation before output.** Every pair:
- passes the kit's official `eligibility()`;
- has two distinct IDs that are arrived, available and in the same pool;
- has not been introduced before.

Also, no member appears twice in the batch, the ask budget is respected, and output is plain JSON (no NumPy types, NaN or Infinity). Local tests additionally pass every proposed batch through the public simulator's validator. All of our development episodes (> 1,500) ran with **0 invalid actions**.

---

## 4. Clarification policy
**Measurements.**
- The kit baseline spends 199 of 720 points per episode [dev]; after about day 17 no askable hard-field gaps remain.
- An oracle test of dealbreaker-ask *order* (180 episodes per asker) found differences ≤ ~1% in mutual acceptances, within noise [dev].
- About 62% of soft clues are blank at decision time (82% in cold start) [dev, 15 worlds × 6 scenarios].

**Rules (a decision-relevance heuristic, not a full value-of-information computation):**
1. **Hard bundle (3 points)**, in the order the kit lists members, for available askable people. In Round 2 we will prioritise people whom ready members' stated preferences already accept, a cheap exact half-check using always-visible age, gender and zone.
2. **Soft fields (1 point each) with the remaining budget**, in field order goal → pace → lifestyle → conversations.
3. **Broad rule (current):** ask soft fields of any available, fully known person with ≥ 1 currently feasible partner.
4. **Matching-margin rule (tested, rejected in §9.6):** ask only if the person's second-best edge score is ≥ 0.6 × their best. A soft answer moves odds by roughly ×0.7–×1.4, so it could then reverse their top choice.
5. **Never ask** declined, unavailable or paused people [rule].

We do not currently ask the three soft fields whose estimated effect was negligible in public development data (Information Value ≤ 0.009 in every tested scenario). We keep them in the observation pipeline so a shifted private scenario cannot cause a parsing or correctness failure.

**Theory.** Adaptive-submodularity results (Golovin & Krause, JAIR 2011) motivate greedy one-question-at-a-time querying when diminishing-return assumptions hold [motivation]. We do not claim our full matching objective satisfies those conditions. The simulator ablations are the evidence.

**Rejected:** filling blank answers with guesses from "similar users".
- Not allowed: "never fabricate a default preference"; declined answers "must not be inferred" [rule].
- Uninformative: soft fields are drawn independently per person [code].

---

## 5. Probability model (the scorer)

### 5.1 Target and operational score
By the chain rule, a qualifying outcome needs:

  P(win) = P(both reply) · P(both yes | replied) · P(date) · P(both answer again) · P(both yes again) · P(both on time, date ≤ 30 days)

- **[code]** Each person's reply probability r_i is a single hidden value. The simulator uses it both for the introduction reply and for the second-date answer (`Simulator.advance`). The probability of the date, of an on-time answer, and the 30-day rule do not depend on visible fields.
- **Tested prototype score:**

  **s_prototype(A, B) = P̂(A yes | clues, A) · P̂(B yes | clues, B) · r̂_A² · r̂_B²**

  The square follows from the inspected mechanism (the same reply probability acts at both stages). Each person's r̂ was estimated from both kinds of answer event.
- **Evidence-supported candidate score:**

  **s_candidate(A, B) ∝ P̂_fixed(A yes | clues, A) · P̂_fixed(B yes | clues, B)**

  with P̂_fixed from the fixed offline scorecard. Personal reply estimation did not improve expected wins (§9.5–9.6), so the candidate removes the personal r̂ terms. A population-level reply factor multiplies every pair by the same constant, so it cannot change the ranking and is omitted.
- This is a **ranking approximation** to the full journey probability. We omit factors that we cannot estimate reliably online or that are constant across pairs under the inspected simulator: the shared pair term, the visible-goal term at the second stage (§5.3), and the date-timing distribution. The approximation is judged against expected wins, not assumed correct.

### 5.2 Measured conditional probabilities [dev: kit baseline, development, 30 worlds, 5,468 reply chances; fields as known at decision time]
| Quantity | Value (n) |
|---|---|
| P(reply) | 0.76 (5,468) |
| P(reply \| replied last time) / P(reply \| silent last time) | 0.77 (2,361) / 0.68 (798) |
| P(yes \| replied) | 0.48 (4,132) |
| P(yes \| yes last time) / P(yes \| no last time) | 0.51 (815) / 0.44 (1,009) |
| P(yes \| goal same) / P(yes \| goal different) | 0.61 (758) / 0.37 (718) |
| P(yes \| goal and pace both same) | 0.70 (257); additive log-odds prediction 0.70 |
| P(date \| both yes) | 0.76 (400) |
| P(second yes \| date): goal same / different / unknown | 0.63 (118) / 0.64 (73) / 0.65 (292) |
| P(second answer within 3 days \| answered) | 0.60 (483) |

Approximate binomial standard errors are √(p(1−p)/n): about ±0.02 for n ≈ 700, and ±0.04–0.06 for the second-stage rows.

**Information Value per field** (yes vs no; 15 worlds per scenario). Information Value is a standard credit-scoring measure of how strongly a field separates "yes" from "no" answers. Scale (Siddiqi 2006): < 0.02 negligible, 0.02–0.1 weak.

| Field | development | shift | cold start |
|---|---|---|---|
| goal | 0.074 | 0.006 | 0.050 |
| pace | 0.002 | 0.066 | 0.004 |
| lifestyle | 0.005 | 0.006 (direction reversed) | 0.012 |
| conversations | 0.005 | 0.017 | 0.006 |
| other three soft fields | ≤ 0.002 | ≤ 0.009 | ≤ 0.008 |

### 5.3 What this implies
1. **Additive log-odds.** The inspected simulator and our conditional measurements support an additive log-odds model for the tested fields. We found no interaction with adequate support, and with ~25 early replies per world and a median of 2 introductions per person, interaction models, per-user vectors and tree ensembles are not justified.
2. **Selection at the second stage.** The simulator contains a visible-goal term at the second stage [code], yet it is invisible in observed data. Our interpretation: pairs with different goals reach a date mainly when their shared pair term is favourable, and that term also raises second-stage answers. Modelling the whole chain over all introductions is the standard remedy for this kind of post-selection bias (ESMM; Ma et al., SIGIR 2018) [motivation].
3. **Habits persist.** Reply behaviour and yes-propensity carry over between a person's introductions, but there are ~2 introductions per person, so strong shrinkage is needed.
4. **The informative field depends on the scenario** (goal normally, pace under shift). The prototype learned the weights online from an offline prior. The ablations (§9.5–9.6) favour a fixed offline scorecard, and adaptive weights stay only if a shift-specific test shows outcome value.

### 5.4 Estimator and reproducibility (prototype; the candidate keeps only the offline prior means)
**Field effects.** For each field and state (same / different), a Beta belief about the yes-rate.
- The prior mean comes from an offline fit on public training seeds; its strength is k_field = 40 pseudo-replies. Tuning showed 12 was worse (§9.3).
- An unknown clue contributes 0, so a blank is never a mismatch.

**Reply behaviour.** r_i ~ Beta(0.76·10 + answered_i, 0.24·10 + unanswered_i).
- *Answered* and *unanswered* are counted over introduction responses and second-date answers.
- An unanswered event is recorded when the simulator reports `missing_reason = no_response`, on day t+7 for introductions and date+5 for second answers.

**Yes-propensity.** Person *i*'s yes-rate among their *answered* introduction replies, shrunk toward the base rate with 10 pseudo-replies. Non-response never enters it.

**Thompson sampling.**
- At each decision, the policy draws **one** value per population effect and **one** per person, and shares them across all candidate edges that day. There are no independent per-edge draws.
- The generator is seeded deterministically from the day and phase (`7919·day + phase`).
- All beliefs are recomputed from the observed feedback history on every call, so no random state or counts need to be carried in memory, and repeated runs are reproducible.
- Exploration happens only among feasible edges; **a hard constraint is never relaxed.**

**Censoring.** A reply that has not yet arrived is pending, not "no". An unanswered message updates reply behaviour only.

**Calibration.** Mean predicted P(yes) was 0.465 against an observed 0.466 (first tuning round, block 7200, broad asking) [dev]. Reliability curves and the Brier score are planned. (The KS statistic measures separation, not calibration.)

**AUC definition.** All AUC values in this note are **directional introduction-response AUC**:
- the target is whether an introduced person answered yes;
- among answered replies, for introductions made by the policy under test;
- scored with that policy's posterior-mean prediction at decision time.

Because each policy is evaluated on its own introductions, AUCs are comparable only within one run table.

### 5.5 Discounting old replies (argument under the inspected mechanism)
- [code] Field effects, personal reply probabilities and yes-propensities are fixed within an episode in every public scenario. The shift scenario changes the weights from day 0; the drift scenario subtracts the same 0.5 from everyone's log-odds from day 35, which leaves each person's ordering of options unchanged.
- For a constant rate *p* estimated by a weighted mean with Σw_i = 1, the variance is p(1−p)·Σw_i², and Σw_i² ≥ 1/n with equality only for equal weights (Cauchy–Schwarz). In scenarios with no within-episode change, discounting therefore adds variance without reducing bias.
- The drift scenario breaks strict stationarity. Its day-35 intercept shift leaves each person's ordering of options unchanged, but equal weighting biases absolute probabilities, and products of two directional probabilities need not keep their exact order. So γ = 1 is a development default, not a general result.
- Where the environment does drift (a real service), exponential smoothing with γ = 1 − α, where α = (−q + √(q² + 4q))/2, is optimal for a local-level model with signal-to-noise ratio *q* (Muth, JASA 1960) [motivation]. *q* = 0 gives γ = 1.
- **Caveat.** If private scenarios contained within-episode drift in field effects, this choice would be wrong. An empirical check (γ ∈ {0.95, 0.98, 1}) is planned.

### 5.6 Offline ceilings for discrimination [oracle, 15 worlds per scenario]
| Predictor | Directional AUC |
|---|---|
| Our policy's scorer (dev runs, by asking rule; §9.3–9.6) | 0.54–0.60 |
| True soft-field effects, all four fields known | 0.61–0.65 |
| + each person's hidden yes-propensity | 0.70–0.72 |
| + the shared pair term | 0.74–0.75 |

Even with the inspected hidden traits, substantial variation remains stochastic. The gap between our scorer and the true-soft-field row comes mostly from blank clues, which is why clarification and scoring are designed together.

---

## 6. Allocation
**Objective (lexicographic).** Each day, first maximise Σ x_ij (the number of introductions). Then, among maximum-cardinality matchings, maximise Σ v_ij x_ij, subject to Σ_j x_ij ≤ 1 and x_ij ∈ {0,1}.
- Solved with networkx `max_weight_matching(maxcardinality=True)` (Edmonds' blossom algorithm).
- Weights are integers, ⌊10⁹ · v⌋ + 1, so differences of about 10⁻⁹ in score are preserved. Ties are broken by networkx's deterministic processing of a deterministically built graph.
- **Why cardinality first:** every feasible introduction has positive expected value in the simulator, and our measurements show ranking differences are small relative to one more introduction.

**Weights.** v_ij = s(i, j) · u_i · u_j, where
- u_i = c_new (if person *i* has never been introduced) × (1 + c_deg / d_i);
- d_i = number of currently feasible partners;
- the tested prototype used c_new = 1.5 and c_deg = 0.5. **The candidate uses c_new = 1** (the coverage boost removed). c_deg is provisional: removing it changed expected wins by +0.0009 ± 0.0018 (§9.6).

Coverage is only a tie-breaker after MSMI and mutual acceptances [rule]. A multiplier that trades estimated primary value for coverage is therefore an objective mismatch. We removed it for that reason; the small favourable result (§9.4) is consistent with this but does not prove it on its own. Coverage may still break exact ties between matchings of practically equal value.

**Why not best-pair-first.** Kit example: best-pair-first gives 0.95; the best set gives 1.30 [rule]. Greedy can lose up to half the optimum.

**Opportunity cost (H6, first test).** v′_ij = v_ij − λ·(O_i^(−j) + O_j^(−i)), where O_i^(−j) = Σ_{k≠j} v_ik / d_k is the value of person *i*'s other options, weighted by the scarcity of those partners. Result: §9.4.

**Fairness.** We considered and rejected upper score cutoffs. Real systems protect disadvantaged users with floors or quotas, not caps (FairRec, FA*IR). In dating apps, attention is spread because popular users become congested (Rios, Saban & Zheng, MSOM 2023) [motivation], and the simulator has no congestion. Details: Appendix C.

---

## 7. Missing and delayed data
| Situation | Rule |
|---|---|
| Unknown hard field | Never passes; ask first |
| Declined hard field | Never introduced, never asked, never inferred |
| Unknown soft field | Contributes 0; ask if relevant |
| Reply not yet arrived | Pending, not "no" (right-censoring) |
| Reply never arrives | Updates reply behaviour only |
| Second-stage answers (up to ~26 days later) | Recorded per stage (below) |
| Member unavailable with no active introduction | Treated as currently non-actionable; we do not infer the reason |
| Delayed scenario | Longer occupancy; dates > 30 days after introduction cannot qualify (not controllable) |

**Offline interpretation of feedback events.** The candidate does not learn from these events (its scorecard is fixed). The table separates them by stage for research analysis, funnel measurement and the prototype's evaluation.

| Event | What it is evidence about | Prototype use | Candidate |
|---|---|---|---|
| Introduction reply missing (day t+7) | that person's first-stage reply probability | reply habit | not used by the candidate |
| Introduction "no" | that person's acceptance of this partner (not reply failure) | field counts, yes-propensity | not used by the candidate |
| Introduction "yes" | reply happened; acceptance | field counts, yes-propensity, reply habit | not used by the candidate |
| Both yes, date did not happen | date occurrence (constant 0.78 for every pair [code]) | – | not used by the candidate |
| Second-stage answer missing | second-stage reply (same hidden reply probability [code]) | reply habit | not used by the candidate |
| Second-stage "no" / "yes" | second-meeting preference | – | not used by the candidate |
| Late second-stage "yes" (> 3 days) | positive preference, but no MSMI credit | – | not used by the candidate |

Population-level stage rates (date occurrence, on-time answering) are the same for every pair in the simulator [code]. Learning them online cannot change any ranking, so they were not tested as a learning arm. The arms that could change decisions (field effects, personal habits) were tested in §9.6.

Data per world (development, kit baseline): 172 reply opportunities (65 yes, 65 no, 42 none), 14 mutual acceptances, 11 dates, 2.3 pauses. Only ~25 replies arrive in the first 10 days, so the prior carries the early decisions [dev].

---

## 8. Existing work used, and why
| Piece | Source | Status | Evidence here |
|---|---|---|---|
| Two-way hard filtering | Reciprocal recommenders (RECON; Pizzato et al., RecSys 2010) | implemented | required for validity |
| Column checks | column-store / bitmap index practice | implemented | Appendix A |
| Lexicographic max-cardinality, max-weight matching | Edmonds (1965); networkx 3.4.2 | implemented | §6, §9 |
| Additive log-odds scorer, WoE / IV | credit scorecards (Siddiqi 2006) | implemented | §5.2–5.3 |
| Beta beliefs + Thompson sampling | Chapelle & Li (NeurIPS 2011); Russo et al. (2018); organiser session "Exploration, Exploitation and Online Learning" (6 Oct 2026) | tested; rejected (§9.5–9.6) | – |
| Whole-chain target | ESMM (Ma et al., SIGIR 2018) | motivation | §5.3 |
| No discounting | Muth (1960) | argument under inspected mechanism | §5.5 |
| Prompt matching in thin markets | Akbarpour, Li & Oveis Gharan (JPE 2020) | motivation; 10-day future-aware oracle tested, no measurable gain | H6, §0 |
| Perfect-information benchmark; judge on business outcome | organiser guest session "Building robust ML systems from messy data" (7 Oct 2026) | adopted as diagnostic | §1.4 |
| Grouped hold-out | same session; GroupKFold practice | adopted (seed blocks) | §9.7 |

**Considered and not used:**
- tree ensembles and per-user embeddings (too little data; no detected interactions);
- smart defaults (prohibited and uninformative);
- profile-based peer personas (hidden traits are independent of the profile in the generator);
- upper score cutoffs;
- discounting.

---

## 9. Baselines, ablations and results
All episodes follow the evaluator's protocol: 60 decision days, then 40 follow-up days. Every policy is run on the **same seeds** (paired).

### 9.1 Required baselines [dev, seeds 6000–6039 × 6 scenarios, 240 episodes each]
| Policy | Realised MSMI /100 | Mutual acceptances /100 | Coverage |
|---|---|---|---|
| Kit greedy | 0.410 | 5.45 | 0.335 |
| Kit random-feasible | 0.352 | 5.64 | 0.337 |
| Kit no-asks | 0.117 | 1.53 | 0.115 |

### 9.2 First ablation [dev, same 240 episodes]
| Policy | MSMI /100 | Mutual /100 (vs A0) | Coverage (vs A0) |
|---|---|---|---|
| A0 kit greedy | 0.410 | 5.45 | 0.335 |
| A1 + lexicographic matching | 0.408 | 5.60 (+0.16 ± 0.10) | 0.336 |
| A2 + hard-field asker by predicted unlock | 0.398 | 5.74 (+0.29 ± 0.11) | 0.338 |
| A3 + scarcity / coverage weights | 0.396 | 5.69 (+0.25 ± 0.10) | 0.339 |
| A4 + Thompson learning (old scorer) | 0.400 | 5.64 (+0.19 ± 0.11) | 0.340 (+0.005 ± 0.001) |

All MSMI differences are within about ±0.04 (1 SE). The A2 mutual-acceptance gain **did not replicate** on new seeds (§9.9).

### 9.3 Second-version scorer ("v2", the prototype's scorer) and first tuning round [dev; expected wins per 100 arrived members]
"Soft asks (≥ 2 options)" means soft questions only for people with at least two currently allowed partners; "≥ 1" means at least one.

| Seed block | Comparison | Expected wins (paired, vs reference) | AUC | Blank clues |
|---|---|---|---|---|
| 7100–7109 | kit greedy → v2 + soft asks (≥ 2 options) | 0.375 → 0.385 (+0.0103 ± 0.0020, +2.7%) | 0.541 → 0.553 | 70% → 59% |
| 7200–7209 | kit greedy → v2 + soft asks (≥ 2 options) | 0.360 → 0.383 (+0.0228 ± 0.0065, +6.3%) | 0.537 → 0.565 | 70% → 57% |
| 7200–7209 | soft asks for ≥ 1 option (vs ≥ 2) | +0.0009 ± 0.0018 | +0.024 ± 0.006 | 57% → 41% |
| 7200–7209 | prior strength 12 (vs 40) | **−0.0118 ± 0.0027** | −0.009 ± 0.006 | – |
| 7200–7209 | yes-propensity strength 3 (vs 10) | +0.0004 ± 0.0021 | −0.008 ± 0.006 | – |
| 7200–7209 | yes-propensity off | +0.0005 ± 0.0029 | −0.016 ± 0.006 | – |

Realised mutual acceptances did **not** rise (7100 block: −0.20 ± 0.17 per 100 vs greedy). The expected-wins gain does not come from more first "yes" answers. Block 7300 (§9.5) suggests it does not come from the reply-behaviour term either; isolating its source is a Round 2 task.

### 9.4 Allocation: option value and boosts [dev, seeds 7300–7309 × 6 scenarios, 60 paired episodes per policy]
All comparisons are paired against the current best ("B" = scorer v2 + soft asks for ≥ 1 option, with both boosts).

| Policy | Expected wins /100 | vs B | Coverage vs B | Mutual /100 vs B |
|---|---|---|---|---|
| Kit greedy | 0.3924 | −0.0006 ± 0.0047 | −0.0018 ± 0.0007 | −0.16 ± 0.15 |
| **B** current best | 0.3930 | – | – | – |
| A1 no boosts (plain lexicographic matching) | 0.3938 | +0.0007 ± 0.0021 | −0.0024 ± 0.0006 | −0.09 ± 0.08 |
| A2 no coverage boost (c_new = 1) | 0.3971 | +0.0041 ± 0.0027 | −0.0013 ± 0.0005 | −0.11 ± 0.10 |
| A3 opportunity cost, λ = 0.5 (no boosts) | **0.3980** | **+0.0050 ± 0.0027** | −0.0014 ± 0.0005 | −0.08 ± 0.09 |

- **On this block, B did not beat greedy** (+0.0006 ± 0.0047). This is the third disjoint block; pooled results are in §0.
- **The coverage boost buys a little coverage (+0.0013) at a likely cost in expected wins (≈ −0.004, about 1.5 SE).** Optimising a tie-breaker can sacrifice the primary objective. Round 2 default: no coverage boost, or a boost applied only within a narrow score tolerance.
- **Opportunity cost:** after controlling for the removal of the coverage boost, the heuristic showed no clear extra benefit (A3 − A2 paired: +0.0009 ± 0.0007). A one-line penalty is a weak proxy for option value. A later 10-day future-aware oracle found no measurable timing gain (§0, H6), so one-day rollout and selective waiting are not current priorities unless new evidence contradicts that result.

### 9.5 Clarification rule and scorer complexity [dev, same 60 episodes]
| Variant (vs B, paired) | Expected wins /100 | AUC* | Mutual /100 | Clarification cost / episode |
|---|---|---|---|---|
| C1 matching-margin asker | +0.0003 ± 0.0016 | −0.024 ± 0.007 | −0.02 ± 0.08 | **225** (B: 274) |
| S1 simple fixed scorecard (offline prior only; no learning, no reply or yes-propensity terms) | +0.0010 ± 0.0033 | **+0.027 ± 0.008** | **+0.34 ± 0.14** | 273 |
| S2 posterior mean instead of Thompson draws | −0.0029 ± 0.0032 | +0.009 ± 0.006 | **+0.38 ± 0.14** | 274 |

\*AUC is measured on each policy's own introductions (§5.4), so differences partly reflect which pairs were introduced.

- **Margin asking** reduced clarification spending by about 18% with no detected overall change in expected wins. But it lost in cold start (−0.011 vs broad asking), and lower clarification cost only matters after exact ties on the preceding metrics [rule]. On the fourth block, broad asking beat it (§9.6), so it is **not adopted**.
- **The online learner and Thompson sampling do not earn their place on this evidence.**
  - A fixed scorecard is at least as good on expected wins and better on mutual acceptances (2.4 SE).
  - Posterior means also raise mutual acceptances (2.7 SE). This suggests that exploration costs early introductions it cannot repay within one episode.
  - The reply-behaviour term (H2) showed no measurable benefit in S1.
- These results led to the candidate tested in §9.6.

### 9.6 Closed-loop feedback and asking rules [dev, new seeds 7400–7419 × 6 scenarios, 120 paired episodes per policy]
R0 = frozen offline scorecard + margin asking + no coverage boost. Errors are **cluster-robust**: 20 seed clusters, because development, delayed and drift share one world per seed.

| Policy | Expected wins /100 | vs greedy | vs R0 | Realised MSMI vs greedy | Ask points |
|---|---|---|---|---|---|
| Kit greedy | 0.372 | – | – | – | 198 |
| R0 frozen scorecard, margin asks | 0.388 | +0.0162 ± 0.0047 | – | −0.121 ± 0.048 | 221 |
| F1 = R0 + population field learning | 0.388 | +0.0164 | +0.0002 ± 0.0017 | – | 221 |
| F2 = F1 + personal reply / yes learning | 0.386 | +0.0138 | **−0.0023 ± 0.0014** | – | 220 |
| V = R0 with matching-value (VOI) asking | 0.389 | +0.0175 | +0.0013 ± 0.0011† | – | 230 |
| D0 = R0 without degree boost | 0.389 | +0.0170 | +0.0009 ± 0.0018† | – | 221 |
| **R1 = frozen scorecard, broad asks (candidate)** | **0.392** | **+0.0205 ± 0.0051** | **+0.0043 ± 0.0019** | −0.096 ± 0.050 | 270 |

† plain paired SE.

**Does feedback change decisions?** On the same state each day, we compared the learner's matching with the frozen scorecard's.
- Population field learning changed the matching on **8.6%** of decision days (4.1% of pairs).
- Adding personal learning raised that to **14.9%** (7.6% of pairs).
- Neither improved expected wins, and personal learning was slightly worse.
- **Conclusion for this simulator: within a 60-day episode, online learning does not repay its variance and delay.** The candidate therefore uses a fixed offline scorecard.

**Other findings.**
- Broad soft asking beat margin asking (+0.0043 ± 0.0019).
- A first matching-value (VOI) asker was +0.0013 over margin asking, but was not compared with broad asking. It stays a Round 2 experiment.
- The candidate's gain over greedy is spread across all families except sparse: cold start +0.013, delayed +0.021, development +0.030, drift +0.030, shift +0.027, sparse +0.002.

### 9.7 Development vs confirmation data
- Seeds 6000–6039, 7000–7029, 7100–7109, 7200–7209, 7300–7309 and 7400–7419 are **development sets**: their results influenced choices. Seeds in the 9000s were used for descriptive analyses.
- **Participant-controlled confirmation block, declared now and untouched:** seeds **50000–50019** for each of the 6 scenario families, 120 episodes. These are public-simulator seeds we control, not equivalent to the organisers' held-back worlds. Once run they are no longer untouched: no tuning on them, and every result will be reported. It will be run once, after the Round 2 policy is frozen, reporting realised MSMI with 95% intervals alongside expected wins, coverage, mutual acceptances, clarification cost, waiting time to first introduction, runtime and invalid-episode count.
- **Pre-declared statistics and power.** On block 7400 the paired standard error over 120 episodes was 0.050 per 100 for realised MSMI and 0.0051 for expected wins. At 80% power these detect differences of about 0.14 (≈ 38% of greedy) and 0.014 (≈ 4%). Under that variance, a 10% realised-MSMI gain would need roughly 1,700 episodes to detect. These figures hold under the variance observed on that block, not universally. We therefore declare now: (1) the **primary participant-controlled policy-selection statistic** is the paired expected-wins difference on seeds 50000–50019, a validated low-variance estimate of expected MSMI under the inspectable public simulator (§1.4). The **official competition outcome** remains realised MSMI, determined by the organisers' held-out evaluation; (2) realised MSMI on the same 120 episodes is reported with its interval, whatever its sign; (3) if runtime allows, an extension block, seeds **50020–50299** (1,680 further episodes, also untouched), is run once with the same frozen policy so realised MSMI alone can resolve a gain near 10%. Neither block is used for any retuning.
- Seed blocks are **disjoint**, not necessarily independent: within one seed, the development, delayed and drift scenarios share the same generated world, and outcome draws are keyed on (seed, pair, day) [code: `rand_for`]. So per-scenario results within a block are correlated.
- **Multiple comparisons.** We tested many variants, and all are reported. The largest observed development gains are subject to selection bias, so we treat them as provisional until the confirmation run.

### 9.8 Results by scenario [dev, seeds 7200–7209; expected wins per 100]
| Policy | cold start | delayed | development | drift | shift | sparse |
|---|---|---|---|---|---|---|
| Kit greedy | 0.357 | 0.444 | 0.443 | 0.417 | 0.396 | 0.104 |
| v2 + soft asks (≥ 2) | 0.379 | 0.460 | 0.482 | 0.455 | 0.418 | 0.103 |
| v2 + soft asks (≥ 1) | 0.373 | 0.457 | 0.483 | 0.456 | 0.431 | 0.103 |

- **Sparse shows no gain:** there is almost no choice to exploit.
- On the 7100 block, shift was the weakest scenario for v2 (0.411 vs 0.416 for greedy). There, the development prior points lifestyle the wrong way.
- Clarification cost: about 200 points per episode for greedy, 227 with soft asks (≥ 2), 272 (≥ 1), out of 720.

### 9.9 Retrospective: what we got wrong
- **An unreplicated gain.** The asker's mutual-acceptance gain (+0.29 ± 0.11) did not repeat on new seeds; an oracle asker gained ≤ ~1%. *Lesson:* replicate before believing.
- **Discounting "for drift"** was unnecessary under the inspected mechanism (§5.5).
- **Random feasible pairs** matched our full prototype on mutual acceptances. A simple baseline can be as good as a complex model on the outcome that matters, as the organiser session "Building robust ML systems from messy data" (7 Oct 2026) stressed.
- **Better prediction ≠ more wins.** Broader asking raised AUC by +0.024 ± 0.006 but not expected wins. A clue only helps where it can change a decision.
- **An apparent timing effect.** Introductions made on days 35–49 once appeared to almost never succeed (0 of ~430 in two world sets), although their expected success was normal (≈ 1.0%). On 60 fresh worlds the rate was 1.05% (7 of 669): it was chance. Assignment day shows no reliable effect outside the drift scenario's built-in day-35 change.
- **Complexity that did not pay.** The online learner, Thompson sampling, personal habit terms, the coverage boost and the margin asker each looked principled. None beat a simpler alternative (§9.4–9.6).
- **Realised MSMI disagreed with the diagnostic on one block (7400).** Rather than explain it away, we tested the diagnostic itself: it is the exact success probability, and replays agree within sampling error. The disagreement is outcome luck (§1.4).
- **Corrected early numbers.**
  - An early estimate of 20–30 introductions per day was wrong: the real maximum is 9–19 per day.
  - The number of pairs passing the gender, zone and age checks on day 0 was 2,996, not 3,215 (a bug in our age check).
  - An early claim that our bit-set eligibility filter was 60× faster was measured against the kit's slow reference checker. Against a row-by-row check that stops at the first failing rule, it is about 2× faster at 10,000 people and about equal at 200 (`experiments/bench_filtering.py`).

---

## 10. Expected failure cases and defences
| # | Failure | Defence | Status |
|---|---|---|---|
| F1 | Sparse supply (coverage ceiling ≈ 0.16 in sparse) | Prompt same-day matching and global allocation. A 10-day future-aware oracle found no measurable gain from waiting in the tested worlds (H6) | Implemented |
| F2 | Withheld answers (≈ 65 of 200 decline a hard field) | Never inferred or asked; kept in the denominator | Implemented; 0 invalid actions in > 1,500 dev episodes |
| F3 | Delayed feedback (replies ≤ 7 days, second answers ≤ ~26 days) | Pending ≠ no; prior carries early decisions | Implemented |
| F4 | Competition for one person | Global matching prevents duplicate assignment and handles same-day competition exactly. A future-aware oracle found no measurable added value from 10-day look-ahead | Implemented; degree boost provisional |
| F5 | Shifted weights | Fixed scorecard as the robust default. Round 2: a gradual blend of two offline weight sets, weighted by the likelihood of observed replies, kept only if it helps shift without harming the other five families | Fixed default implemented; adaptation planned |
| F6 | Sparse personal history (~2 introductions each) | The candidate uses no person-specific learned parameters; population- or scenario-level adaptation is adopted only after it shows incremental outcome value | Implemented |
| F7 | Invalid output | Batch validation (§3); official checker; budget read from state | Implemented and measured (0 invalid) |
| F8 | Timeout (10 s per call, including start-up) | A monotonic-time guard keeps a fixed output margin. If optimisation has not started by the cutoff, a pre-validated simple matching over the already-computed feasible graph is used. If safe completion cannot be guaranteed, an empty batch is returned. Both paths are tested [plan] | Planned for Round 2. Slowest measured day so far: 45 ms; the guard is not yet in the frozen build |
| F9 | Protocol / format faults: NaN or Infinity, NumPy scalar types in JSON, memory near 1 MiB, missing optional keys, empty population, empty feasible graph, all members unavailable, duplicate IDs, members from several pools, declined soft fields | Explicit casting and guards; unit tests for each case [plan]. The policy returns an empty memory object, because the cumulative observable state (introductions, feedback, ask log) is enough to rebuild its statistics on every call; it uses no persistent filesystem state and no information from other episodes | Empty memory implemented; unit tests planned |
| F10 | Larger hidden pools | Column filtering; matching within connected components | Column filtering implemented and benchmarked (Appendix A); component splitting planned |
| F11 | Over-reading noise | Paired seeds; low-variance diagnostic; untouched confirmation block | Implemented |

---

## 11. Observations on the problem framing
1. **Early negative answers do not release people.** Both people stay unavailable for 8 days after an introduction, even after a definitive "no" on day 1 [code]. In a real service, immediate release after a definitive negative answer could increase opportunity without weakening any eligibility constraint.
2. **Thickness more than ranking.** With ~3 allowed partners per person and ~75% of them already used by greedy [oracle], improvements are more likely to come from information (clarification), timing (before departures) and availability than from better pair ranking.
3. **Outcome noise.** With about one qualifying outcome per episode, rankings on realised MSMI over 20 seeds per family will have wide intervals: in our runs, a paired 95% interval of about ±0.10 per 100 on a baseline of about 0.37, i.e. roughly ±26%. We report low-variance diagnostics alongside MSMI for development, while recognising why an official metric should rest on realised, observable outcomes.
4. **Real-service extensions outside the simulator:**
   - retry members who ignored a message;
   - recompute age from date of birth;
   - let users rate the importance of each preference;
   - churn that depends on match experience.

---

## 12. Reproducibility and provenance
- **Measured-code version.** Every number comes from a script in `experiments/`, with raw per-episode JSONL in `experiments/results/`, at commit `d86ff40ecc561157a6c9b15f6b977acc0e556752`.
- **Research-note version.** This note and its PDF sit in later, document-only commits. We checked the diff: between the measured-code commit and the note commits, no experimental code or raw result used by this note changed; only the note, its PDF, repository housekeeping and separate Round 2 planning files. The full note commit and the PDF's full SHA-256 are recorded in `CHECKSUMS.txt` in the repository (a file cannot contain its own checksum).

| Section | Script |
|---|---|
| §9.1–9.2 | `run_baselines.py`, `run_ablation.py` |
| §9.3 | `test_scorer_v2.py`, `tune_v2.py` |
| §9.4–9.5 | `tune_v3.py` |
| §9.6 | `tune_v4.py`, `tune_v4b.py` |
| §5.2 | `funnel_probs.py`, `woe_iv.py` |
| §5.6 | `scorer_data.py` |
| §1.4 | `theory_ceilings.py`, `why_unused.py`, `daily_cost.py`, `checks_v3.py`, `pwin_check.py` |
| Appendix A | `bench_100k.py` |

- **Commands:** run from the organiser kit folder, for example `python tune_v3.py 7300 10 development > out.jsonl`, then `python summarise_scorer_v2.py out*.jsonl`.
- **Environment** (checked with `python --version` and the libraries' `__version__`): Python 3.13.16, numpy 2.5.3, networkx 3.4.2 (BSD-3). The experiments use only these plus the Python standard library and the kit. They will be pinned in the Round 2 Docker image.
- **Inference seed:** deterministic per day and phase (`7919·day + phase`).
- **Permitted inputs only.** The policy reads only the observation, clarification results, feedback and its own memory. Hidden values appear only in offline measurement scripts (expected wins, oracle ceilings).
- **AI-assisted tools.** Anthropic Claude was used to help draft and debug experimental scripts, propose and run analyses, prepare mathematical explanations, and edit this research note. Microsoft 365 Copilot was used to review drafts of the note. The author directed the research questions, reviewed the principal experimental results, and made the final methodological and submission decisions. Source-code interpretations, mathematical arguments and generated prose remain subject to the limitations stated in the note. No external AI service is used by the policy during evaluation.

## References
- Akbarpour, M., Li, S., & Oveis Gharan, S. (2020). Thickness and information in dynamic matching markets. *Journal of Political Economy* 128(3).
- Chapelle, O., & Li, L. (2011). An empirical evaluation of Thompson sampling. *NeurIPS.*
- Edmonds, J. (1965). Paths, trees, and flowers. *Canadian Journal of Mathematics* 17.
- Golovin, D., & Krause, A. (2011). Adaptive submodularity: theory and applications in active learning and stochastic optimization. *JAIR* 42.
- Ma, X., et al. (2018). Entire space multi-task model: an effective approach for estimating post-click conversion rate. *SIGIR.*
- Muth, J. F. (1960). Optimal properties of exponentially weighted forecasts. *JASA* 55(290).
- Pizzato, L., Rej, T., Chung, T., Koprinska, I., & Kay, J. (2010). RECON: a reciprocal recommender for online dating. *RecSys.*
- Rios, I., Saban, D., & Zheng, F. (2023). Improving match rates in dating markets through assortment optimization. *MSOM* 25(4).
- Russo, D., Van Roy, B., Kazerouni, A., Osband, I., & Wen, Z. (2018). A tutorial on Thompson sampling. *Foundations and Trends in ML* 11(1).
- Siddiqi, N. (2006). *Credit Risk Scorecards.* Wiley.
- Patro, G. K., et al. (2020). FairRec: two-sided fairness for personalized recommendations in two-sided platforms. *WWW.*
- Zehlike, M., et al. (2017). FA*IR: a fair top-k ranking algorithm. *CIKM.*
- Organiser materials: participant specification 1.0.0 and public kit; session slides "Exploration, Exploitation and Online Learning" (6 Oct 2026) and "Building robust ML systems from messy data" (7 Oct 2026), distributed to participants.

---

## Appendix A. Filter scaling benchmark (outside the evaluated scale)
100,000 synthetic people, 35,051 of them with complete hard fields. All four methods found the identical 7,970,144 feasible pairs [dev, `bench_100k.py`].

| Method | Per new arrival | All pairs |
|---|---|---|
| Pair-by-pair row check | 21.7 ms | 791 s |
| Group by gender × zone | 8.7 ms | 289 s |
| Bitmap index | 1.4 ms | 35.6 s |
| Column checks | 0.21 ms | 6.1 s |

In an incremental architecture, newcomer processing is one important scaling path. A production system would also need updates for changed preferences, removals, availability and index repair. At 100k, exact matching would run within connected components or use a greedy approximation.

## Appendix B. Scorecard view of the development prior
Each clue adds or removes points from one person's "yes" score for one partner. 600 points means even odds; +20 points doubles the odds. With no clues known, a person starts at 598 points.

| Clue | Same | Different | Unknown |
|---|---|---|---|
| goal | +20 | −11 | 0 |
| pace | +10 | −10 | 0 |
| lifestyle | +7 | −9 | 0 |
| conversations | +2 | −5 | 0 |

## Appendix C. Fairness objectives considered
- Utilitarian sum, Nash welfare (Σ log), α-fairness, max-min.
- Price of fairness: Bertsimas, Farias & Trichakis (*Operations Research* 2011); Dickerson, Procaccia & Sandholm (AAMAS 2014).
- Group fairness in online matching: Ma, Xu & Xu (AAMAS 2022).
- Code read: FairRec (`FairRec_www_2020` @ ad2c455) uses exposure caps plus round-robin turns; FA*IR (`fairsearch-fair-python` @ a92a3d6) uses minimum quotas.
- Neither uses caps on the best candidates.
- Optional Round 2 tests: √s and log s + C weights (valid only together with maximum cardinality), and coverage-first weights.

## Appendix D. Further material in the repository
- `EDGE_CASES.md`: 21 edge cases.
- `STRESS_TESTS.md`: 10 stress-world designs.
- `TUNING.md`: every tunable parameter, with its reason, range and risk.
- `SCORER.md`, `TABLES.md`, `NOTES.md`: full working notes.

# The One Introduction Problem: Round 1 Research Note

| | |
|---|---|
| **Team** | solo |
| **Version date** | 8 October 2026 |
| **Repository** | https://github.com/Sga-HQ/The-Sequential-Matching-Problem-Hackathon_round1 |
| **Code and results behind every number** | commit `41051bd8a976976b3ba341aa4bbee86aaa9bee15` |
| **Organiser kit** | participant specification 1.0.0, kit commit `a8e26b35118cfa8e886a02f93984923e43ab64f6` |

**How to read the claims.** Each claim is labelled by the kind of evidence behind it:
- **[rule]**: the organisers' specification.
- **[code]**: behaviour we read in the public simulator source (`kit.py` at the kit commit above).
- **[dev]**: an empirical result on our development seeds.
- **[oracle]**: an offline diagnostic that uses hidden simulator values (never available to the policy).
- **[motivation]**: a literature result that motivates a choice without proving it applies here.
- **[plan]**: a Round 2 experiment.

All uncertainties written ± are **one paired standard error across episodes**. 95% intervals are about ±2 SE.

---

## 0. Summary

We treat the challenge as **sequential constrained allocation** rather than pair-by-pair compatibility prediction. Each day the policy must:
- decide which unknown fields are worth clarifying;
- then build a valid, non-overlapping matching using only what it can observe.

**What we measured.**
- **Reciprocal feasibility and information availability dominate.** Removing clarification reduced realised MSMI by about **72%** [dev, 240 episodes].
- **Reciprocally eligible alternatives are few** (about 3 per person over an episode; definition in §1.4). The kit's greedy baseline already introduces about **75%** of those pairs [oracle].
- So better ranking has limited opportunity unless clarification first exposes the relevant information. Much of the remaining pair-level variation comes from latent stochastic terms that the policy cannot see [code, oracle].

**Our policy combines four mechanisms:**
1. strict two-way feasibility filtering;
2. dealbreaker-first clarification followed by 1-point soft-field questions;
3. a model of directional responses and reply behaviour (built as a shrunk online learner; current evidence favours a simpler fixed scorecard, §9.5);
4. a lexicographic maximum-cardinality, maximum-weight matching with scarcity weights.

**Development results.**
- On disjoint development seed blocks, the policy changed a hidden-information **expected-wins diagnostic** by **+2.7%**, **+6.3%** and **+0.2%** relative to the public greedy baseline [dev].
- These are development results, not official-ranking results. Realised MSMI is too noisy at our sample sizes to confirm them, and those seed sets are no longer suitable for confirmation because they influenced design choices.
- **A third disjoint block showed no gain (+0.2%).** Pooled over the three blocks, the gain is +0.0099 ± 0.0018 per 100 (about +2.6%), with clear heterogeneity between blocks (Q = 7.9, 2 degrees of freedom).
- On that block, a **simple fixed scorecard** was at least as good as the full online model, and removing the coverage boost helped slightly (§9.4–9.5). **Current evidence therefore favours a simpler policy than the one we first built.**

**What remains open.**
- A relaxed offline oracle suggests limited remaining opportunity from ranking alone. We treat it as an optimistic, simulator-specific diagnostic, **not a formal bound** on all sequential policies.
- The main open question is **dynamic option value**: what does occupying a person for 8+ days cost others in a thin, changing graph?
- Round 2 will freeze the policy before evaluating once on an untouched, pre-declared seed block (§9.6). It will report official MSMI, coverage, mutual acceptances, clarification cost, waiting time, runtime and invalid-episode counts.

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
- For each introduced pair, we compute its success probability from the simulator's outcome formula, using hidden per-person values and integrating over the shared pair term with 5-point Gauss–Hermite quadrature. We then sum these probabilities.
- The 5-point integration was checked against a 60-point reference: over 3,000 random pairs, maximum absolute error 4.1 × 10⁻⁷ (mean relative error 0.001%) [dev, `checks_v3.py`].
- The formula omits the delayed scenario's 30-day date rule, so it slightly overestimates in that scenario, equally for all policies.
- It is unavailable to the policy. We use it only to reduce outcome noise when selecting candidates. Final claims must rest on realised MSMI over untouched seeds (§9.6).

---

## 2. Hypotheses
- **H1 (clarification).** Spending otherwise-unused budget on soft-field questions reduces blank clues and improves scorer discrimination. It improves wins only where a choice exists.
- **H2 (reply behaviour).** Because each person's reply probability applies at both the introduction and the second-date stage [code], down-weighting people with a record of non-reply should improve expected wins. *Not supported so far (§9.5).*
- **H3 (allocation).** Lexicographic maximum-cardinality, maximum-weight matching beats best-pair-first. Its advantage over plain maximum cardinality comes from *which* people are matched now versus kept available.
- **H4 (no discounting).** Within an episode, old replies should not be discounted, because the effects they estimate are constant [code] (§5.5).
- **H5 (headroom).** Under our relaxed oracle, sequential scarcity leaves roughly ≤ 40% improvement over the public baseline; oracle soft-field ranking alone leaves about 8%. We will challenge these values with stronger oracle policies, and check whether omitted timing or assignment mechanisms break the relaxation.
- **H6 (option value, main open question).** Accounting for what an introduction takes from other people's future options (8+ day occupancy, departures, arrivals) beats same-day matching with simple scarcity weights.

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
- An oracle test of dealbreaker-ask *order* (180 episodes per asker) found differences ≤ ~1% in both-said-yes, within noise [dev].
- About 62% of soft clues are blank at decision time (82% in cold start) [dev, 15 worlds × 6 scenarios].

**Rules (a decision-relevance heuristic, not a full value-of-information computation):**
1. **Hard bundle (3 points)**, in kit order, for available askable people. In Round 2 we will prioritise people whom ready members' stated preferences already accept, a cheap exact half-check using always-visible age, gender and zone.
2. **Soft fields (1 point each) with the remaining budget**, in field order goal → pace → lifestyle → conversations.
   - **Broad rule (current):** ask any available, fully known person with ≥ 1 currently feasible partner.
   - **Matching-margin rule (tested):** ask only if the person's second-best edge score is ≥ 0.6 × their best. A soft answer moves odds by roughly ×0.7–×1.4, so it could then reverse their top choice.
3. **Never ask** declined, unavailable or paused people [rule].

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
- Our **operational ranking score** is

  **s(A, B) = P̂(A yes | clues, A) · P̂(B yes | clues, B) · r̂_A² · r̂_B²**

  The square follows from the inspected mechanism. Each person's r̂ is estimated from both kinds of answer event.
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

**Information Value per field** (yes vs no; 15 worlds per scenario). Scale (Siddiqi 2006): < 0.02 negligible, 0.02–0.1 weak.

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
4. **The informative field depends on the scenario** (goal normally, pace under shift). So the weights are learned online from an offline prior.

### 5.4 Estimator and reproducibility
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

**Calibration.** Mean predicted P(yes) was 0.465 against an observed 0.466 (tuning round 1, broad asking) [dev]. Reliability curves and the Brier score are planned. (The KS statistic measures separation, not calibration.)

**AUC definition.** All AUC values in this note are **directional introduction-response AUC**:
- the target is whether an introduced person answered yes;
- among answered replies, for introductions made by the policy under test;
- scored with that policy's posterior-mean prediction at decision time.

Because each policy is evaluated on its own introductions, AUCs are comparable only within one run table.

### 5.5 Discounting old replies (argument under the inspected mechanism)
- [code] Field effects, personal reply probabilities and yes-propensities are fixed within an episode in every public scenario. The shift scenario changes the weights from day 0; the drift scenario subtracts the same 0.5 from everyone's log-odds from day 35, which leaves each person's ordering of options unchanged.
- For a constant rate *p* estimated by a weighted mean with Σw_i = 1, the variance is p(1−p)·Σw_i², and Σw_i² ≥ 1/n with equality only for equal weights (Cauchy–Schwarz). Under these conditions, discounting adds variance without reducing bias. We therefore use γ = 1.
- Where the environment does drift (a real service), exponential smoothing with γ = 1 − α, where α = (−q + √(q² + 4q))/2, is optimal for a local-level model with signal-to-noise ratio *q* (Muth, JASA 1960) [motivation]. *q* = 0 gives γ = 1.
- **Caveat.** If private scenarios contained within-episode drift in field effects, this choice would be wrong. An empirical check (γ ∈ {0.95, 0.98, 1}) is planned.

### 5.6 Offline ceilings for discrimination [oracle, 15 worlds per scenario]
| Predictor | Directional AUC |
|---|---|
| Our policy's scorer (dev runs, by asking rule; see §9.7) | 0.54–0.59 |
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
- currently c_new = 1.5, c_deg = 0.5.

These are **empirical policy parameters**, not derived from the ranking rules. Coverage is only a tie-breaker after MSMI and mutual acceptances [rule], so the boost must justify itself on expected wins. Ablations: §9.4.

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
| Second-stage answers (up to ~26 days later) | Used when they arrive |
| Member unavailable with no active introduction | Treated as currently non-actionable; we do not infer the reason |
| Delayed scenario | Longer occupancy; dates > 30 days after introduction cannot qualify (not controllable) |

Data per world (development, kit baseline): 172 reply opportunities (65 yes, 65 no, 42 none), 14 mutual acceptances, 11 dates, 2.3 pauses. Only ~25 replies arrive in the first 10 days, so the prior carries the early decisions [dev].

---

## 8. Existing work used, and why
| Piece | Source | Status | Evidence here |
|---|---|---|---|
| Two-way hard filtering | Reciprocal recommenders (RECON; Pizzato et al., RecSys 2010) | implemented | required for validity |
| Column checks | column-store / bitmap index practice | implemented | Appendix A |
| Lexicographic max-cardinality, max-weight matching | Edmonds (1965); networkx 3.4.2 | implemented | §6, §9 |
| Additive log-odds scorer, WoE / IV | credit scorecards (Siddiqi 2006) | implemented | §5.2–5.3 |
| Beta beliefs + Thompson sampling | Chapelle & Li (NeurIPS 2011); Russo et al. (2018); organiser session "Exploration, Exploitation and Online Learning" (6 Oct 2026) | implemented; value under test (§9.5) | – |
| Whole-chain target | ESMM (Ma et al., SIGIR 2018) | motivation | §5.3 |
| No discounting | Muth (1960) | argument under inspected mechanism | §5.5 |
| Prompt matching in thin markets | Akbarpour, Li & Oveis Gharan (JPE 2020) | motivation; waiting not yet tested | H6 |
| Perfect-information benchmark; judge on business outcome | organiser guest session "Building robust ML systems from messy data" (7 Oct 2026) | adopted as diagnostic | §1.4 |
| Grouped hold-out | same session; GroupKFold practice | adopted (seed blocks) | §9.6 |

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

All MSMI differences are within about ±0.04 (1 SE). The A2 mutual-acceptance gain **did not replicate** on new seeds (§9.8).

### 9.3 Scorer v2 and tuning round 1 [dev; expected wins per 100 arrived members]
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
- **Opportunity cost** was the best variant, but only +0.0009 beyond simply removing the coverage boost, which is not distinguishable from noise. **H6 remains open.** A one-line penalty is a weak proxy for option value. Round 2 will test explicit one-day look-ahead and selective waiting for contested people.

### 9.5 Clarification rule and scorer complexity [dev, same 60 episodes]
| Variant (vs B, paired) | Expected wins /100 | AUC* | Mutual /100 | Clarification cost / episode |
|---|---|---|---|---|
| C1 matching-margin asker | +0.0003 ± 0.0016 | −0.024 ± 0.007 | −0.02 ± 0.08 | **225** (B: 274) |
| S1 simple fixed scorecard (offline prior only; no learning, no reply or yes-propensity terms) | +0.0010 ± 0.0033 | **+0.027 ± 0.008** | **+0.34 ± 0.14** | 273 |
| S2 posterior mean instead of Thompson draws | −0.0029 ± 0.0032 | +0.009 ± 0.006 | **+0.38 ± 0.14** | 274 |

\*AUC is measured on each policy's own introductions (§5.4), so differences partly reflect which pairs were introduced.

- **Margin asking** keeps expected wins while spending about 18% fewer points. Clarification cost is the third ranking tie-breaker [rule], so this is a free improvement.
- **The online learner and Thompson sampling do not earn their place on this evidence.**
  - A fixed scorecard is at least as good on expected wins and better on mutual acceptances (2.4 SE).
  - Posterior means also raise mutual acceptances (2.7 SE). This suggests that exploration costs early introductions it cannot repay within one episode.
  - The reply-behaviour term (H2) showed no measurable benefit in S1.
- **Round 2 default:** a fixed or posterior-mean scorecard with margin asking. Online learning is kept only if the shift-detection blend (F5) proves its value in the shift scenario without harming the other five.

### 9.6 Development vs confirmation data
- Seeds 6000–6039, 7000–7029, 7100–7109, 7200–7209 and 7300–7309 are **development sets**: their results influenced choices. Seeds in the 9000s were used for descriptive analyses.
- **Confirmation block, declared now and untouched:** seeds **50000–50019** for each of the 6 scenario families, 120 episodes, mirroring the official protocol. It will be run once, after the Round 2 policy is frozen, reporting realised MSMI with 95% intervals alongside coverage, mutual acceptances, clarification cost, waiting time to first introduction, runtime and invalid-episode count.
- Seed blocks are **disjoint**, not necessarily independent: within one seed, the development, delayed and drift scenarios share the same generated world, and outcome draws are keyed on (seed, pair, day) [code: `rand_for`]. So per-scenario results within a block are correlated.
- **Multiple comparisons.** We tested many variants, and all are reported. The largest observed development gains are subject to selection bias, so we treat them as provisional until the confirmation run.

### 9.7 Results by scenario [dev, seeds 7200–7209; expected wins per 100]
| Policy | cold start | delayed | development | drift | shift | sparse |
|---|---|---|---|---|---|---|
| Kit greedy | 0.357 | 0.444 | 0.443 | 0.417 | 0.396 | 0.104 |
| v2 + soft asks (≥ 2) | 0.379 | 0.460 | 0.482 | 0.455 | 0.418 | 0.103 |
| v2 + soft asks (≥ 1) | 0.373 | 0.457 | 0.483 | 0.456 | 0.431 | 0.103 |

- **Sparse shows no gain:** there is almost no choice to exploit.
- On the 7100 block, shift was the weakest scenario for v2 (0.411 vs 0.416 for greedy). There, the development prior points lifestyle the wrong way.
- Clarification cost: about 200 points per episode for greedy, 227 with soft asks (≥ 2), 272 (≥ 1), out of 720.

### 9.8 Retrospective: what we got wrong
- **An unreplicated gain.** The asker's mutual-acceptance gain (+0.29 ± 0.11) did not repeat on new seeds; an oracle asker gained ≤ ~1%. *Lesson:* replicate before believing.
- **Discounting "for drift"** was unnecessary under the inspected mechanism (§5.5).
- **Random feasible pairs** matched our full prototype on mutual acceptances. A simple baseline can be as good as a complex model on the outcome that matters, as the guest session stressed.
- **Better prediction ≠ more wins.** Broader asking raised AUC by +0.024 ± 0.006 but not expected wins. A clue only helps where it can change a decision.
- **An apparent timing effect.** Introductions made on days 35–49 once appeared to almost never succeed (0 of ~430 in two world sets), although their expected success was normal (≈ 1.0%). On 60 fresh worlds the rate was 1.05% (7 of 669): it was chance. Assignment day shows no reliable effect outside the drift scenario's built-in day-35 change.
- **Complexity that did not pay.** The online learner, Thompson sampling and the coverage boost each looked principled, but none beat simpler alternatives on block 7300 (§9.4–9.5).
- **Corrected early numbers.**
  - "20–30 pairs per day" was really 9–19.
  - The day-0 allowed-pair count was 2,996, not 3,215 (an age-check bug).
  - A "60× faster" claim was ~2× under a fair comparison.

---

## 10. Expected failure cases and defences
| # | Failure | Defence |
|---|---|---|
| F1 | Sparse supply (coverage ceiling ≈ 0.16 in sparse) | Prompt matching; scarcity weights; option value (H6) |
| F2 | Withheld answers (≈ 65 of 200 decline a hard field) | Never inferred or asked; kept in the denominator |
| F3 | Delayed feedback (replies ≤ 7 days, second answers ≤ ~26 days) | Pending ≠ no; prior carries early decisions |
| F4 | Competition for one person | Global matching; scarcity weights |
| F5 | Shifted weights | Online learning; Round 2: a gradual blend of two offline weight sets, weighted by the likelihood of observed replies |
| F6 | Noisy personal estimates (~2 introductions each) | Strong shrinkage (10 pseudo-observations) |
| F7 | Invalid output | Batch validation (§3); official checker; budget read from state |
| F8 | Timeout (10 s per call, including start-up) | A monotonic-time guard keeps a fixed output margin. If optimisation has not started by the cutoff, a pre-validated simple matching over the already-computed feasible graph is used. If safe completion cannot be guaranteed, an empty batch is returned. Both paths are tested [plan] |
| F9 | Protocol / format faults: NaN or Infinity, NumPy scalar types in JSON, memory near 1 MiB, missing optional keys, empty population, empty feasible graph, all members unavailable, duplicate IDs, members from several pools, declined soft fields | Explicit casting and guards; unit tests for each case [plan]. The current policy carries no memory |
| F10 | Larger hidden pools | Column filtering; matching within connected components |
| F11 | Over-reading noise | Paired seeds; low-variance diagnostic; untouched confirmation block |

---

## 11. Observations on the problem framing
1. **Early negative answers do not release people.** Both people stay unavailable for 8 days after an introduction, even after a definitive "no" on day 1 [code]. In a real service, immediate release after a definitive negative answer could increase opportunity without weakening any eligibility constraint.
2. **Thickness more than ranking.** With ~3 allowed partners per person and ~75% of them already used by greedy [oracle], improvements are more likely to come from information (clarification), timing (before departures) and availability than from better pair ranking.
3. **Outcome noise.** With about one qualifying outcome per episode, rankings on realised MSMI over 20 seeds per family will have wide intervals. We report low-variance diagnostics alongside MSMI for development, while recognising why an official metric should rest on realised, observable outcomes.
4. **Real-service extensions outside the simulator:**
   - retry members who ignored a message;
   - recompute age from date of birth;
   - let users rate the importance of each preference;
   - churn that depends on match experience.

---

## 12. Reproducibility and provenance
- **Code and results.** Every number comes from a script in `experiments/`, with raw per-episode JSONL in `experiments/results/`, at commit `41051bd8a976976b3ba341aa4bbee86aaa9bee15`.

| Section | Script |
|---|---|
| §9.1–9.2 | `run_baselines.py`, `run_ablation.py` |
| §9.3 | `test_scorer_v2.py`, `tune_v2.py` |
| §9.4–9.5 | `tune_v3.py` |
| §5.2 | `funnel_probs.py`, `woe_iv.py` |
| §5.6 | `scorer_data.py` |
| §1.4 | `theory_ceilings.py`, `why_unused.py`, `daily_cost.py` |
| Appendix A | `bench_100k.py` |

- **Commands:** run from the organiser kit folder, for example `python tune_v3.py 7300 10 development > out.jsonl`, then `python summarise_scorer_v2.py out*.jsonl`.
- **Environment:** Python 3.13.16, numpy 2.5.3, networkx 3.4.2 (BSD-3). These will be pinned in the Round 2 Docker image.
- **Inference seed:** deterministic per day and phase (`7919·day + phase`).
- **Permitted inputs only.** The policy reads only the observation, clarification results, feedback and its own memory. Hidden values appear only in offline measurement scripts (expected wins, oracle ceilings).
- **AI-assisted tools.** Anthropic Claude was used as a coding and research assistant to draft experimental scripts, debug implementations, run and summarise analyses, write up mathematical arguments and edit portions of this note. All hypotheses, source-code claims, derivations, experimental outputs and conclusions were reviewed by the author. AI-generated suggestions were treated as provisional and accepted only after inspection or reproducible testing. No external model is used by the policy during evaluation.

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
600 points at even odds; +20 points doubles the odds. One direction starts at 598 points.

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

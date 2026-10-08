# The One Introduction Problem — Round 1 Research Note

**Team:** solo · **Kit version:** participant specification 1.0.0 · **Date:** 9 October 2026
**Repository (all scripts, raw results, notes):** `sga-hq/the-sequential-matching-problem-hackathon_round1`, branch `claude/keen-mendel-pvprxr`

> **Draft status (remove before submitting):** items marked **[CONFIRM]** need the author's decision.

---

## 0. Summary in one page

**Our reading of the problem.** Every day the policy decides whom to ask (12 points) and which non-overlapping, mutually allowed pairs to introduce. The score (MSMI) counts introductions where both people go on a date and both want a second one. We first measured where the score comes from and where it is lost, before choosing methods.

**What we found (measured on the public simulator, not assumed):**
1. **Asking is the dominant lever.** Without asks, MSMI falls by 72%: most people arrive with unknown dealbreakers.
2. **Allowed partners are scarce.** Each person has only about 3 allowed partners over the whole episode. The kit's greedy baseline already introduces **75% of all allowed pairs** (98% in the sparse scenario), and introduces nearly everyone who has any partner at all.
3. **So the room to improve is small, and we can bound it.**
   - Using the simulator's own success formula, the hard upper bound is **+40%** over the baseline (introduce every allowed pair, which is not reachable).
   - A **perfect** soft-field scorer would add **+8%**.
   - The realistic target is **+5–15%**.
4. **A pair's success is mostly hidden luck.**
   - Even a scorer that knew every visible clue exactly would reach AUC **0.64**; knowing each person's hidden pickiness gives 0.71; the rest (up to 0.74) is a coin flip.
   - Our scorer reaches 0.54–0.55, mainly because **62% of the soft clues are blank** at decision time.

**Our design** (each piece is justified by a measurement in this note):
- reciprocal feasibility by vectorised column checks;
- a two-priority asker (dealbreakers first, then 1-point soft-field questions with the budget that is otherwise wasted);
- a whole-journey scorer, P(A yes) · P(B yes) · rA² · rB² (r = reply habit, which a win needs twice), learned online with Beta counts and Thompson sampling;
- a maximum-weight, maximum-cardinality matching (Edmonds' blossom algorithm) with urgency boosts for people with few options;
- an official eligibility re-check before every output.

**Current result:** our best policy beats the kit's greedy baseline by **+2.7% and +6.3% in expected wins** on two independent sets of 60 new episodes (≈3.5–5 standard errors each). That is real but small, exactly as the ceilings predicted. Asking soft fields more widely raises scorer AUC from 0.565 to 0.589, and blank clues fall from 57% to 41%.

**Where we question the framing (§11):**
- A person who says "no" on day 1 still stays occupied for 8 days.
- With about 3 partners per person, the bottleneck is market thickness, not ranking quality.

---

## 1. Problem interpretation

### 1.1 The daily decision
Each day *t* the policy receives an observation and makes two decisions.
1. **Ask:** spend up to 12 points. The dealbreaker bundle costs 3 points (all 11 hard fields at once); a named soft field costs 1. Answers arrive the same day.
2. **Introduce:** return a set of pairs. Each person may appear at most once. Every pair must pass every dealbreaker in **both** directions and must never have been introduced before. Returning nothing is valid.

One invalid pair in any of the 120 assessed episodes makes the submission ineligible. **Validity therefore comes before everything else.**

### 1.2 The journey of one introduction (exact rules, read from the simulator code)
```
Day t        Introduced. Both people become occupied.
Day t+1..t+7 Each person replies yes / no on a random day, or never replies (24% of replies never arrive).
   ├─ any "no" or no reply → over; the pair can never be repeated; both free again on day t+8
   └─ both "yes" → a date 1–14 days after the later reply (+5–12 days in the delayed scenario)
        ├─ the date does not happen (22%) → over
        └─ the date happens → each person answers "second date?" 1–5 days later, or never
             └─ both "yes" → both paused for good. This counts for MSMI only if both answers come within
                3 days AND the date is ≤ 30 days after the introduction.
```
Occupied time: 8 days normally; if both said yes, until 6 days after the date (day t+8 to t+27).

### 1.3 The pool (development scenario, measured over 10 worlds)
| Group | People per world | Can be introduced? |
|---|---|---|
| All dealbreakers known on arrival | 69.9 | yes |
| Dealbreakers unknown, askable (all miss 7–11 of 11; nobody misses only 1–2) | 65.4 | after one 3-point ask |
| Refused at least one dealbreaker | 64.6 | never (a refusal is permanent and must not be inferred) |

- About 70% of people arrive on day 0; the rest arrive by day 20.
- 12% leave at a random day between 22 and 59. In the simulator code this is decided when the person is created and is unrelated to anything observable.

### 1.4 Where the score is won and lost (the binding constraints)
| Constraint | Measurement | Consequence |
|---|---|---|
| Unknown dealbreakers | no-asks baseline MSMI −72% | Asking is essential |
| Scarce allowed partners | ~3 per person; baseline uses 75% of allowed pairs | Little choice exists; ranking can only matter when a choice exists |
| Choice only exists early | After day 20, ~105 people are free and ready but only ~1–2 allowed pairs exist among them | The scorer matters on day 0 and while newcomers arrive |
| Unused allowed pairs | 53% one person already succeeded (paused) · 27% one person left · 20% one person was occupied | Only the last two are recoverable (introduce early; choose carefully) |
| Luck | Best possible AUC 0.74 even with all hidden traits | Success per pair ≈ 1%; large episode-to-episode noise |
| Measurement noise | Comparing policies on MSMI needs ~79 episodes per policy to detect 1.0 → 1.5 wins per episode (power analysis) | We compare on **expected wins** (below) and confirm on MSMI |

**Expected wins (our main development metric).** For every pair a policy introduces, we compute its exact success chance from the simulator's own formula, integrating over the shared random term (5-point Gauss–Hermite). We then sum these chances. Hidden values are used **only for offline measurement**, never by the policy. This removes most of the luck from comparisons, the way the guest lecture compared forecasts against a perfect-information benchmark rather than raw error.

---

## 2. Hypotheses

- **H1 (asking):** spending the unused ask budget on 1-point soft-field questions reduces blank clues and raises both scorer quality and expected wins.
  - *Evidence so far:* blank clues fell from 71% to 59%; AUC rose from 0.540 to 0.553 (0.527 → 0.560 in cold start); expected wins changed by +0.3% (within noise).
- **H2 (whole journey):** scoring the full chain to a second date beats scoring only the first "yes", because reply habit enters the chain twice.
  - *Evidence:* reply habit persists (P(reply | replied last time) = 0.77 vs 0.68 after a silence). The second-date step shows no visible field effect (selection bias, §5.3).
- **H3 (allocation):** maximum-weight matching with urgency for scarce people beats picking the best pair first.
  - *Evidence:* the kit's own four-person example (0.95 → 1.30). Coverage rose +0.005 ± 0.001, consistently.
- **H4 (no ageing):** within one episode, old replies should not be discounted. Proof in §5.5.
- **H5 (ceiling):** no policy can exceed +40% in the public simulator, and a perfect soft-field scorer is worth about +8%. **Falsifiable:** any measured gain above these bounds would reveal a lever outside our model.

---

## 3. Reciprocal feasibility

**Definition.** For dealbreaker rule *k*, let c_k(i→j) ∈ {0,1} be 1 when person *j* satisfies person *i*'s rule *k*. A pair (i, j) is allowed on day *t* when

  e_ij(t) = ∏_k c_k(i→j) · c_k(j→i) · [i, j available and fully known] · [pair never introduced]

A single 0 in either direction removes the pair. Unknown values never count as a pass. Declined answers are never inferred.

**Implementation: column checks.**
- Each rule is evaluated as a 0/1 column over all people at once (numpy), and the columns are combined with logical AND.
- We benchmarked four methods on 100,000 synthetic people (35,051 with complete dealbreakers). All four found the identical 7,970,144 allowed pairs.

| Method | Per new arrival | All pairs |
|---|---|---|
| Pair-by-pair row check | 21.7 ms | 791 s |
| Group by gender × zone first | 8.7 ms | 289 s |
| Bitmap index | 1.4 ms | 35.6 s |
| **Column checks (chosen)** | **0.21 ms** | **6.1 s** |

- At 200 people every method takes milliseconds: our daily filter took ≤ 26 ms, and the slowest whole day took 45 ms against the 10-second limit. The column method costs nothing extra, so we use it from day one.
- Real apps grow gradually, so the per-arrival cost (0.21 ms) is the relevant number at scale.
- *Scope:* the 100k test covers the filter only. At that size, exact matching would run within connected components or use a greedy approximation.

**Real-app design (not possible in the hackathon).** Keep a saved table of allowed pairs with scores, ranked per person, and check only newcomers.
- Arrivals go through one queue: insert first, then check against old + new people.
- Each pair is stored once under (smaller ID, larger ID), so simultaneous arrivals are never missed.
- A nightly full re-check is a backup.
- The hackathon carries at most 1 MiB of memory between calls (100k people → ~8 M pairs ≈ 64 MB), so we recompute daily there.

**Safety.** Every chosen pair is re-checked with the kit's official `eligibility()` before it is returned.

---

## 4. Clarification (asking) policy

**What the data says.**
- The kit's baseline spends only **199 of 720** ask points per episode. After about day 17 nobody has unknown dealbreakers left, and the budget sits idle.
- An oracle test (180 episodes per asker, all 6 scenarios) showed that the *order* of dealbreaker asks barely matters. Versus the kit's order, both-said-yes changed by: random +1.2% ± 2.2%, ours −0.2% ± 2.4%, perfect-knowledge oracle −0.1% ± 2.1%, unlimited asking +0.8% ± 2.3%.
- By contrast, 62% of soft clues are blank at decision time (82% in cold start), and blank clues are the main reason the scorer is weak (§5).

**Policy (two priorities):**
1. **Dealbreaker bundles (3 points).** Ask pending people who could pair with already-ready people first. Cheap exact check: age, gender and zone are always visible, so we count the ready people whose stated preferences accept this person. Pending people whose only possible partners are other pending people come last.
2. **Soft fields (1 point each) with the leftover budget:**
   - ask the clue most likely to change a decision: goal first, then pace, lifestyle, conversations;
   - ask only people who currently have a choice of partners;
   - never ask the three fields with no measurable effect (§5.2).

   Every soft answer also speeds up learning.
3. **Never ask** blocked, occupied or retired people (the kit forbids asking unavailable people).

**No combinatorial explosion.** Each question is judged on its own ("could this one answer change today's choice?"), so the cost is linear in the number of people. Choosing one question at a time is near-optimal when answers have diminishing returns (adaptive submodularity; Golovin & Krause, JAIR 2011). Related theory: a few well-chosen queries per vertex recover most of the value of full information in stochastic matching (Blum, Dickerson, Haghtalab, Procaccia, Sandholm & Sharma).

**Rejected:** guessing blank answers from "similar users" ("smart defaults").
- The integration guide says "never fabricate a default preference", and declined answers "must not be inferred or bypassed".
- It would also not work: in the generator every soft field is drawn independently, so other answers carry no information about a blank one.

---

## 5. Probability estimates (the scorer)

### 5.1 Target
The competition counts second-date intentions, so the scorer targets the **whole journey**. By the chain rule of conditional probability:

  P(win) = P(both reply) · P(both yes | replied) · P(date) · P(both answer again) · P(both yes again) · P(both on time)

### 5.2 Measured conditional probabilities (kit baseline, development, 30 worlds, 5,468 reply chances; decision-time fields only)
| Quantity | Value |
|---|---|
| P(reply) | 0.76 |
| P(reply \| replied last time) / P(reply \| silent last time) | 0.77 / 0.68 |
| P(yes \| replied) | 0.48 |
| P(yes \| said yes last time) / P(yes \| said no last time) | 0.51 / 0.44 |
| P(yes \| goal same) / P(yes \| goal different) | 0.61 / 0.37 |
| P(yes \| goal and pace both same) | 0.70 (adding the two effects in log-odds predicts 0.70) |
| P(date \| both yes) | 0.76 |
| P(second yes \| date), goal same / different / unknown | 0.63 / 0.64 / 0.65 |
| P(second answer on time \| answered) | 0.60 |

**Information Value per field** (15 worlds per scenario). Industry scale (Siddiqi 2006): < 0.02 useless, 0.02–0.1 weak.

| Field | development | shift | cold start |
|---|---|---|---|
| goal | 0.074 | 0.006 | 0.050 |
| pace | 0.002 | 0.066 | 0.004 |
| lifestyle | 0.005 | 0.006 (reversed: same lifestyle *lowers* the chance) | 0.012 |
| conversations | 0.005 | 0.017 | 0.006 |
| emotional availability, space for relationship, relocate | ≤ 0.002 | ≤ 0.009 | ≤ 0.008 |

### 5.3 What the measurements imply
1. **The logistic form is correct.** Clues add in log-odds with no interaction (predicted 0.70 = observed 0.70). Feature crosses, per-user taste vectors and tree models are not justified: there is no interaction, and there are ~25 replies in the first 10 days and a median of 2 introductions per person.
2. **Selection bias at the second step.** The simulator code contains a goal effect at the second date, yet it is invisible in the data. Pairs with different goals reach a date only when their shared luck is good, and that luck also helps at the second step. Advertising systems face the same problem with click → conversion and model the whole chain over all impressions (ESMM; Ma et al., SIGIR 2018). For ranking, the visible clues enter only the "both yes" factor; the other factors are constant across pairs **except reply habit, which appears twice.** Hence

   **score(A, B) = P(A yes | clues, A) · P(B yes | clues, B) · r_A² · r_B²**

3. **Personal habits persist.** Reply habit and pickiness carry over between a person's introductions. But a person gets only ~2 introductions, so these estimates must be strongly anchored to the population average.
4. **The strongest clue depends on the scenario** (goal normally, pace under shift). A fixed scorecard cannot handle this, so the weights must be learned online.

### 5.4 The estimator
- **Field effects:** for each field *f* and state *s* ∈ {same, different}, a Beta belief about the yes-rate. The prior comes from an offline fit on public training worlds, worth *k_field* imaginary replies (the "normaliser"). Unknown clues add 0, so a blank never counts as a mismatch.
- **Reply habit:** r_i ~ Beta(0.76 · k_reply + answered_i, 0.24 · k_reply + ignored_i), with k_reply = 10.
- **Pickiness:** person *i*'s own yes-rate, shrunk toward the base rate with k_pick = 10 imaginary replies.
- **Thompson sampling:** each day every uncertain number is drawn from its Beta belief rather than set to its mean (Chapelle & Li, NeurIPS 2011; Russo et al., 2018). Uncertain pairs occasionally get a high draw and are tried. As evidence accumulates the draws settle. Exploration is at the level of fields and people, and **never relaxes a dealbreaker**.
- **Missing replies are not "no".** A reply that has not arrived yet is pending (right-censoring); a reply that never arrives counts only toward reply habit.

**Scorecard view (for interpretability).** Target 600 points at even odds, 20 points to double the odds (factor 20/ln 2 = 28.9). One direction starts at 598 points.

| Clue | Same | Different | Unknown |
|---|---|---|---|
| goal | +20 | −11 | 0 |
| pace | +10 | −10 | 0 |
| lifestyle | +7 | −9 | 0 |
| conversations | +2 | −5 | 0 |

Example: goal same, lifestyle different → 609 points → P(yes) ≈ 0.57.

### 5.5 Ageing: why the discount factor is exactly 1 here
- **Claim:** within an episode, old replies should not be down-weighted (γ = 1).
- **(a) The effects are constant within an episode.** From the simulator source: field effects are fixed for the whole episode in every scenario (shift changes them from day 0; drift lowers everyone's log-odds by the same 0.5 from day 35, which leaves each person's ordering of options unchanged). Personal traits are fixed too.
- **(b) Equal weights minimise variance.** For a constant rate *p* estimated by a weighted average with Σw_i = 1, the variance is p(1−p)·Σw_i², and by Cauchy–Schwarz Σw_i² ≥ 1/n, with equality only for equal weights. Any γ < 1 adds noise and removes no bias.
  - Over 60 days, γ = 0.98 keeps 89% of the effective data, 0.95 keeps 59%, and 0.90 keeps 32%.
- **(c) For a real app where tastes drift,** exponential smoothing is the optimal filter for a slowly wandering level (Muth, JASA 1960): α = (−q + √(q² + 4q))/2 and γ = 1 − α, where *q* is the signal-to-noise ratio of the drift. *q* = 0 gives γ = 1, consistent with (a).
- **Retrospective:** our prototype used γ = 0.98 "for drift". The proof shows that cost about 11% of the data and bought nothing.

### 5.6 How good can any scorer be? (offline ceiling using hidden values)
| Scorer knows… | AUC |
|---|---|
| Ours today | 0.54–0.55 |
| All 4 soft fields exactly, true weights | 0.61–0.65 |
| + each person's pickiness | 0.70–0.72 |
| + the pair's shared luck | 0.74–0.75 |

Most of our gap to 0.64 is blank clues, not the formula. That is why the asker and the scorer are designed together. (A standard credit-scoring rule of thumb calls AUC > 0.75 "strong". In this simulator that is unreachable even with perfect knowledge.)

Calibration: mean predicted P(yes) 0.44 vs actual 0.46, slightly low. We will check it with reliability curves and the Brier score. (The KS statistic, often suggested, measures separation, not calibration.)

---

## 6. Allocation method

**Objective.** Each day:

  maximise Σ_{(i,j) ∈ E_t} v_ij · x_ij  subject to Σ_j x_ij ≤ 1 for every i, x_ij ∈ {0, 1}

- v_ij = score(i, j) · u_i · u_j
- u_i = 1.5 if person *i* has never been introduced (coverage is the first tie-breaker), times (1 + 0.5 / d_i), where d_i = person *i*'s number of allowed partners today (scarce people first).

Among all matchings with the **most pairs**, we take the one with the highest total: networkx `max_weight_matching(maxcardinality=True)`, Edmonds' blossom algorithm, O(n³), with integer weights.

**Why not best-pair-first.** Kit example: A–B 0.90, C–D 0.05, A–D 0.65, B–C 0.65. Best-pair-first gives 0.95; the best set gives 1.30. Greedy can lose up to half the optimum.

**Why the most pairs.** Scores separate pairs only weakly, so each extra introduction adds more expected value than reordering.

**Why match every day rather than wait.** Departures are invisible in advance. In dynamic matching markets, waiting for a thicker market pays only when departures are known; otherwise matching promptly is near-optimal (Akbarpour, Li & Oveis Gharan, JPE 2020).

**Fairness ("averaging") — investigated and rejected.** We asked whether an upper score cutoff or a fairness objective should stop the best pairs being "taken".
- Literature: the price of fairness (Bertsimas, Farias & Trichakis 2011; in kidney exchange, Dickerson, Procaccia & Sandholm, AAMAS 2014). Group fairness in online matching (Ma, Xu & Xu, AAMAS 2022). Assortment optimisation in dating (Rios, Saban & Zheng, MSOM 2023).
- Code read: FairRec and FA*IR.
- Conclusion: real systems use **floors/quotas for the disadvantaged, never caps on the best**. Dating apps spread attention because popular users get flooded, and the simulator has no flooding. Here, the way one person's choice hurts another is **over time** (an 8-day occupancy, then departures), which urgency addresses. Optional tests: √score, log score + C (valid only with maximum cardinality), coverage-first weights.

---

## 7. Handling missing and delayed data

| Situation | Rule |
|---|---|
| Unknown dealbreaker | Never pass; ask first |
| Declined dealbreaker | Permanently blocked; never inferred, never asked |
| Unknown soft field | Contributes 0 (neutral); ask if it could change a decision |
| Reply not yet arrived | Pending, not "no" (right-censoring) |
| Reply never arrives | Updates reply habit only; never counted as a "no" |
| Date / second answers (up to 26 days later) | Learned when they arrive; the current score does not depend on them |
| "Left" vs "occupied" | Both show as unavailable; we infer "left" when no introduction is in progress |
| Delayed scenario | Longer occupancy; dates more than 30 days after the introduction cannot count, and this is not controllable |

**Data flow per world** (development, measured): 172 reply chances (65 yes, 65 no, 42 none), 14 mutual acceptances, 11 dates, 2.3 pauses. Only ~25 replies arrive in the first 10 days, so **the prior carries the early decisions**.

---

## 8. Existing solutions we used, and why

| Piece | Source | Why this and not something else | Evidence |
|---|---|---|---|
| Two-way dealbreaker filter | Reciprocal recommenders (RECON, Pizzato et al. 2010); kit rules | A dating match must suit both people | Validity |
| Column-wise checks | Column-store / bitmap index practice | ~100× faster than row checks at 100k, identical output | §3 |
| Maximum-weight matching | Edmonds 1965; networkx | Best total, not best single pair | Kit example; coverage +0.005 ± 0.001 |
| Logistic / WoE scorer | Credit scorecards (Siddiqi 2006) | Clues add with no interaction; interpretable | §5.3 |
| Beta + Thompson sampling | Chapelle & Li 2011; lecture of 6 Oct | Learns online, explores without a tuning dial | Lecture regret example reproduced (13 vs 99 for greedy) |
| Whole-chain target | ESMM (Ma et al. 2018) | Corrects selection bias at the second step | §5.3 |
| No ageing | Muth 1960 | Effects are constant within an episode | §5.5 |
| Match promptly, urgency for scarce people | Akbarpour et al. 2020 | Departures are invisible | §6 |
| Expected-wins metric, perfect-information ceiling | Guest lecture (7 Oct) | Judge on the business outcome, not model error | §1.4 |
| Grouped hold-out | Guest lecture; GroupKFold practice | Tune on training worlds, report on unseen worlds | §9 |

**Not used, with reasons:**
- tree models / XGBoost (too little data, no interactions);
- factorisation machines / per-user vectors (median 2 introductions per person);
- smart defaults (forbidden and uninformative);
- peer personas (hidden traits are independent of the profile in the generator);
- upper score cutoffs (§6);
- discounting (§5.5).

---

## 9. Baselines, ablations and results

### 9.1 The three required baselines (same 40 worlds × 6 scenarios, 240 episodes each)
| Policy | MSMI /100 | Both said yes /100 | Coverage |
|---|---|---|---|
| Kit greedy | 0.410 | 5.45 | 0.335 |
| Kit random-feasible | 0.352 (−14%) | 5.64 | 0.337 |
| Kit no-asks | 0.117 (−72%) | 1.53 | 0.115 |

### 9.2 Ablation: adding pieces one at a time (240 episodes per policy)
| Policy | MSMI /100 | Both said yes /100 | Coverage |
|---|---|---|---|
| A0 kit greedy | 0.410 | 5.45 | 0.335 |
| A1 + maximum-weight matching | 0.408 | 5.60 | 0.336 |
| A2 + value-of-information asker | 0.398 | 5.74 | 0.338 |
| A3 + urgency boosts | 0.396 | 5.69 | 0.339 |
| A4 + Thompson learning | 0.400 | 5.64 | 0.340 (+0.005 ± 0.001) |

MSMI differences are all within ±0.04 noise. The asker's apparent +5% in both-said-yes **did not replicate** on new worlds (§9.4).

### 9.3 Scorer v2 on 10 new worlds × 6 scenarios (60 paired episodes per policy)
| Policy | Expected wins /100 | vs kit (paired) | AUC | Blank clues |
|---|---|---|---|---|
| Kit greedy | 0.375 | – | 0.541 | 70% |
| Old prototype | 0.384 | +0.0086 ± 0.0024 (+2.3%) | 0.547 | 71% |
| Scorer v2 | 0.384 | +0.0091 ± 0.0024 (+2.4%) | 0.540 | 71% |
| Scorer v2 + soft asks | 0.385 | **+0.0103 ± 0.0020 (+2.7%)** | **0.553** | **59%** |

- MSMI over these 60 episodes ranged 0.26–0.44 for nearly identical expected wins. **MSMI at this sample size is noise.**
- Both-said-yes did not increase (−0.20 ± 0.17 vs kit). The gain comes from later stages of the journey.
- Weak spot: the shift scenario (0.411 vs the kit's 0.416). The development prior points lifestyle the wrong way.

**Tuning round 1** (10 further new worlds × 6 scenarios, seeds 7200–7209, 60 paired episodes per version; `experiments/tune_v2.py`, `results/tune_v2_summary.txt`)

| Change vs scorer v2 + soft asks | Expected wins (paired) | AUC (paired) | Verdict |
|---|---|---|---|
| (reference) v2 + soft asks vs kit | **+0.0228 ± 0.0065 (+6.3%)** | +0.028 ± 0.008 | – |
| T1: ask soft fields of anyone with 1+ option | +0.0009 ± 0.0018 | **+0.024 ± 0.006** | **adopt.** Blank clues 57% → 41%; best calibration (0.465 vs 0.466) |
| T2: normaliser 40 → 12 imaginary replies | **−0.0118 ± 0.0027** | −0.009 ± 0.006 | **reject.** Learning faster from ~25 early replies just learns noise |
| T3: stronger pickiness (k = 3) | +0.0004 ± 0.0021 | −0.008 ± 0.006 | reject (no gain) |
| T4: pickiness off | +0.0005 ± 0.0029 | −0.016 ± 0.006 | keep pickiness (helps prediction, not yet wins) |
| T5: T1 + T2 + T3 | −0.0021 ± 0.0032 | +0.009 ± 0.007 | reject (T2 drags it down) |

- Across the two independent sets of new worlds, scorer v2 + soft asks beat the kit by **+2.7%** (seeds 7100–7109) and **+6.3%** (7200–7209) in expected wins. **We report roughly +4.5% with that spread**, rather than the more flattering figure.
- More asking makes the scorer clearly better (AUC 0.565 → 0.589) without yet adding wins. This is consistent with §1.4: better ranking only pays where a choice exists.
- Lowering the normaliser was a plausible idea that the data rejected clearly (4.4 standard errors worse).

### 9.4 Retrospective: what we got wrong, and how we found out
- **"+5% from the asker"** (240 episodes, 2.7 standard errors) did not repeat on new worlds. An oracle asker gains ≤ 1%. *Lesson:* one significant-looking result is not a finding. Replicate on held-out worlds.
- **Ageing "for drift"** turned out to be unnecessary (proof in §5.5).
- **"Clever beats simple" is false here.** Random feasible pairs matched our full prototype on both-said-yes. This is exactly the guest lecture's lesson that a naive baseline can beat a sophisticated model on the business metric.
- **Early numbers we corrected:**
  - "20–30 pairs per day" was really 9–19;
  - day-0 allowed pairs after the first filters were 2,996, not 3,215 (an age-check bug);
  - "60× faster" was ~2× at 1k–10k people under a fair comparison.

### 9.5 Planned experiments for Round 2
| # | Experiment | Hypothesis | Measure |
|---|---|---|---|
| E1 | Soft-ask threshold and field order | More asks → fewer blanks → higher AUC and wins | expected wins, AUC, blank share |
| E2 | Normaliser strength (k_field 5–200) | Lower k learns shift faster; too low is noisy | per-scenario expected wins |
| E3 | Gradual shift detection: blend two offline weight sets by the likelihood of observed replies | Fixes the shift weak spot without hurting the other 5 scenarios | shift vs others |
| E4 | Reply habit and pickiness on/off | Each adds value through the twice-needed reply | paired expected wins |
| E5 | Urgency strengths; front-loading before day 35 | Scarce people and drift timing | coverage, expected wins |
| E6 | Offline evolutionary tuning (differential evolution) of all knobs | Joint optimum beats one-at-a-time tuning | train worlds → **held-out** worlds |
| E7 | Stress worlds (partial profiles, reply collapse, arrival surges, early churn, 80/20 gender ratio, 2,000 people, odd data) | Zero invalid episodes; never worse than greedy | validity, runtime |
| E8 | Final confirmation: hundreds of episodes on MSMI | Gains survive on the official metric | MSMI with confidence intervals |

E6 cost: one fitness evaluation ≈ 20 worlds × 5 s = 100 s; 20 candidates × 30 rounds ≈ 17 CPU-hours (≈ 4 h on 4 cores), offline only.

---

## 10. Expected failure cases (and our defences)
| # | Failure | Why it happens | Defence |
|---|---|---|---|
| F1 | Sparse supply (sparse scenario: coverage ceiling 0.16) | Few people in each zone | Match promptly; scarce-first urgency; never wait |
| F2 | Withheld answers (≈ 65 of 200 refuse a dealbreaker) | A refusal is permanent | Never infer; never ask; count them honestly in the denominator |
| F3 | Delayed feedback | Replies up to 7 days, second answers up to 26 days | Pending ≠ no; the prior carries early decisions |
| F4 | Competition for the same person | X and Y both have only Z | Matching (one pair per person); the loser gets a boost next time Z is free |
| F5 | Shift scenario | Development prior wrong for lifestyle | Online learning; planned gradual detection (E3) |
| F6 | Reply-habit noise | ~2 introductions per person | Strong shrinkage (k = 10) |
| F7 | Disqualification | Invalid pair, overlap, repeat, over-budget ask, crash, timeout | Official checker on every pair; budget read from the state; empty output on any doubt; time guard falling back to the kit greedy method |
| F8 | Larger hidden pools | O(n²) Python loops | Column checks; connected components |
| F9 | Over-reading noise | MSMI is extremely noisy | Expected wins; paired seeds; held-out worlds |

A full catalogue of 21 edge cases is in `EDGE_CASES.md`, and 10 dating-app stress tests are in `STRESS_TESTS.md`.

---

## 11. Questioning the framing (as invited by the organisers)
1. **A "no" still costs 8 days.** In the simulator both people are occupied for 8 days from the introduction, whatever the answer. Someone who declines on day 1 sits idle for a week. A real service should release people as soon as a "no" arrives. That would add introductions at no cost, and it matters more here than any ranking improvement we measured.
2. **The bottleneck is market thickness, not ranking.** With ~3 allowed partners per person and 75% of allowed pairs already introduced by greedy, ranking quality has a hard ceiling (+8% for a perfect soft scorer). The levers that matter are information (asking), timing (before departures) and availability (shorter idle time).
3. **MSMI alone is too noisy to rank policies reliably.** With ~1 success per episode, 20 seeds per family give wide intervals. We recommend reporting expected wins (or mutual acceptances) alongside MSMI.
4. **Real-app notes.**
   - Retry people who ignored a message because they were busy (the simulator forbids repeats).
   - Store date of birth and recompute age daily (age is fixed in a 60-day episode).
   - Let users rate how important each preference is.
   - Leaving is random in the simulator, but in real apps it depends on getting matches.

---

## 12. Reproducibility and provenance
- Every number in this note comes from scripts in `experiments/`, with raw JSONL results in `experiments/results/`. Seeds are declared per experiment: 6000–6039 for the ablation and baselines; 7000–7029 for the asker bounds; 7100–7109 for the scorer test; 7200–7209 for tuning; 9000+ for data analyses.
- **Training vs evaluation:** priors are fitted on separate public training seeds; reported comparisons use different seeds.
- The policy reads only the observation, clarification results, feedback and its own memory. Hidden values are used only in offline measurement scripts (expected wins, ceilings).
- **Packages:** Python 3, numpy, networkx (BSD-3, to be pinned in the Docker image).
- **AI assistance [CONFIRM wording]:** an AI coding assistant (Claude) was used for coding and for testing ideas through experiments. *(If it also helped write up the maths or this note, say so here: the kit requires documenting external models and coding tools.)*
- Lecture material and public repositories consulted are cited where used. No code was copied from GPL-licensed sources.

## References
- Akbarpour, M., Li, S., & Oveis Gharan, S. (2020). Thickness and information in dynamic matching markets. *Journal of Political Economy.*
- Bertsimas, D., Farias, V., & Trichakis, N. (2011). The price of fairness. *Operations Research.*
- Blum, A., Dickerson, J., Haghtalab, N., Procaccia, A., Sandholm, T., & Sharma, A. Ignorance is almost bliss: near-optimal stochastic matching with few queries. *EC 2015 / Operations Research.*
- Chapelle, O., & Li, L. (2011). An empirical evaluation of Thompson sampling. *NeurIPS.*
- Dickerson, J., Procaccia, A., & Sandholm, T. (2014). Price of fairness in kidney exchange. *AAMAS.*
- Edmonds, J. (1965). Paths, trees, and flowers. *Canadian Journal of Mathematics.*
- Golovin, D., & Krause, A. (2011). Adaptive submodularity. *JAIR.*
- Ma, W., Xu, P., & Xu, Y. (2022). Group-level fairness maximization in online bipartite matching. *AAMAS.*
- Ma, X., et al. (2018). Entire space multi-task model (ESMM). *SIGIR.*
- Muth, J. F. (1960). Optimal properties of exponentially weighted forecasts. *JASA.*
- Pizzato, L., et al. (2010). RECON: a reciprocal recommender for online dating. *RecSys.*
- Rios, I., Saban, D., & Zheng, F. (2023). Improving match rates in dating markets through assortment optimization. *MSOM.*
- Russo, D., Van Roy, B., Kazerouni, A., Osband, I., & Wen, Z. (2018). A tutorial on Thompson sampling. *Foundations and Trends in ML.*
- Siddiqi, N. (2006). *Credit Risk Scorecards.* Wiley.
- Patro, G., et al. (2020). FairRec. *WWW.* · Zehlike, M., et al. (2017). FA*IR. *CIKM.*

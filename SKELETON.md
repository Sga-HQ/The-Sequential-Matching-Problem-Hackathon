# Solution Skeleton

The best pieces from everything we studied, organised into one daily process. Each piece lists **where it came from** and **the evidence** for it. Prototype code: `experiments/prototype_policy.py`. Measured results: section 4.

## 1. Where the ideas came from (source key)

| Key | Source |
|---|---|
| **U** | Your own ideas from our discussions |
| **K** | Organiser kit: problem statement, simulator code, dataset |
| **L** | Hackathon lecture "Exploration, Exploitation and Online Learning" (6 Oct) |
| **F** | Your friend's "Fresher Friend Matching" architecture and mathematical appendix |
| **R** | Public code read at source level: SMPyBandits, contextualbandits, chaos-rrs, RECON, kidney_solver, networkx, matching (RESEARCH.md §1) |
| **P** | Papers: Akbarpour et al. 2020; Chapelle & Li 2011; Chen et al. 2009; Blum et al.; Huang et al. 2018; Mehta & Panigrahi 2012 (RESEARCH.md §2) |
| **E** | Our own experiments (`experiments/`) |

## 2. The daily process

```
 state + memory
      │
 0. LOAD & SORT ── stores: Active · Pending · Blocked · Matched (busy) · Retired · History
      │
 1. FIND ALLOWED PAIRS ── columnar 1/0 masks, both directions (reciprocal)
      │
 2. ASK (12 pts) ── rank Pending people by predicted value of unlocking them → top 4 get the 3-pt bundle
      │
 3. RE-SORT ── answered people → Active; their pairs are added
      │
 4. SCORE EACH PAIR ── P(A yes) × P(B yes); soft-field weights from offline fit, Thompson draw,
      │                updated gently from discounted replies
 5. URGENCY ── × boost for never-introduced people and people with few options
      │
 6. MATCH ── maximum-weight, maximum-cardinality matching (blossom), integer weights
      │
 7. SAFETY ── official eligibility() on every chosen pair
      │
 8. RETURN pairs (+ memory)
```

## 3. Each piece, with its origin and evidence

| Step | Piece | Origin | Evidence |
|---|---|---|---|
| 0 | Person stores (Active, Pending, Blocked, Matched, Retired, History) | **U** (Pending/Active/Matched/History), Blocked and Retired added in discussion | Refusals are visible from day 0 and permanent (**K** simulator code) |
| 0 | Profile / preferences / mutual / soft / status tables | **U** | Problem statement §15 asks to keep normalisation, modelling, allocation separate (**K**) |
| 1 | Check every rule both ways | **K** rules; **R** chaos-rrs `ReciprocalCG`, RECON | Required for validity |
| 1 | 1/0 rule checks | **U** (per-person 1/0 row idea) | All methods give identical pairs (**E** `bench_100k.py`) |
| 1 | Columnar numpy masks instead of row-by-row | **R** bitmap/column-store practice (Elasticsearch roaring bitmaps) | 100k people: 0.21 ms per arrival vs 21.7 ms; 6 s vs 791 s all-pairs (**E**) |
| 1 | Search once per person; shared edge list | **U** | – |
| 2 | Ask only where the answer can change a decision | **L** slide 21 (value of information); **P** Blum et al. (few queries suffice) | – |
| 2 | Predict what an ask unlocks by copying unknown answers from similar complete people | **U** idea ("match complete to incomplete") | 1.32 partners per ask vs 0.62 random (**E** `asker_prediction.py`) |
| 2 | Extra value for partners with few options | **F** §7 floor ≥ 1 | – |
| 2 | Never ask Blocked people | **U** + **K** | Asking cannot reveal a refused answer (**K** code) |
| 4 | Only 4 soft fields carry signal; mutual fields stay filters | **E** `soft_weights.py` | Adding mutual fields worsened held-out log-loss (0.6898 → 0.6912) |
| 4 | Weights fitted offline as a prior | **E** + **F** §14 (events-per-variable limit) | Online data per episode supports only a few parameters |
| 4 | Thompson draw instead of plain average | **L** slides 19–20; **P** Chapelle & Li 2011 | Lecture: regret 14 vs 92 for greedy; reproduced 13 vs 99 (**E**) |
| 4 | Discounted counts (γ = 0.98/day) | **R** SMPyBandits `DiscountedBeta`; **L** slide 22 | Shift scenario changes weights (**E**: pace +0.68, lifestyle negative) |
| 4 | Pair value = P(A yes) × P(B yes) | **R** kidney_solver failure-aware scoring | All combination rules tie today (**E** `combine_directions.py`); product is the true joint chance |
| 5 | Boost never-introduced people | **F** §7 floor ≥ 1 | Coverage is ranking tie-breaker #1 (**K**) |
| 5 | Boost people with few options; match daily rather than wait | **P** Akbarpour et al. 2020; **U** waiting-time idea | Waiting only pays if you know who is about to leave |
| 6 | Best total set, not best pair first | **K** A–B–C–D example | – |
| 6 | Maximum cardinality (as many pairs as possible) | **F** §2 funnel elasticity | Scorer AUC only ~0.55 → more introductions is the cheaper lever (**E**) |
| 6 | Blossom algorithm, integer weights | **R** networkx `max_weight_matching` docs | Float weights can give slightly suboptimal matchings |
| 7 | Official checker on chosen pairs | **K** | One invalid pair disqualifies |
| Test | Develop on mutual acceptances, confirm on MSMI with many seeds | **F** §11 power analysis | MSMI 1.0 → 1.5 per episode needs ~79 episodes per policy (**E** calc) |

## 4. Measured results (7 Oct)

`experiments/run_ablation.py`: same protocol as the organiser evaluator (60 days + 40 follow-up), 40 seeds × 6 scenarios = **240 episodes per policy**, pieces added one at a time. Raw data: `experiments/results/ablation_6000-6039.jsonl`. Difference vs A0 is paired by seed, ± one standard error.

| Policy | MSMI /100 (primary) | Mutual accept /100 | Coverage |
|---|---|---|---|
| A0 kit greedy baseline | 0.410 | 5.45 | 0.335 |
| A1 + max-weight matching | 0.408 (−0.002 ± 0.032) | 5.60 (+0.16 ± 0.10) | 0.336 |
| A2 + value-of-information asker | 0.398 (−0.013 ± 0.038) | **5.74 (+0.29 ± 0.11), +5%** | 0.338 |
| A3 + coverage/urgency boost | 0.396 (−0.015 ± 0.037) | 5.69 (+0.25 ± 0.10) | 0.339 |
| A4 + Thompson online learning | 0.400 (−0.010 ± 0.039) | 5.64 (+0.19 ± 0.11) | **0.340 (+0.005 ± 0.001)** |

Reading:
- **MSMI: no measurable change.** All differences are inside ±0.04 noise. Detecting a 10% change would need thousands of episodes (power analysis, friend §11).
- **Mutual acceptances: +5% from the asker** (≈2.7 standard errors) — the clearest real gain.
- **Coverage: +0.5 points, very consistent, but already near the ceiling.** Ceiling (people who have any allowed partner at all) = 0.41 development, 0.16 sparse; we reach 0.39 / 0.17.
- Thompson learning showed no overall gain; shift-scenario MSMI 0.40 → 0.57 is suggestive but within noise.

### Asker ceiling test (`asker_bounds.py`, 180 episodes per asker, 6 scenarios, 200-person worlds)
Same matcher for all; only the choice of whom to ask changes. Versus kit order:

| Asker | Both-said-yes | Coverage | MSMI |
|---|---|---|---|
| Random | +1.2% (± 2.2%) | −0.1% | +9% (noise ±10%) |
| Ours (value of information) | −0.2% (± 2.4%) | +0.1% | +5% (noise ±10%) |
| Oracle (knows hidden answers) | −0.1% (± 2.1%) | +0.1% | −4% (noise ±9%) |
| Unlimited (everyone answers at once) | +0.8% (± 2.3%) | 0.0% | +8.5% (noise ±7%) |

- **Even a perfect or unlimited asker adds about 1% at most.** The order of asking barely matters: the kit asks 4 per day and everyone askable is answered by about day 17, while most matching happens later.
- The +5% both-said-yes for the asker in §4 did **not** repeat on new seeds → most likely luck. Treat it as no effect.
- Decision: keep the asker simple; spend effort elsewhere.

### Theoretical ceilings (`theory_ceilings.py`, `why_unused.py`; simulator success formula, development, 10 worlds)
Exact win chance per allowed pair, from the simulator's formula. Same number of introductions per person as the baseline:

| Scenario | Expected wins / episode | vs baseline |
|---|---|---|
| Kit greedy baseline | 0.906 | – |
| Perfect soft-field scorer (all 4 fields known and weighted exactly) | 0.976 | +8% |
| + perfect knowledge of hidden pickiness and reply rate | 0.992 | +9% |
| Use every allowed pair (not reachable) | 1.268 | +40% |

The baseline already uses 92 of 124 allowed pairs (75%; 98% in sparse). Why the rest go unused:
- 53%: one person already found a match and is paused (simulator rule; not recoverable).
- 27%: one person left the app (exit day 22–60; introducing people earlier recovers some).
- 20%: one person was busy with many introductions (capacity; choose their best partners).

**Conclusion: realistic headroom over the baseline is roughly +5–15% in wins, not more.** It comes from:
1. Knowing soft fields (the +8% bound assumes they are known; today ~60% are unknown and 72% of the ask budget is unused) → spend spare points on 1-point soft asks.
2. Choosing the best partners for people with many options (capacity-limited).
3. Introducing people as early as possible (beats departures).
Not worth effort: asker order (≤ 1%), heavy exploration.

## 5. Where the remaining room is (next experiments)

| Lever | Why | Evidence |
|---|---|---|
| Spend the unused ask budget | Only 199 of 720 points used per episode; after ~day 17 Pending is empty | **E** |
| Ask `relationship_goal` (1 pt) for Active people with unknown goal | Goal drives both the first yes and the second-date yes | **K** simulator, **E** weights |
| Score the whole funnel, not just "both yes" | Second-date chance has its own goal-match term | **K** simulator code |
| Reply reliability | ~22% of replies never arrive and kill the pair | **K** data; reliability, not rejection reasons |
| Coverage is near its ceiling | Gains must come from pair quality and repeat introductions | **E** |

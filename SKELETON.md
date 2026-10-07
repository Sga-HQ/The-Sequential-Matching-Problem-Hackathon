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

## 4. Measured results

See section "Results" below (filled in from `experiments/run_ablation.py`).

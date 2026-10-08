# Research Log: Papers, Open-Source Code and Our Experiments

Goal: not a ready-made solution, but **small pieces** of other people's approaches that we can adopt and improve.
Code was read at the source level (commit noted), not only the README.

---

## 1. Open-source code read

| Repo (commit) | Licence | What we read | Piece worth adopting |
|---|---|---|---|
| [m-ochi/recon](https://github.com/m-ochi/recon) (8dffe38) | see repo | `recon.py`: RECON reciprocal recommender | Compatibility per attribute = share of the person's past interest in that value; **any zero kills the pair**; both directions combined with harmonic mean |
| [kdevo/chaos-rrs](https://github.com/kdevo/chaos-rrs) (0027f73) | see repo | `recommend/candidates.py`, `recommend/predict/reciprocal.py` | (1) **Candidate-generator chain**: filter → cache → reciprocal filter, each a small composable class. (2) `ReciprocalCG`: forward candidates, then keep only those whose own candidate list contains the user (= our forward + reverse search). (3) Six ways to combine both directions (max, quadratic, arithmetic, geometric, harmonic, **uninorm** `uv/(uv+(1-u)(1-v))`, min). (4) "rank violations" metric: how often one-way ranking disagrees with two-way ranking |
| [david-cortes/contextualbandits](https://github.com/david-cortes/contextualbandits) (fc49364) | BSD-2 | `online.py` LogisticTS / BootstrappedTS, `utils.py` `_LogisticUCB_n_TS_single` | (1) **Logistic Thompson sampling**: fit logistic regression, covariance Σ = (Xᵀ·diag(p(1−p))·X + λI)⁻¹ (Laplace approx.), draw log-odds + N(0,1)·√(xᵀΣx), then sigmoid. (2) **`beta_prior` cold-start switch**: until an arm has n observations, score it by a Beta draw; switch to the model afterwards. (3) Author's own note: LogisticTS often performs poorly; **BootstrappedTS** (several models on resampled data, pick one at random) is preferred |
| [SMPyBandits/SMPyBandits](https://github.com/SMPyBandits/SMPyBandits) (012fc13) | MIT | `Policies/Posterior/DiscountedBeta.py`, `Policies/DiscountedThompson.py` | **Discounted Beta**: on each update, successes S ← γS + r, failures F ← γF + (1−r); sample Beta(1+S, 1+F). Exactly our "discount old evidence" idea, ~10 lines. Reference: Raj & Kalyani 2017 |
| [JohnDickerson/kidney_solver](https://github.com/JohnDickerson/kidney_solver) (dc57446) | GPL-2 (**do not copy code**) | `kidney_digraph.py` `failure_aware_cycle_score`, `kidney_utils.py` chains | **Failure-aware weights**: an exchange's value is multiplied by the chance every edge in it succeeds. For us: pair weight = value × P(A yes) × P(B yes) × P(date happens) |
| [daffidwilde/matching](https://github.com/daffidwilde/matching) (497602e) | MIT | `algorithms/stable_roommates.py` (Irving) | Stable matching for a **one-sided pool** (our case). Useful as a comparison/ablation: "stable" vs "maximum total value". Needs full preference rankings, so not our main matcher |
| [networkx/networkx](https://github.com/networkx/networkx) | BSD-3 | `algorithms/matching.py` | `max_weight_matching` (Edmonds blossom, O(n³)); **use integer weights** (the docstring warns float weights can give slightly suboptimal results → scale scores ×10⁶ and round). `maximal_matching` = greedy O(E) fallback |
| [LeafyChan](https://github.com/LeafyChan) (friend) | – | public repo list | No public repo on recommendation/matching (invoice, games, quantum, cybersecurity). Ask him directly for the friend-suggestion work |

### Lecturer's repo: keith-17/data-projects @ 8221616312bffceae1b78d6cdc857d6ef3219eb4 (no licence file → ideas only, no code copy)
- `CAVU/analysis/analysis.ipynb`: car-park forecast. GroupShuffleSplit by quarter/terminal/car park; correlation top-8 feature
  selection; RF GridSearchCV; LR/ARIMA/RF/XGB/MLP/SVR compared on R², MAE, RMSE; vectorised booking→day expansion (`general_utils.py`).
  Same-week booking aggregates used as features → possible leakage (our reading).
- `numerai/*`: GroupKFold by era. `research_center_assignment/`: experiments dict, FastAPI, Docker, pytest regression checks.
- Takeaways for us: grouped hold-out by world/seed; experiments dict for ablations; regression tests on the policy interface.

### Fairness / "averaging" in matching (researched 8 Oct; V = verified by reading code or abstract, R = from memory, not re-checked)
- **Code read (V):**
  - FairRec (github.com/gourabkumarpatro/FairRec_www_2020 @ ad2c455, `FairRec.py`): a cap on how often each producer is shown, plus round-robin picking.
  - FA*IR (github.com/fair-search/fairsearch-fair-python @ a92a3d6, `re_ranker.py fair_top_k`, `mtable_generator.py`): a minimum-quota floor for the protected group.
  - Neither uses an upper cutoff; both use floors or quotas for the disadvantaged.
  - networkx `max_weight_matching(maxcardinality=True)` = the best weight among the matchings with the most pairs.
- **Papers:**
  - Dickerson, Procaccia & Sandholm, AAMAS 2014 (V): the price of fairness is usually small.
  - McElfresh & Dickerson, AAAI 2018 (V): it can be large.
  - Bertsimas, Farias & Trichakis, Oper. Res. 2011 (R): price of fairness bounds.
  - Ma, Xu & Xu, AAMAS 2022 (V): group max-min in online matching.
  - Rios, Saban & Zheng, MSOM 2023 (V): dating apps spread attention because popular users get congested; ≥27% more matches in the field.
  - Tomita & Yokoyama, arXiv 2601.13609 (V): Nash welfare (Σ log) vs match count.
  - Caragiannis et al., EC 2016 (R) and Mo & Walrand 2000 (R): Nash welfare and α-fairness.
- **Conclusion for us:**
  - Keep Σ q with maxcardinality. **No upper cutoff.**
  - The real-app reason for averaging (congestion of popular users) does not exist in the simulator.
  - The real "best pair taken" problem here is over **time** (busy 8 days, people leave) → handled by urgency and scarcity boosts.
  - Overconfident top scores → shrink scores toward the mean (Beta prior).
  - Optional toggles to test (same seeds, 50+): √q, log q + 10 (safe only with maxcardinality), coverage-first (q + 10 × number of never-introduced people in the pair), max-min via binary search on a threshold.

## 2. Papers

| Topic | Paper | Piece for us |
|---|---|---|
| Stochastic matching with patience | Chen, Immorlica, Karlin, Mahdian, Rudra. *Approximating Matches Made in Heaven.* ICALP 2009 | Dating-motivated; limited "probes" per person; greedy ≥ 1/4 OPT |
| Few queries | Blum, Dickerson et al. *Ignorance Is Almost Bliss.* Oper. Res. | O(1) queries per vertex ≈ full optimum → a few asks per person may be enough |
| Fully online matching | Huang et al. *How to Match when All Vertices Arrive Online.* STOC 2018 | Arrivals + deadlines; Ranking 0.5211-competitive |
| Stochastic rewards | Mehta & Panigrahi. FOCS 2012 | Matches succeed with probability p |
| Dynamic matching | Akbarpour, Li, Oveis Gharan. JPE 2020 | Wait only if you know who is about to leave |
| Logistic Thompson | Chapelle & Li. *An Empirical Evaluation of Thompson Sampling.* NeurIPS 2011 | Laplace-approx. logistic TS; strong baseline |
| Reciprocal recommenders | Pizzato et al. RECON (RecSys 2010); survey arXiv 2007.16120 | Both-direction compatibility; harmonic mean |
| Congestion | 2023 field experiment on two-sided matching in online dating (Int. Econ. Review); arXiv 2411.19214 | Ranking by predicted probability concentrates on popular users → matching across the pool fixes it |

## 3. Our experiments (scripts in `experiments/`, run from the organiser kit folder)

### 3.1 Filtering at 100,000 people (`bench_100k.py`) — all 11 dealbreakers, both directions
35,051 people with complete dealbreakers; every method found the **same 7,970,144 allowed pairs**.

| Method | Build | One new arrival | All pairs |
|---|---|---|---|
| User's 1/0 row (early exit) | – | 21.7 ms | 791.5 s |
| Blocking index (gender × zone buckets) | 0.02 s | 8.7 ms | 289.1 s |
| Bitmap index (Python big ints) | 0.39 s | 1.4 ms | 35.6 s |
| **Columnar (numpy arrays)** | 0.30 s | **0.21 ms** | **6.1 s** |

Columnar is ~100× faster than the row-by-row idea per arrival and ~130× for all pairs. Same logic, applied to whole columns at once.

### 3.2 Soft-field weights (`soft_weights.py`) — logistic regression on simulator packets
Packets = features visible at introduction time + the later observed reply (no-reply dropped). Train seeds 1000–1029, test 2000–2014.

| Feature set | Test log-loss (development) | Test log-loss (shift) |
|---|---|---|
| Base rate only | 0.6926 | 0.6863 |
| **4 soft fields** | **0.6898** | **0.6749** |
| All 7 soft | 0.6907 | 0.6772 |
| 7 soft + mutual/other | 0.6912 | 0.6780 |

- Adding mutual fields (wants_children, schedule overlap, same zone, age gap) **made held-out predictions worse** → keep them as filters only.
- Development weights: goal match +0.71 / differ −0.37 is strongest. Shift weights: pace +0.68, conversations +0.53, lifestyle match −0.23 → **weights must be learned online**.
- AUC is only ~0.55: soft fields explain a little; hidden personal tendencies and luck dominate. **More good introductions matters more than a perfect scorer.**

### 3.3 Combining both directions (`combine_directions.py`)
Product, harmonic mean, uninorm, minimum and arithmetic mean all gave AUC 0.561. Reason: soft-field match/differ is symmetric, so P(A yes) = P(B yes) for every pair. The rule only matters once person-level (asymmetric) signals exist. Default: **product** (the actual probability that both say yes, assuming independence).

### 3.4 Predicting what an ask unlocks (`asker_prediction.py`)
Fill a Pending person's unknown dealbreakers by copying them from random complete people of the same gender (30 samples) and count allowed partners. Truth used only for scoring. 10 worlds, day 0:

| Asking 4 people chosen by | Real partners unlocked (avg) |
|---|---|
| Random | 0.62 |
| **Our prediction** | **1.32** |
| Perfect hindsight | 2.90 |

Prediction doubles the value of each ask. Correlation predicted vs real: 0.37.

## 3.5 Friend's work: "Fresher Friend Matching" architecture + mathematical appendix (25 pp)
Campus friend recommender (N≈500): ingestion → scoring (MaxSim-IDF interests, co-location uplift, schedule
Jaccard, hand-set weights) → assignment (degree-capped b-matching with floor ≥ 1, greedy ½-approx; submodular
slate diversification) → serving (80/20 exploit/explore, propensity logging) → measurement (IPW, A/B power).

| His section | Idea | Fit for us | Action |
|---|---|---|---|
| §2 Funnel, elasticity = 1 | Output = product of stage rates; +x% at any stage = +x% output | ✅ MSMI = intros × P(both yes) × P(date) × P(both 2nd yes) | Since the scorer only reaches AUC ~0.55, raise the cheapest stage: **number of valid introductions** (asker, daily matching) |
| §3 Compute budget | At small n, score all pairs; no retrieval system | ✅ at 200 | Already shown: columnar does both small and 100k |
| §4 IDF / MaxSim | Rare shared interests count more; soft document frequency | ⚠️ our soft fields are 2–4 fixed categories, simulator rewards any match equally | Not adopted (could test) |
| §5 Uplift Δ = P(do: rec) − P(no rec) | Don't waste slots on pairs who'd meet anyway | ❌ in our simulator nobody meets without an introduction | Keep idea of opportunity cost via urgency |
| §6 Hand-set weights (too little data) | Prior weights, revise by A/B | ⚠️ we can fit offline from unlimited simulator data | Fitted weights = prior; online updates must be gentle (see §14) |
| §7 b-matching with **floor ≥ 1** | Top-k per user starves low scorers; guarantee each user ≥ 1 | ✅ coverage is our 1st tie-breaker | Boost never-introduced people; "repair pass" for anyone with an edge but no intro |
| §8 Submodular slate diversity | 1 − ∏(1 − q): correlated bets are one bet | ⚠️ one intro at a time here | Optional: vary partner profile across a person's successive intros |
| §9 ε-greedy from **mid-score band**, propensity logging, IPS | Explore among plausible, not bottom decile | ✅ Thompson already explores near ties; IPS unnecessary (we run full simulator episodes) | Keep exploration within plausible pairs |
| §10 Null-model noise floor (CV) | Check a feature's spread when there is no signal | ✅ method | Use to sanity-check any new feature |
| §11 Power for A/B | n per arm from z-scores | ✅ critical | **MSMI ~1 success/episode → detecting 1.0→1.5 needs ~79 episodes per policy; 1.0→1.25 needs ~283.** Develop on mutual acceptances (18→22.5 needs ~16) and confirm on MSMI |
| §14 Events-per-variable ≥ 10 | Cap model size by outcome count | ✅ | One episode gives ~190 replies (~95 of the rarer class) → ≤ 9 parameters online; early days far fewer → strong prior from offline fit, light online updates |
| §16 Binding-constraints table | One table of the numbers that limit everything | ✅ format | Use in our Round 1 note |

## 4. Adopt list (decisions)
1. Filter: **columnar numpy masks** (scales best); keep per-rule 1/0 row only for explanations.
2. Candidate pipeline structure from chaos-rrs: filter → cache → reciprocal check.
3. Scorer: **discounted Beta** counts (SMPyBandits) for cold start → **bootstrapped logistic TS** once enough replies (contextualbandits pattern).
4. Pair weight: failure-aware (kidney_solver idea) = P(A yes)·P(B yes)·P(date) × urgency.
5. Matcher: networkx `max_weight_matching` with **integer-scaled weights**; greedy `maximal_matching` as an ablation.
6. Asker: donor-imputation prediction of partners unlocked (tested: 2× random).
7. Ablations to report: stable roommates vs max-weight; harmonic vs product once asymmetric signals exist.

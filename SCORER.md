# The scorer, from zero

**What it is:** a function that gives a number between 0 and 1: *"how likely is A to say yes to B?"*.
For a pair we do this both ways and multiply: **pair score = P(A yes to B) × P(B yes to A)**.

## The real data (development scenario, 30 worlds, 4,207 replies, `experiments/yes_rates.py`)
Only fields **we can see** are used; that is how the policy works.

| Clue (soft field) | Yes-rate when it matches | Yes-rate when it differs | **Unknown in** |
|---|---|---|---|
| (no clue, everyone) | 0.48 | | |
| relationship goal | **0.56** | **0.40** | 66% of replies |
| relationship pace | 0.55 | 0.45 | 67% |
| lifestyle | 0.55 | 0.44 | 67% |
| conversations | 0.54 | 0.47 | 66% |

Two lessons:
1. Goal is the strongest clue, but even it only moves the chance from 0.48 to 0.56 or 0.40.
2. **Two-thirds of the time we can't see the clue at all.** The biggest improvement is not a cleverer formula. It is **knowing more fields**: asking a soft field costs 1 point, and 72% of the ask budget is unused.

## The recipe, step by step

**Step 1: start from the average.** Everyone has a 0.48 chance. That is a scorer already, just a dumb one.

**Step 2: turn each clue into a multiplier.** We work in *odds* (chance ÷ (1 − chance)), because odds can be multiplied safely. Odds 0.48 → 0.92.

| Clue | Match multiplier | Differ multiplier | Unknown |
|---|---|---|---|
| goal | ×1.38 | ×0.72 | ×1 |
| pace | ×1.32 | ×0.89 | ×1 |
| lifestyle | ×1.32 | ×0.85 | ×1 |
| conversations | ×1.27 | ×0.96 | ×1 |

**Step 3: combine the clues.** Multiply the odds, then convert back.
Example: A→B where goal matches, lifestyle differs, and the rest is unknown:
odds = 0.92 × 1.38 × 0.85 = 1.08 → chance = 1.08 / 2.08 = **0.52**.
*(This is "logistic regression" or "naive Bayes" in textbook words: adding log-odds is the same as multiplying odds.)*

**Step 4: both directions.** For example 0.52 × 0.60 = **0.31** = the pair score.

**Step 5: learn while running.** The multipliers above come from past worlds. In a new world people may behave differently (the shift scenario: matching lifestyles *hurts*). So we keep counting replies each day: "when goals matched: X yes, Y no".

**Step 6: the normaliser (user's idea).** Do not let a few lucky replies swing a multiplier. Start each count with **40 imaginary replies** at the past-world rate, so real data has to outweigh them. This pulls overconfident scores back toward the average.

**Step 7: ageing (forget old replies slowly).** Each reply's weight is multiplied by **γ every day**.
- γ = 0.98: a reply counts half after 34 days.
- γ = 0.95: a reply counts half after 14 days.

The 8-day busy period does not matter here: the counts are pooled over **everyone**, and replies arrive every day from different people.

The right γ is a trade-off:
- too low → we forget useful data, and the scores get noisy;
- too high → we react slowly when behaviour changes (drift scenario, day 35).

**Plan:** let evolutionary search pick γ in 0.90–1.00 on training worlds, then check it on separate worlds.

**Step 8: test the scorer on worlds it has never seen.** Two checks:
- **Calibration:** when it says 0.6, do about 60% say yes?
- **Does it raise wins** in the full simulation?

## Decisions for the user
1. **Clues:** the 4 soft fields (data shows the dealbreaker fields add nothing). Add **reply reliability** (people who ignore messages)?
2. **Target:** score only "both say yes" (now), or the whole journey to "both want a second date"? Goal matters again at the second-date step.
3. **Spend the unused budget** to ask soft fields (goal first), so fewer clues are unknown?

---
# Version 2 (8 Oct): conditional probabilities along the whole journey
Measured with `experiments/funnel_probs.py`: kit greedy baseline, development scenario, 30 worlds, 5,468 reply chances. Only observable fields are used.

## What the data says

| Question | Answer |
|---|---|
| P(reply) | 0.76 |
| P(reply \| replied last time) vs P(reply \| silent last time) | **0.77 vs 0.68**: reply habit is a lasting personal trait |
| P(yes \| replied) | 0.48 |
| P(yes \| said yes last time) vs P(yes \| said no last time) | **0.51 vs 0.44**: pickiness is a lasting trait too |
| P(yes \| goal same) vs P(yes \| goal different) | **0.61 vs 0.37** |
| P(yes \| goal and pace both same) | 0.70 (predicted by adding the two effects in log-odds: 0.70) |
| P(yes \| goal and pace both different) | 0.32 |
| P(date \| both yes) | 0.76 |
| P(second answer arrives \| date) | 0.79 |
| P(second yes \| date), goal same / different / unknown | **0.63 / 0.64 / 0.65: no visible effect** |
| P(second answer on time \| answered) | 0.60 |

(An earlier sample, `yes_rates.py` on 30 other worlds measured on day 70, gave goal 0.56 vs 0.40. Same direction, sampling noise.)

## Conclusions
1. **Clues add up in log-odds with no interaction.** Goal and pace together: predicted 0.70, observed 0.70. So the logistic model (multiply odds, add log-odds) is the correct form. A table of every combination is not needed. This is the "naive Bayes / logistic" structure, checked on data.
2. **The second-date step shows no visible goal effect, even though the simulator code has one (+0.4 log-odds).** The reason is **selection bias**: pairs with different goals only reach a date if they had good shared luck, and that same luck also helps at the second step. Ad systems hit the same problem with "click then buy": they model the whole chain over **all** introductions (ESMM, Ma et al., SIGIR 2018, cited from memory).
   For us: score the whole journey as a chain of conditional probabilities:
   **P(win) = P(both reply) × P(both yes | replied) × P(date) × P(both answer second) × P(both yes second) × P(both on time)**
   The visible clues only change the "both yes" factor. The rest is constant across pairs, **except reply habit, which appears twice**: once at the introduction and once at the second date.
   So for ranking pairs: **journey score ∝ P(A yes) · P(B yes) · rA² · rB²**, where r = the person's reply rate.
3. **Per-person memory helps.** Reply habit and pickiness carry over between a person's introductions. Each person gets two small Beta counts:
   - replies: start Beta(7.6, 2.4), i.e. 0.76 worth 10 imaginary replies;
   - yes: start at their clue-based chance.
   Each person only has about 3–7 introductions, so the starting counts keep these gentle (this is the normaliser).
4. **Thompson sampling.** Each day, every uncertain number (each field multiplier, and each person's reply rate and pickiness) is **drawn** from its Beta belief instead of using the average. Pairs we are unsure about sometimes get a high draw and get tried; with more data the beliefs narrow and the draws settle (Chapelle & Li 2011; Russo et al. 2018 tutorial; cited from memory).

## Ageing: the exact number, with proof
**Claim:** in this simulator the best ageing multiplier is **γ = 1 (no ageing)**.
1. From `kit.py` `_prob`: each field's effect is **constant for the whole episode** in every scenario.
   - *shift* uses different weights from day 0, so they are constant within the episode;
   - *drift* subtracts 0.5 from **everyone's** log-odds from day 35, which changes the base, not the field effects;
   - hidden traits (pickiness, reply rate) are fixed per person.
2. For a constant rate p estimated from replies y₁…yₙ with weights wᵢ (Σwᵢ = 1), the variance is p(1−p)·Σwᵢ². By Cauchy–Schwarz, Σwᵢ² ≥ (Σwᵢ)²/n = 1/n, with equality only when all weights are equal. Any γ < 1 gives unequal weights, so **more noise and no reduction in bias** (there is nothing to track). Over 60 days the effective share of data used is γ = 1: 100%, 0.98: 89%, 0.95: 59%, 0.90: 32%.
3. General formula (when things really do drift, as in a real app): exponential smoothing is the optimal filter for a "slowly wandering level" (Muth 1960). The best weight is α = (−q + √(q² + 4q))/2, where q = (how much the true rate wanders per day)² ÷ (noise of one day's data)², and γ = 1 − α.
   - Here q = 0, so α = 0 and γ = 1, consistent with the claim.
   - In a real app, q would be measured from history (e.g. q = 0.001 gives γ = 0.97).
4. Drift lowers **everyone** equally on the same day, so the order of a person's options is unchanged. Ranking does not need to know the base dropped.

Retrospective: the prototype used γ = 0.98 "for drift". The maths shows that only costs data (11%) and buys nothing here.

---
# Version 3 (8 Oct): the extra data a good scorer needs, all 6 scenarios
`experiments/scorer_data.py`, kit greedy baseline, 15 worlds per scenario. Fields are taken **as known at decision time**. Results are in `experiments/results/scorer_data_*.txt`.

## 1. Yes-rate when a field is the same vs different
| Field | development | shift | sparse | cold_start | delayed | drift |
|---|---|---|---|---|---|---|
| goal | 0.59 / 0.37 | **0.49 / 0.46** | 0.54 / 0.41 | 0.58 / 0.42 | 0.57 / 0.40 | 0.56 / 0.34 |
| pace | 0.56 / 0.43 | **0.62 / 0.41** | 0.78 / 0.37 | 0.55 / 0.46 | 0.59 / 0.45 | 0.54 / 0.40 |
| lifestyle | 0.50 / 0.44 | **0.39 / 0.49 (reversed)** | 0.60 / 0.43 | 0.59 / 0.48 | 0.50 / 0.47 | 0.48 / 0.42 |
| conversations | 0.46 / 0.50 | 0.55 / 0.46 | 0.43 / 0.49 | 0.59 / 0.47 | 0.49 / 0.51 | 0.43 / 0.47 |
| emotional_availability, space_for_relationship, relocate | ≈ equal in every scenario: **no effect** (matches the code) | | | | | |

- Small cells (sparse: 447 replies in total) are noisy. Conversations moves either way.
- **Shift really is different:** pace matters most, goal barely matters, and matching lifestyles *lowers* the chance. A starting belief fitted on development points the wrong way for lifestyle.

## 2. How much we can see, and how much we learn
| | development-like | cold_start | sparse |
|---|---|---|---|
| Each soft field unknown at decision time | **61–64%** | **81–83%** | 61–65% |
| Yes/no replies per world, days 0–9 / 10–19 / 20–29 / … | 25 / 39 / 31 / 20 / 13 / 10 | 15 / 33 / 31 / 19 / 12 / 8 | 9 / 13 / 6 / 1 |
| Introductions per introduced person | median 2, mean 2.3 | median 2 | median 1 |

- **Learning is slow:** about 25 replies in the first 10 days, and only ~9 of those have a given field known. Detecting the shift scenario's reversed lifestyle effect takes weeks, but most matching happens early. So **the starting belief matters a lot**, and asking soft fields speeds up learning too.
- **Per-person memory has little data:** most people get only 2 introductions. Reply habit and pickiness help a little, but the starting counts must dominate.

## 3. How good can any scorer ever be? (offline, using the hidden truth)
AUC = the chance the scorer ranks a random "yes" above a random "no" (0.5 = coin flip, 1 = perfect).

| Scorer knows… | AUC (all scenarios) |
|---|---|
| Our scorer today (63% of fields unknown, learned weights) | ~0.55 |
| **All 4 soft fields exactly, with the true weights** | **0.61–0.65** |
| + each person's hidden pickiness | 0.70–0.72 |
| + the pair's hidden shared luck | 0.74–0.75 (the rest is a coin flip) |

**Conclusion:**
- Most of the gap between today (0.55) and a perfect soft-field scorer (0.64) comes from **unknown fields**, not the formula. So **asking soft fields with the unused budget is the scorer's biggest lever.**
- Pickiness is worth about as much again, but people get only ~2 introductions, so it can only be learned a little.
- Above 0.75 is impossible: it is luck.

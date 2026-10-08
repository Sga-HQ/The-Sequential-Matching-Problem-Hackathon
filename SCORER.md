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

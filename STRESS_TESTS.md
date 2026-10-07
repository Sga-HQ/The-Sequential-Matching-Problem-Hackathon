# Hidden-world traps and stress tests

The question: what could organisers hide in the private worlds that makes most policies fail?

**What the kit says.** The six scenario families are named publicly (development, sparse, cold_start, delayed, shift, drift), and `evaluate.py` builds them with the same public generator (`kit.generate(seed, 200, ..., variant)`). Only the **seeds** are secret, and the kit says the public variants "let teams test the same categories". So the most likely truth is the same rules with different random worlds.

We still prepare for more than that, for three reasons:
- the organisers could change details;
- the policy is meant to be reused by a real dating app (kit §15);
- the Round 1 note must explain failure cases.

Two lists follow:
- **A.** traps inside the six known families, read from the simulator code;
- **B.** problems a real dating-app builder meets, used as our own stress tests.

---

## A. Traps inside the six known families (from `kit.py`)

| Family | What changes in the code | How a naive policy fails | Our defence |
|---|---|---|---|
| sparse | 12 zones; each person accepts only their own zone | Each person has almost no partners (coverage ceiling 0.16). A policy that **waits** for a better partner strands people. | Match now, maximise the number of pairs, give priority to people with few options |
| cold_start | Only 20% of profiles are complete (35% normally) | Asks run out (4 bundles/day). A learner has little data, so a strong prior dominates. | Spend the budget on people whose unlock creates pairs; rely on the offline prior |
| delayed | Dates come 5–12 days later | 1. Feedback arrives late; a learner that treats "no answer yet" as failure learns that everything fails (right-censoring). 2. People stay busy longer. 3. A date must happen within 30 days of the introduction, so a few wins become impossible. | Learn only from replies that have arrived; pending ≠ no |
| shift | Weights change: pace 0.8, conversations 0.5, **lifestyle −0.25** (matching lifestyles now *hurts*), goal 0.25 | A prior fitted on development pushes the wrong pairs, and a strong prior is slow to unlearn | Discounting plus Thompson. **To test:** is prior strength 40 too strong to unlearn in time? |
| drift | Acceptance drops (−0.5 log-odds) from day 35 | A non-ageing learner trusts old, happier data; it is also worth introducing pairs **before** day 35 | Ageing γ = 0.98. **To test:** whether front-loading introductions before day 35 helps |

## B. Dating-app builder stress tests (beyond the public families)

| # | Real-world situation | Why an app builder worries | What would break | Defence / test |
|---|---|---|---|---|
| 1 | **Partly filled profiles** (1–3 dealbreakers missing; *your idea*) | Real users skip one awkward question; public worlds have nobody like this (everyone askable misses 7–11) | A policy that assumes "complete or nearly empty" mis-values the asks | First use the known fields to rule people out (`eligibility` already returns infeasible on a known failure even with gaps); ask only if a partner is still possible |
| 2 | **Ghosting wave** (reply rates fall to 20–50%) | Common after app updates and at holidays | Treating a missing reply as "no" corrupts learning (the kit says missing ≠ label) | Missing replies count as neither yes nor no; track each person's reliability separately |
| 3 | **Launch surge** (half the pool arrives on one day, or after day 20) | Marketing campaigns, university terms | A policy that "used up" everyone early has no partners left for newcomers; the asker is overloaded | Re-plan daily; the asker values new arrivals |
| 4 | **Early churn** (30–50% leave from day 5) | The biggest problem in real dating apps | Waiting policies lose people | Introduce early; prioritise people with few options |
| 5 | **Unbalanced market** (80/20 gender split, many people wanting the minority group) | Typical in real apps | Competition for the same few people: pair-by-pair ranking double-books them | Matching (one pair per person) plus capacity-aware choice |
| 6 | **Bigger pool** (1,000–5,000 people) | Growth | The **10-second limit** (2 cores, 1 GiB) is exceeded, which **disqualifies** the entry. Our prototype's Python pair loop is O(n²). | Columnar filter, a time guard (fall back to the greedy baseline when time runs low), sparse matching |
| 7 | **Odd data**: a day with nobody available, a profile with every field declined, age_min > age_max, an empty who_to_meet, a value never seen before | Data-quality bugs | A crash or invalid output **disqualifies** the entry | Defensive code; on any doubt return no pairs (always valid); fuzz tests |
| 8 | **Different budget or costs** | Product change | Hard-coding 12 or 3 makes asks over budget → invalid | Always read `ask_budget_remaining` from the state (the prototype already does) |
| 9 | **Very late or out-of-order feedback** | Notification delays | Counting a reply on the wrong day; double counting | Use `observed_day`; never use events from the future |
| 10 | **Memory growth** over 60 days | Long-running service | Carried memory > 1 MiB → invalid | Store only small counts, not histories |

## How we will use this
- **Round 1 note, "failure cases":** list A and items 1, 2, 4, 5 and 6 from list B, with the defence for each.
- **Round 2:** build a `stress_worlds.py` that changes kit worlds (partial profiles, ghosting, surge, churn, imbalance, 2,000 people, odd data) and require **zero invalid episodes**, with the score no worse than greedy in each.

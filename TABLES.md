# Tables (user's design, 8 Oct): what they hold, how people move, and the daily flow

The program is restarted every day, so the tables are rebuilt each day from what the app shows us.
Only small learned numbers are carried over in memory.

## The 6 tables

| # | Table | Holds | Where it comes from |
|---|---|---|---|
| 1 | **User data** (who I am) | age, gender, zone, smoking, has children + soft fields + a **"ready"** column (all dealbreakers known: yes/no) | app, each day |
| 2 | **User preference** (who I want) | age range, who to meet, zones, partner smoking/children, relationship structure, wants children, schedule | app; same person ID as table 1 (one-to-one) |
| 3 | **Busy** | person + day introduced + timer | derived from History and the app's `available` flag |
| 4 | **Blocked** | people who refused a dealbreaker question | app, visible on arrival, permanent |
| 5 | **Retired** | pairs who both want a second date (both people paused for good); also people who left the app | derived from History |
| 6 | **History** | every introduction made, plus replies as they arrive; stops repeats | the app gives the full list each day |

"Pending" and "Active" are **not tables**. They are the "ready" column plus "not busy / blocked / retired".

**Busy timer (simulator rules):**
- Introduced on day t → free again on **day t+8**.
- If both say yes → the timer is reset to **6 days after the date**. The date comes 1–14 days after the later reply, so free again between day t+8 and t+27 (later in the delayed scenario).
- If both then want a second date → **Retired**.

**No "allowed pairs" table.** That was a cache of the dealbreaker check, not scoring. Measured: re-checking every free pair from scratch takes ≤ 26 ms per day at 200 people, so a cache adds complexity for no gain.

## Daily flow (existing and new people together)

```
ASK PHASE
 1. Rebuild tables 1–6 from today's app view.
 2. Choose whom to ask (12 points): people who are not ready, not blocked, not busy.
    Answers come back the same day → they become "ready".
MATCH PHASE (app view refreshed after the asks)
 3. Today's list = ready AND not busy AND not blocked AND not retired.
 4. Filter: for every pair in today's list → all dealbreakers pass both ways AND not in History.
 5. Score each surviving pair: P(A says yes) × P(B says yes), from the soft fields.
 6. Match: pick the set of pairs with the highest total, each person at most once.
 7. Safety: official checker on each chosen pair → send. Chosen people go to Busy (timer starts).
```

## Measured daily work (5 development worlds × 60 days, `daily_cost.py`)

| Days | People arrived | Free & ready | Pair checks | Allowed pairs | Introductions made | Time (filter / score / match) |
|---|---|---|---|---|---|---|
| 0 | 143 | 59 | 1,712 | 21 | 9.6 | 7.8 / 0.2 / 1.1 ms |
| 1–9 | 158 | 57 | 1,667 | 3.2 | 2.0 | 7.3 / 0.2 / 0.2 ms |
| 10–19 | 186 | 86 | 3,684 | 4.1 | 2.2 | 16.6 / 0.3 / 0.3 ms |
| 20–39 | 200 | 105 | 5,450 | 1.9 | 1.1 | 24.5 / 0.4 / 0.2 ms |
| 40–59 | 200 | 109 | 5,956 | 0.9 | 0.5 | 25.9 / 0.4 / 0.1 ms |

- The slowest day was **45 ms**, against the 10-second limit. Importing numpy and networkx adds about 0.1–0.3 s.
- After day 20, ~105 people are free and ready, but only ~1–2 allowed pairs exist among them: **most people have used up their partners.** This is the "~3 partners each" wall seen from the inside.

## Real-app design at scale (for the note; decided 8 Oct)
- **Filter method:** column checks (numpy) from day one. At 200 people every method takes milliseconds. At 100,000 people, measured: 0.21 ms per new person vs 21.7 ms for pair-by-pair; 6.1 s vs 791 s for all pairs; all methods give identical pairs. Cheap, no downside, so use it from the start.
  *Honest scope:* the 100k test covered the **filter** only. Exact matching (blossom) would be too slow at 100k; there you would match within groups (connected components) or use a greedy approximation.
- **Allowed-pairs table (real app only):** columns `pair · score · score_day`, kept ranked per person.
  - The dealbreaker result never changes (preferences are fixed).
  - The score is refreshed daily (learning changes it). That costs about 8 multiplications per pair.
  - The hackathon cannot carry it between days (1 MiB memory limit; 100k → ~8M pairs ≈ 64 MB), so there we recheck daily.
- **Simultaneous arrivals (user's question):** with a saved table, if A and B arrive together and A is checked before B is added, the pair A–B is missed. The fix:
  1. **Insert first, then check.** Add the whole batch of newcomers to the people table, then check each newcomer against **old + new** people.
  2. **Store each pair once,** keyed by (smaller ID, larger ID), so A–B and B–A cannot both be added.
  3. In a live system, process arrivals through one queue (or a database transaction), so a later arrival always sees an earlier one. A nightly full sweep catches anything missed.
  In the hackathon this cannot happen: the app is day-based and we recheck everyone daily.
- **No "asked" column needed:** asking a pending person always makes them ready. Refusals are visible on arrival (→ Blocked), and an ask never creates a refusal.
- **Leaving:** the simulator decides it at random when the person is created (12% leave, on a random day 22–59). It is unrelated to anything we do or see, so it cannot be reduced, only beaten by introducing people early. We infer a "left" column: unavailable with no busy timer running.
- **Age:** fixed for the whole 60-day episode (no date of birth in the data). A real app should store the date of birth and recompute the age daily, because people can cross an age-range boundary.

## What comes back after an introduction (History table), and how we use it
Measured with the kit's greedy baseline, development scenario, 10 worlds (`experiments/feedback_stats.py`). Counts are per world, 86 introductions each on average.

| Event | When it arrives (days after introduction) | Per world | Values |
|---|---|---|---|
| Introduction reply (one per person) | median 5, at most 7 (no reply is reported on day 7) | 172 | yes 65 · no 65 · **no reply 42 (24%)** |
| Date happened (only if both said yes) | median 12.5, at most 21 | 14 | yes 11 · no 3 |
| Second-date answer (one per person) | median 16, at most 26 | 22 | yes 11 · no 6 · no reply 5 |
| Paused (both want a second date) | median 16, at most 23 | 2.3 | – |

How each piece is used:
1. **Learning what people like (scorer).** Every yes/no reply updates the counts per soft field (goal, pace, lifestyle, conversations). "No reply" is **not** a no, so it does not enter the yes/no counts. Old replies count less (× 0.98 per day).
2. **Reply reliability per person (new).** A win needs each person to reply **twice** (introduction and second date). People who have already ignored replies are less likely to complete the journey. Measured: on average 24% of a person's replies are missing, and 29% of people with ≥2 introductions miss at least half. Use: lower the pair score for people with a record of not replying (with a gentle prior, because counts are small).
3. **Busy / Retired bookkeeping.** Mutual yes → the busy timer extends to 6 days after the date. Paused → Retired.
4. **Waiting is not failure.** An introduction with no answer yet stays "waiting". Only answered events count.
5. **Wrong-belief check.** If recent yes-rates fall well below what the scorer expects (drift scenario, day 35+), ageing lets the counts catch up.

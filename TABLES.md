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

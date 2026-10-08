# The 7 tables: what they hold, how people and pairs move, and when

The program sees the app once a day. The tables are rebuilt from what the app shows each day.
Only small learned numbers are kept in memory.

## The tables

**People tables:** each person is in exactly **one** of these at any time.

| # | Table | Who is in it | Can be paired? |
|---|---|---|---|
| 1 | **Pending** | Arrived, but some dealbreakers were never asked | No; ask first |
| 2 | **Active** | All dealbreakers known and free today | **Yes** |
| 3 | **Busy** | Recently introduced; waiting for replies or a date | No; wait |
| 4 | **Blocked** | Refused to answer at least one dealbreaker | Never |
| 5 | **Retired** | Found a match (both want a second date) or left the app | Never |

**Pair tables:**

| # | Table | What is in it |
|---|---|---|
| 6 | **Allowed pairs** | Every pair that passes all dealbreakers both ways and has not been introduced yet |
| 7 | **History** | Every introduction made, plus the replies and outcomes as they arrive |

## How people move (with timing from the simulator code)

```
                arrives (70% on day 0, the rest on days 1–20)
                        │
     ┌──────────────────┼──────────────────────┐
     ▼                  ▼                      ▼
 [4 BLOCKED]       [1 PENDING]  ──asked──▶ [2 ACTIVE]  ◀──────────────┐
 refused a field   missing fields   same day  complete & free           │
 (visible on                                     │ introduced on day t  │ free again
  arrival; final)                                ▼                      │
                                             [3 BUSY] ───────────────────┘
                                                 │   • normally free again on day t+8
                                                 │   • if both said yes: busy until 6 days after the date
                                                 │     (between day t+8 and t+27; later in the delayed scenario)
                                                 ▼
                                            [5 RETIRED]
                                both want a second date (paused once both answers are in)

 Anyone not yet retired can LEAVE the app (12% of people, between days 22 and 59) → [5 RETIRED]
```

- Pending → Active takes **one ask** (3 points) and the answer comes **the same day**. Asking never creates a Blocked person: refusals are visible from arrival.
- **"Left" and "Busy" look the same** to us: both show `available = false`. We tell them apart from History. If someone is unavailable with no introduction in the last 8 days and no date pending, they have left.

## How pairs move

```
 two people both in Active or Busy, all dealbreakers pass both ways
        │  (searched ONCE, when a person's dealbreakers first become fully known)
        ▼
 [6 ALLOWED PAIRS] ── shown only when both people are Active (hidden, not deleted, while one is Busy)
        │  chosen by the matcher on day t
        ▼
 [7 HISTORY] ── replies arrive over the next days
                 day t+1 … t+7      : each person says yes / no, or no reply (we learn "no reply" on day t+7)
                 if both said yes   : date 1–14 days after the later reply (78% of dates happen)
                 after the date     : each person's second-date answer within 1–5 days
 An allowed pair is deleted when either person is Retired.
```

## How the tables feed scoring

```
 [7 HISTORY] replies ──▶ COUNTS per soft field (goal, pace, lifestyle, conversations)
                         "when goals matched, how many said yes / no?"  (older replies count less)
                                   │
                                   ▼
 [6 ALLOWED PAIRS] among [2 ACTIVE] people ──▶ SCORE each pair = P(A says yes) × P(B says yes)
                                   │
                                   ▼
                          MATCHER picks the best set → new rows in [7 HISTORY]
```

Feedback is **delayed**: today's score uses only replies that have already arrived. An introduction with no reply yet is **pending**, not a "no".

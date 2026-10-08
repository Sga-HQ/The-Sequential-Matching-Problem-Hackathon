# Edge cases the introducer must handle

The user asked for every case like "A meets B, B is busy, C loses out", i.e. ways a decision today hurts someone later.
Timings come from `kit.py`. Status: **handled** · **partly** (proxy in place) · **planned** · **n/a** (cannot be influenced).

## A. Time: today's choice blocks tomorrow
| # | Case | Why it hurts | What we do | Status |
|---|---|---|---|---|
| A1 | A–B introduced; B is busy 8 days; C's only partner is B; C leaves meanwhile | C loses their only chance | Boost people with few options, so the scarcest pairs go first | partly |
| A2 | Both say yes → busy until 6 days after the date (up to day t+27) | A "yes" locks both people for weeks | Prefer pairs whose people have no other partners waiting | planned |
| A3 | Success → both paused for good | Their other partners lose options | Unavoidable; it is the goal | n/a |
| A4 | People leave (12%, days 22–59, random) | Pairs not made by then are lost | Introduce everyone with a partner as early as possible, especially before day 22 | partly |
| A5 | Drift scenario: yes-rate drops from day 35 | Later introductions are worth less | Front-load introductions before day 35; ageing of old replies | planned (test) |
| A6 | Delayed scenario: dates 5–12 days later | Longer busy; a date more than 30 days after the introduction does not count | Avoid late-chain waiting; nothing else controllable | n/a |
| A7 | A better partner may arrive tomorrow (arrivals until day 20) | Matching now may waste a slot | Match today (waiting only pays if departures are known; Akbarpour et al. 2020) | handled |
| A8 | Last days (55–59) | Still count: 40-day follow-up after day 59 | Keep introducing until day 59 | handled |

## B. Competition: two people want the same partner
| # | Case | What we do | Status |
|---|---|---|---|
| B1 | X and Y both have only Z | Best-total matching picks one; the other gets a boost while waiting for Z to become free | partly |
| B2 | Best single pair blocks two good pairs (kit A-B-C-D example) | Maximise the total, not the best pair first | handled |
| B3 | A person with many options takes a scarce person's only partner | Few-options boost on the scarce person's side | handled |

## C. People and data
| # | Case | What we do | Status |
|---|---|---|---|
| C1 | A pair is burned after one try (no repeats, even if the date did not happen) | Spend each pair wisely: scarce people's single pair goes to their best moment | partly |
| C2 | A person who never replies (24% of replies missing) wastes their partner's 8 busy days | Reply-reliability factor per person (gentle prior) | planned |
| C3 | A pending person could be someone's best partner if asked | Asker priority (user's rule) | handled |
| C4 | Two arrivals at the same time | Daily recheck (hackathon); arrival queue (real app; see TABLES.md) | handled |
| C5 | "Busy" and "left" look the same | Infer "left" from History (unavailable, no busy timer) | planned |
| C6 | Waiting replies are not failures | Count only arrived answers | handled |

## D. Validity: never disqualified
| # | Case | What we do | Status |
|---|---|---|---|
| D1 | Any invalid pair, overlap, repeat or over-budget ask | Official checker on every pair; read the budget from the state | handled |
| D2 | A day with no allowed pairs | Return an empty list (valid) | handled |
| D3 | Running close to the 10-second limit | Time guard → fall back to the kit's greedy method | planned |
| D4 | Odd data (empty preferences, every field declined, unseen values) | Defensive code; skip the person | planned |

## How evolution fits
The "partly" and "planned" rows mostly come down to **how strong each boost should be**:
- the few-options boost
- the never-introduced boost
- the front-loading strength
- the reliability weight
- the ageing rate

Evolutionary search (differential evolution, offline) tunes these numbers. Fitness is the expected wins on **training worlds**, checked on **separate worlds**. It runs after the scorer exists, because every boost multiplies the score.

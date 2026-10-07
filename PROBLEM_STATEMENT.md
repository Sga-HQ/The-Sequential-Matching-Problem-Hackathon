# Problem Statement — The Sequential Matching Problem

*A short briefing for discussing the hackathon. Organiser kit: https://github.com/RomeoJulietLove/The-Sequential-Matching-Problem*

## 1. The challenge in one paragraph

We must write a program that acts as a **matchmaker** for a population of about 200 synthetic (fake) people over 60 simulated days. Every day the program makes two decisions: **(1) which missing information to ask people for**, under a small daily budget, and **(2) which pairs of people to introduce to each other**. An introduction only counts as a success if **both** people accept it, they go on a date, and **both** say they want a second date. The goal is to maximise the number of successful pairs.

## 2. The pool at a glance

About 200 people take part in each run. Most are present on day 0, the rest arrive by day 20, and about 12% leave between days 22 and 60. Of roughly 19,900 possible pairs, only about 0.5% are allowed, about 13% are unknown until someone answers questions, and about 87% are ruled out by a dealbreaker. On a typical day only 10–20 allowed pairs exist among people who are free, and they fall into a few small, separate groups. Some people want same-gender or non-binary partners, so the pool cannot be split into two fixed sides.

## 3. Hard rules (must hold both ways)

Each person has 11 "dealbreaker" answers: acceptable age range, genders they want to meet, acceptable zones (fictional locations), smoking and partner-smoking, has/partner/wants children, relationship structure, schedule. A pair is allowed only if each person satisfies the other's rules. If any answer is unknown, the pair is blocked until we ask. About a quarter of people refused at least one question — they can never be matched.

## 4. What we control each day

1. **Ask:** 12 budget points per day. Asking one person all dealbreakers costs 3; one soft question costs 1.
2. **Match:** choose any set of allowed, non-overlapping pairs (an empty set = wait a day).

## 5. What makes it hard

- **Sequential:** today's matching removes people for ~8 days and changes tomorrow's options. Waiting may find a better partner, but people may leave.
- **Allocation, not ranking:** taking the single best pair first can be worse overall. Example: values A–B 0.90, C–D 0.05, A–D 0.65, B–C 0.65 → greedy total 0.95, best total 1.30.
- **Unknown weights:** success depends on soft answers (relationship goal matters most), hidden personal tendencies and luck. We only see outcomes for pairs we actually introduce ("selective feedback").
- **Delayed feedback:** replies arrive days later; ~22% never reply (missing, not "no").
- **Rare successes:** only ~1.5% of introductions end in a mutual second-date wish.

## 6. Scoring and limits

- Score = successful pairs per 100 people who arrived, averaged over 120 hidden test worlds in 6 scenario types (standard, sparse geography, cold start, delayed dates, changed outcome weights, changing response behaviour).
- Any invalid introduction anywhere → disqualified.
- Runs offline, CPU only, 1 GB RAM, **10 seconds per decision**, no files kept between calls (state passed back as ≤1 MB JSON).
- Simple baselines supplied: greedy 0.50, no-questions 0.33, random 0.25.

## 7. Our current plan

| Step | Method |
|---|---|
| Find allowed pairs | Bitset index (1/0 columns combined with AND) + per-rule 1/0 check |
| Choose whom to ask | Value of information: ask where the answer could change a matching decision |
| Estimate edge weights | Beta–Bernoulli **Thompson sampling** on yes/no reply counts per soft field, with discounting |
| Prefer long-waiting people | Weight boost by waiting time, few options, nearness to the end |
| Choose today's pairs | **Maximum-weight matching** on a general graph (Edmonds' blossom) |
| Safety | Re-check every chosen pair with the official rule checker |

## 8. Research models we would like your view on

Four models from the literature look very close to our setting. We would value your judgement on which fits best, and which algorithm or proof idea from it we should use.

| Model | Paper | Why it looks relevant |
|---|---|---|
| Stochastic matching with patience | Chen, Immorlica, Karlin, Mahdian, Rudra, "Approximating Matches Made in Heaven", ICALP 2009 | Motivated by online dating. Each edge exists with probability p; each person can be probed only a limited number of times (our people get ~7 introductions). A greedy probing strategy gets at least 1/4 of the optimum. |
| Stochastic matching with few queries | Blum, Dickerson et al., "Ignorance Is Almost Bliss", Operations Research | A constant number of edge queries per vertex achieves almost the full optimum. Our daily "asks" are queries that reveal edges. |
| Fully online matching | Huang et al., "How to Match when All Vertices Arrive Online", STOC 2018 | Vertices arrive over time and have deadlines, like our arrivals, departures and day 59. Ranking is 0.5211-competitive on general graphs. |
| Online matching with stochastic rewards | Mehta and Panigrahi, FOCS 2012 | A match only pays off with some probability, like an introduction that can be refused. |

Specific questions:

1. Which of these models fits our problem best?
2. Is Ranking (or a variant) better than recomputing a maximum-weight matching every day?
3. How should we choose which vertices to query (ask), given 12 points per day?
4. Does the theory say to spread introductions over uncertain pairs, or to commit to the most likely ones?

## 9. Timeline

- Round 1 — research note (approach, no code): **9 Oct 2026, 23:59 IST**
- Round 2 — working program + report: **12–18 Oct 2026**

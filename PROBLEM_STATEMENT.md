# Problem Statement — The Sequential Matching Problem

*A short briefing for discussing the hackathon. Organiser kit: https://github.com/RomeoJulietLove/The-Sequential-Matching-Problem*

## 1. The challenge in one paragraph

We must write a program that acts as a **matchmaker** for a population of about 200 synthetic (fake) people over 60 simulated days. Every day the program makes two decisions: **(1) which missing information to ask people for**, under a small daily budget, and **(2) which pairs of people to introduce to each other**. An introduction only counts as a success if **both** people accept it, they go on a date, and **both** say they want a second date. The goal is to maximise the number of successful pairs.

## 2. The graph view

| Concept | Graph equivalent |
|---|---|
| Person | Node (~200, arriving over days 0–20; ~12% leave later) |
| Pair that satisfies all hard rules in **both directions** | Edge |
| How likely the pair is to succeed | Edge weight (unknown — must be learned from feedback) |
| Person whose hard rules are not yet known | Node whose edges are hidden until we "ask" |
| One day's introductions | A **matching**: set of edges, no node used twice |
| A person in an active introduction | Node temporarily removed (≈8 days) |
| A pair already introduced | Edge permanently deleted (no repeats) |

The graph is **general (not bipartite)**: people may want the same gender or non-binary partners. It is **sparse**: of ~19,900 possible pairs, only ~0.5% are allowed, ~13% are unknown, ~87% are ruled out. On a typical day only ~10–20 edges exist among free people, forming several small separate components.

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

## 8. Timeline

- Round 1 — research note (approach, no code): **9 Oct 2026, 23:59 IST**
- Round 2 — working program + report: **12–18 Oct 2026**

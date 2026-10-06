# Discussion Notes — Sequential Matching Hackathon

Running log of key facts, decisions and open questions. Updated as ideas evolve.
Organiser kit: https://github.com/RomeoJulietLove/The-Sequential-Matching-Problem

---

## 1. Deadlines
- **Round 1 (research note, PDF/Markdown, via Google Form): 9 Oct 2026, 23:59 IST**
- Round 1 results: 11 Oct 2026, 22:00 IST
- Round 2 (build): 12–18 Oct 2026, 23:59 IST, via GitHub "Final submission" issue
- AI tools allowed for planning/coding **if declared**. No AI/network calls inside the graded program.

## 2. The problem in one line
Act as a matchmaker for ~200 synthetic people over 60 days: each day decide **whom to ask questions** and **whom to introduce**, so that the most pairs end up with **both wanting a second date (MSMI)**.

## 3. Key facts (verified from data / simulator code)

### Population
- Max 200 people per world. ~136 present on day 0; rest arrive days 1–20; none after day 20.
- ~12% leave somewhere between day 22 and 60.
- After an introduction a person is **busy 8 days** (longer if a date is pending) → max ~7 intros each over 60 days.

### Daily loop
LOOK → ASK (12 points/day) → LOOK again → MATCH → next day (late feedback arrives).

### Dealbreakers (11 fields, 7 rules, all checked BOTH ways = "reciprocal")
gender wanted, age min/max, zone, smoking + partner smoking, has/partner/wants children, relationship structure, schedule overlap.
- Gender, age, zone cut the most pairs.
- Kit function `eligibility(a, b)` does the full check → reuse it.

### Who can be matched
| Group | Meaning | Fresh world (day 0) |
|---|---|---|
| A complete | all 11 known → matchable | ~40% |
| B askable | some never asked, none refused | ~33% |
| C refused | refused ≥1 dealbreaker → **blocked forever** | ~26% (35% in dataset) |
- Profiles are either complete or very sparse (0–5 known); nobody has 6–10 known.
- **Asking a group-B person always succeeds** (refusals are fixed and visible upfront).
- Blocked people still count in the score denominator.

### Pairs
- Of 19,900 possible pairs, only ~0.5% allowed, ~13% unknown, ~87% ruled out.
- On a typical day only ~10–20 allowed pairs among free people; max ~9–19 intros/day.
- Allowed pairs form small separate "islands" → can solve each island separately.

### Funnel (dataset, 613 introductions)
both yes ~14% → date ~half of those → **both want 2nd date ≈ 1.5% of intros**.
Replies: 37% yes, 41% no, **22% no reply** (no reply ≠ no).

### What drives "yes" (soft fields, dataset check + simulator code)
| Field | Match vs differ yes-rate | Use? |
|---|---|---|
| relationship_goal | 59% vs 39% (also affects 2nd date) | ⭐⭐⭐ |
| conversations | 56% vs 49% | ⭐ |
| lifestyle | 54% vs 47% | ⭐ |
| relationship_pace | 53% vs 47% | ⭐ |
| emotional_availability, space_for_relationship, relocate | no effect | ❌ |
- Each person also has hidden pickiness + hidden reply rate → estimate from their history.
- Hidden "shift" scenario changes weights (lifestyle turns negative) → weights must be **learned/updated from feedback**, not hard-coded.
- conversations.jsonl / questionnaires.jsonl repeat the same fields → no new info.

### Scoring (ranking)
MSMI per 100 arrived members, averaged over 6 scenario families × 20 hidden worlds.
Baselines: greedy 0.50, no-asks 0.33, random 0.25. One invalid pair anywhere = disqualified.

## 4. Our system design (current version)
```
1. FILTER      dealbreakers both ways (reuse kit eligibility)
2. ASK         3 pts: unlock people who open most pairs; 1 pt: relationship_goal on borderline pairs
3. RECALIBRATE new/updated person → compute their allowed partners + scores
4. SCORE       soft-field matches + person history, both directions
5. THRESHOLD   required score drops with waiting time / few options / near end
6. MATCH       best non-overlapping set (best total, not best-pair-first)
7. SAFETY      re-check every pair before submitting
8. LEARN       update person profiles + score weights from feedback (stored in memory)
```

### Each day the policy outputs exactly two things
1. **asks**: which info to request (≤12 points). Empty list allowed.
2. **pairs**: allowed, non-overlapping introductions. Empty list allowed (= everyone waits a day).
- **Introductions are free** — they do NOT use the 12 question points. Only asks cost points.
- Limit on intros = availability (busy 8 days, one intro at a time per person), not budget.

### What an introduction actually is (simulator)
- NOT Tinder: no browsing/swiping. Matchmaker hands each person ONE suggested profile at a time.
- Day 0: assigned → each person independently replies yes/no within 7 days (they have not talked yet). Some never reply.
- Both yes → a date is scheduled 1–14 days later; it happens ~78% of the time.
- After the date → each says whether they want a 2nd meeting; counts only if both yes within 3 days.
- Busy the whole time (8 days, longer if a date is pending). One active introduction per person.

### Feedback has NO reason
- A reply is only yes / no / no-reply. Nobody says *why*.
- "Why" must be **inferred**: compare what this person's rejected vs accepted profiles had in common.
- Simulator "no" comes from: soft-field mismatches + hidden personal pickiness + luck. No hidden extra preferences.
- Each person gets ≤ ~7 intros → too few to learn their personal taste in detail.
  → learn **population-wide** field weights + **per-person** pickiness & reply rate.

### Profile stores (user's design, 7 Oct)
| Store | Who | Leaves when |
|---|---|---|
| **Active** | all 11 dealbreakers known, free → can be paired | introduced → Matched |
| **Pending** | some dealbreakers never asked (askable) | asked → Active |
| **Matched (cooldown)** | in an introduction (≥8 days, longer if date pending) | free again → Active |
| **Matched pairs (history)** | every pair ever introduced | never — used to block repeats |
| **Blocked** *(added)* | refused ≥1 dealbreaker | never — never matchable |
| **Retired** *(added)* | both said yes to 2nd date (paused) or left the app | never |
- Search when a person ENTERS Active (new arrival with full info, answered asks, or back from cooldown):
  1. forward: who in Active fits ALL of P's preferences
  2. reverse: of those, whose preferences P fits
- Simulator gives `available` + `introductions` each call → stores can be rebuilt every call
  (program restarts per call; memory limit 1 MiB).

## 5. Decisions so far
- Ignore group C (refused) for asking — can never be matched.
- Treat unknown soft fields as **neutral**, never as mismatch.
- Score each direction separately (A→B, B→A).
- Waiting threshold uses **each person's own waiting time** (not assumed equal) — pair uses the longer waiter (proposal).
- Threshold → zero near day 59; people with very few options are introduced without waiting.
- Design for scale: **do not rely on brute force all-pairs**. Use an index + staged bulk filters.
  Final safety check still runs full `eligibility()` on the few chosen pairs (cheap).

## 6. Open questions / hard parts
- [ ] Asker rule: exactly how to rank whom to ask.
- [ ] Scorer: how to turn soft fields + history into a number (see plan below).
- [ ] Threshold curve: how fast it drops with waiting.
- [ ] Efficient person→candidates mapping + cross-check.

## 7. Scorer build plan (step by step, start simple)
- v0: count matching soft fields (what greedy baseline does).
- v1: weighted by the yes-rate table above (goal counts most); unknown = neutral.
- v2: learn weights from our own simulator "packets" (only info visible at intro time) with separate train/tune/test seeds.
- v3: update weights + per-person pickiness/reply rate live from feedback during the episode.

## 7b. Product ideas (for report "future work", not possible in simulator)
- Let a person pick a **reason** when saying no (from soft fields: goal, pace, lifestyle, conversations…).
  Turns guessing into data. Simulator only returns yes/no/no-reply, so can't be used in this hackathon.
- Don't over-interpret individual rejections — too little data per person; prefer population-level learning.

## 8. Research leads
Dynamic matching markets / kidney exchange ("Thickness and Information in Dynamic Matching Markets"), reciprocal recommender systems, maximum weight matching, value of information / active learning, contextual bandits, Gale–Shapley (why not used).

## 9. Idea log
- Divide & conquer: block by gender → zone → age (cuts 9,180 → 3,215 pairs on day 0). Best use: deciding **whom to ask**.
- Waiting-time threshold ("aging") — lower the bar the longer someone waits.
- Recalibrator: on arrival / after an ask, recompute that person's candidates and scores.
- ~~Rejection learning per person~~ **DROPPED (user decision):** can't ask why → don't judge individuals from rejections.
- Later optimisation: keep bucket lists sorted by age + binary search for range lookups (note for Round 2).
- Staged bulk cross-check (cheapest + most-eliminating filter first):
  1. Index: (gender, zone) → people, each list **sorted by age**.
  2. New person P: look up only buckets P wants (gender × acceptable zones).
  3. Age: binary-search P's age range in the sorted list → slice, no full scan.
  4. Bulk reverse check on survivors: do THEY want P's gender? → then P's zone? → then P's age?
  5. Remaining rules (smoking, kids, structure, schedule) only on the few left.
  - Unknown fields never eliminate (stay "?"); refused field = blocked forever.
  - Elimination power in data: gender (116,788 pair-failures) > age (105,982) > zone (98,832) > rest (<22k each).

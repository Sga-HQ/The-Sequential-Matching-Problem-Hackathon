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
- **Existing entries (decided 7 Oct): "search once per person, ever" + a shared edge list**
  - Search when a person's 11 dealbreakers become fully known (new arrival with full info, or after asks).
  - Search against Active **+ Matched** (everyone with full info, busy or not), not just Active.
  - Each found pair = one **edge**, stored once for both people → existing people get the newcomer automatically.
  - Busy → edge hidden (not deleted); cooldown over → edge visible again, no re-search needed.
  - Edge deleted only when: pair introduced (history) or a person is Retired.
  - Preferences never change in the simulator → edges stay valid.
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

### Questions to ask organisers / lecturer (via Question issue or Discord)
1. ⭐ May the policy use structure learned by reading the public simulator code (which soft fields matter, drift timing), or must it learn from replies only?
2. Are the 120 hidden worlds made by the same `generate()` as public variants (only seeds secret)?
3. Memory resets per episode — is within-episode learning expected to matter, or offline-trained priors?
4. How to handle delayed/pending feedback in exploration (pending ≠ no)?
5. How is the Round 1 note judged (length, format, how much evidence)?

## 7. Scorer build plan (step by step, start simple)
- v0: count matching soft fields (what greedy baseline does).
- v1: weighted by the yes-rate table above (goal counts most); unknown = neutral.
- v2: learn weights from our own simulator "packets" (only info visible at intro time) with separate train/tune/test seeds.
- v3: update weights + per-person pickiness/reply rate live from feedback during the episode.

## 7b. Product ideas (for report "future work", not possible in simulator)
- Let a person pick a **reason** when saying no (from soft fields: goal, pace, lifestyle, conversations…).
  Turns guessing into data. Simulator only returns yes/no/no-reply, so can't be used in this hackathon.
- Don't over-interpret individual rejections — too little data per person; prefer population-level learning.

## 7c. Lecture: "Exploration, Exploitation and Online Learning" (hackathon session, 6 Oct 2026)
Core lesson: every introduction does two jobs — it is the product AND our only source of data
("selective feedback": no outcome for pairs we never introduce). Greedy can lock onto wrong beliefs forever.
How we use it:
| Lecture idea | Where in our system |
|---|---|
| Thompson sampling (Beta counts, sample, act) | Scorer: per soft-field feature keep yes/no counts → Beta; each day draw a plausible weight set, score pairs, match. Explores automatically, no dial. |
| Value of information (ask only if answer could change the decision) | Asker: ask goal on borderline pairs; ask dealbreakers of people whose unlock changes today's/near-future matching. Not "most uncertain". |
| Non-stationarity (discount old evidence, γ^age or sliding window) | Handles hidden "drift" (response conditions change mid-run) and "shift" (weights differ) scenarios. |
| Cold start (budget intros for learning) | Newcomers: uncertainty in Thompson gives them chances; never override dealbreakers. |
| Surrogate model μ + κσ (UCB) | Alternative to Thompson for scoring: mean + bonus for uncertainty. |
| Free evaluations → GA / DE | Offline only: simulator runs are cheap → tune our knobs (threshold curve, priors, γ) with DE/grid on train seeds. |
| Regret, calibration | Report: compare vs greedy; check scorer calibration on held-out seeds. |
- Round 1 must answer: **"how does our policy explore, and how would it discover a wrong belief?"** (lecture objective 5).
- Exploration is at population/feature level (consistent with dropping per-person rejection analysis).

## 7c. Lecture: "Exploration, Exploitation and Online Learning" (hackathon session, 6 Oct 2026)
Core message: every introduction does two jobs — serves people AND produces evidence.
- Explore = try uncertain options to learn; Exploit = use what looks best now. Regret = loss from not picking the best.
- Greedy (exploit only) can lock onto a wrong belief forever because we only see outcomes of pairs we introduce
  ("selective feedback"). Our kit's greedy baseline does exactly this.
- Thompson sampling: keep a belief (Beta(yes+1, no+1)) per option, draw a random plausible value, act on the draw,
  update. Uncertain options get tried naturally; no dial to tune. Best in lecture's comparison.
- Surrogate/UCB: score = prediction + κ·uncertainty. A useful model knows what it doesn't know.
- Value of information: ask only where the answer could CHANGE a decision, not where most uncertain.
- Non-stationarity: discount old evidence (weight γ^age) → handles "drift" (day ≥35) and "shift" scenarios.
- Cold start: newcomers have no history; decide if they get exploratory intros or protection.
- GA / DE: for cheap evaluations — not our case (an introduction is expensive: ≤~7 per person).
- Round 1 questions to answer in the note: which algorithm? how much quality traded for learning, who decides?
  fairness to newcomers? **how does the system notice a wrong belief and what does it do?**

### How we apply it
1. Scorer beliefs: Beta(yes+1, no+1) per (soft field × match/differ/unknown), from introduction replies
   (frequent signal; MSMI too rare to learn from). Prior = dataset yes-rate table.
2. Each day: Thompson-sample the beliefs → pair scores → matcher picks best set ("combinatorial Thompson sampling").
3. Asker = value of information: dealbreaker ask for Pending people whose unlock adds options to under-served
   Active people; 1-pt relationship_goal ask only when the answer could flip a pair above/below threshold.
4. Discount old replies (γ≈0.97/day) so weights re-learn under shift/drift.
5. Censoring: pending replies are not "no"; no-reply is not "no".
6. Wrong-belief detection: compare predicted vs actual yes-rate over a recent window; if far apart, widen
   beliefs (reset toward prior) so exploration restarts.
7. Optional per-person reply reliability Beta(replied+1, missed+1) — reliability, not "why they rejected".
Related refs from lecture: Das & Kamenica (2005) two-sided bandits & dating; Liu, Mania & Jordan (2020)
competing bandits in matching markets; Chen et al. (2013) combinatorial bandits; Joulani et al. (2013) delayed feedback.

## 7d. Questions raised in the session chat (anonymised) + our answers
- **⭐ Organiser's question (signals what they care about):** we only get feedback on people we introduce —
  how do we discover our matching assumptions are wrong *without users bearing too much experimentation cost*?
  → Explore only among near-ties (cheap: Thompson flips choices only when scores are close); use cheap asks
  before costly introductions; monitor predicted vs actual yes-rate and reset beliefs if they diverge.
- Can a system detect it is confidently wrong when its uncertainty is also wrong?
  → Not from inside. Needs an outside check: calibration of predictions vs real replies over a recent window.
- Concepts only for research proposal? → No, used in both rounds (Round 1 describes, Round 2 implements).
- Well-established industry solutions? → Contextual bandits (news recommendation, Li et al. 2010), reciprocal
  recommenders, kidney-exchange matching, Gale–Shapley-style ranking. None fits this simulator off-the-shelf.
- Are new arrivals completely unknown? → No. Some arrive with full dealbreakers, some sparse, some with refusals.
- Ask vs explore, given cost? → Asks are cheap (points), introductions are expensive → resolve with asks first.
- Should a confident model still try uncertain options? → Sometimes, when the cost is small (near-ties).
- No training data for a pattern? → Generate it with the simulator (our "packets").
- Will early good matches shrink the user base? → In simulator successful pairs pause; that IS the goal (score
  counts successful pairs per arrived member, not retention).
- Do we ever see outcomes of pairs we didn't introduce? → Never (selective feedback).
- Isn't it always the same dataset? → No: each introduction creates a new pair outcome; simulator gives unlimited new worlds.

## 8. Research leads
Dynamic matching markets / kidney exchange ("Thickness and Information in Dynamic Matching Markets"), reciprocal recommender systems, maximum weight matching, value of information / active learning, contextual bandits, Gale–Shapley (why not used).
From lecture refs: Russo et al. 2018 (Thompson tutorial), Das & Kamenica 2005 (two-sided bandits & dating market), Liu, Mania & Jordan 2020 (competing bandits in matching markets), Joulani et al. 2013 (online learning under delayed feedback), Lakkaraju et al. 2017 (selective labels), Howard 1966 (value of information), Garivier & Moulines 2011 (discounted UCB).

## 9. Idea log
- **1/0 encoding = bitsets (user idea, 7 Oct) — tested, works.**
  - For each value keep a "people bitset" (bit i = person i): has_gender[g], in_zone[z], age_is[a],
    wants_gender[g], accepts_zone[z], agemin_ok[a], agemax_ok[a]. Unknown → bit set to 1 (passes, stays "?").
  - Candidates of P = (forward: people P wants) AND (reverse: people who want P) → bitwise AND, one CPU op per rule.
  - Test world 101, day 0: 2,996 pairs survive gender+zone+age both ways — **identical to official checker**,
    0.0007 s vs 0.0425 s (~60× faster). Built once per person (on arrival / after ask) → cheap.
  - Still run full `eligibility()` on chosen pairs as final safety check.
  - Same idea for soft fields: per-pair vector match=1 / differ=0 (+ unknown flag) = scorer input.
- Divide & conquer: block by gender → zone → age (cuts 9,180 → 2,996 pairs on day 0 (corrected; earlier 3,215 had an age-check bug)). Best use: deciding **whom to ask**.
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

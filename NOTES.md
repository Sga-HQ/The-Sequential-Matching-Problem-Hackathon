# Discussion Notes — Sequential Matching Hackathon

Running log of key facts, decisions and open questions. Updated as ideas evolve.
Organiser kit: https://github.com/RomeoJulietLove/The-Sequential-Matching-Problem

---

## 1. Deadlines
- **Round 1 (research note, PDF/Markdown, via Google Form): 9 Oct 2026, 23:59 IST**
- Round 1 results: 11 Oct 2026, 22:00 IST
- Round 2 (build): 12–18 Oct 2026, 23:59 IST, via GitHub "Final submission" issue
- AI tools allowed for planning/coding **if declared**. No AI/network calls inside the graded program.
  Kit §14: "Document external models and coding tools" → the note/report must state AI (Claude) use.
  User (7 Oct): AI was used **for coding and testing ideas, not planning**. Disclosure wording must match what AI did.
- **Team: solo (decided 7 Oct).** Friend gave permission to use his research as long as it is not published
  before his; no credit needed (his approval). In the note, cite the original papers for shared concepts
  (Akbarpour 2020, b-matching, power analysis), written in our own words.
- **Aim of the hackathon (kit §1, §10, §15):** a sound, valid, reusable decision policy plus an honest report.
  Ranked against OTHER TEAMS (not vs baseline) on MSMI over 6 scenarios × 20 private seeds; Round 1 is the research note.
- **Round 1 workflow:** user writes the logic in plain words → Claude writes math + why + source + evidence
  (ROUND1_LOGIC_MATH.md). Block 1 (daily pairing) done as a worked example.

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
- **Testing rule (user, 7 Oct):** test at the real size (200-person worlds). Use 100k scale tests only when a
  decision specifically depends on scale; the 100k filtering benchmark is done and not repeated.
- Ignore group C (refused) for asking — can never be matched.
- Treat unknown soft fields as **neutral**, never as mismatch.
- Score each direction separately (A→B, B→A).
- Waiting threshold uses **each person's own waiting time** (not assumed equal) — pair uses the longer waiter (proposal).
- Threshold → zero near day 59; people with very few options are introduced without waiting.
- Design for scale: **do not rely on brute force all-pairs**. Use an index + staged bulk filters.
  Final safety check still runs full `eligibility()` on the few chosen pairs (cheap).

### Table design (user idea, 7 Oct) — split "who I am" from "who I want"
| Table | Columns | Used for |
|---|---|---|
| **profile** (who I am) | age, gender, zone, smoking, has_children | other people's preferences are checked against this |
| **preferences** (who I want) | age_min/max, who_to_meet, acceptable_zones, partner_smoking, partner_children | checked against other people's profile |
| **mutual** (must agree/overlap) | relationship_structure, wants_children, schedule | compared both ways |
| **soft** | goal, pace, lifestyle, conversations (+3 no-effect fields) | scorer only |
| **status** | per-field observed / not_asked / declined + day observed; available; store (Active/Pending/...) | asker, safety |
| **history** | introductions + replies | no repeats, scorer counts |
- Forward search = MY preferences × THEIR profile; reverse = THEIR preferences × MY profile.
- Matches problem statement §15: "keep normalisation, modelling and allocation separate".

### Daily pair selection for existing people (researched 7 Oct)
1. Edges = allowed pairs among free people (from the edge list / bitsets).
2. Weight per edge = Thompson-sampled P(A yes)·P(B yes) × urgency boost (waiting time, few options, near end).
3. **Maximum-weight matching** over the whole graph (Edmonds blossom — graph is NOT bipartite because of
   same-gender / non-binary preferences). networkx `max_weight_matching` (BSD, pure Python) or exact search per island.
4. Wait vs match: Akbarpour–Li–Oveis Gharan (JPE 2020): waiting to thicken the market helps a lot ONLY if you
   know who is about to leave ("critical"); otherwise matching greedily-ish is near optimal.
   → match nearly everyone each day; only hold back people with many options when a clearly better partner is likely.
5. RECON (Pizzato et al.) combines both directions with the **harmonic mean** — penalises one-sided pairs.

### Scorer vs Thompson (clarified)
- Scorer = the component that gives each allowed pair a number (how likely both say yes).
- Thompson sampling = HOW the scorer gets its numbers: random draw from each yes/no count instead of the plain average.
- Mutual fields (structure, wants_children, schedule) are HARD rules → filter only, zero weight in scorer.
  Soft fields only change likelihood → scorer only, never block.

### System overlay
```
TABLES (rebuilt from simulator state each call; learned counts kept in `memory`)
 profile | preferences | mutual | soft | status | history | edges | scorer_counts

DAILY PIPELINE
 0 LOAD      state + memory → fill tables, set each person's store
 1 INDEX     new/updated full-info people → bitsets → new edges (both directions)
 2 ASK       Pending people ranked by value of information → asks (≤12 pts)
 3 RE-INDEX  answered people → Active (or Blocked) → new edges
 4 SCORE     edges among free people → Thompson draw from scorer_counts → weight
 5 URGENCY   weight × waiting-time / few-options / near-end boost
 6 MATCH     max-weight matching (blossom) → pairs
 7 SAFETY    official eligibility() on every chosen pair
 8 SAVE      history + updated counts (+discount) → memory
 FEEDBACK    replies arrive later → update scorer_counts; wrong-belief check

PERSON FLOW
 arrive → Blocked (refused) | Pending (missing) | Active (complete)
 Pending --ask--> Active ;  Active --introduced--> Matched (busy)
 Matched --free again--> Active ;  Matched --both want 2nd date / left--> Retired
```

### Algorithm stack (current)
| Part | Algorithm |
|---|---|
| Filter | Bitset index + per-rule 1/0 row (hybrid), reciprocal |
| Asker | Value-of-information ranking under 12-pt budget (greedy knapsack) |
| Scorer | Beta–Bernoulli Thompson sampling with discounting ("combinatorial Thompson sampling" with matcher) |
| Timing | Aging/urgency boost; mostly match daily (Akbarpour et al. 2020) |
| Matcher | Maximum-weight matching, general graph, Edmonds' blossom |
| Safety | Official `eligibility()` on chosen pairs |

### People to consult (7 Oct)
- **DSA professor (graphs):** briefing file = `PROBLEM_STATEMENT.md`. Ask about matching on dynamic graphs,
  blossom vs simpler exact search on tiny components, online matching / when to wait, incremental edge updates,
  weighting both directions, bitset indexing.
- **Professor: research-level questions (user wants theory, not code tips).** Four closely matching models:
  1. Stochastic matching with patience: "Approximating Matches Made in Heaven" (Chen, Immorlica, Karlin, Mahdian,
     Rudra, ICALP 2009). Motivated by dating; edges exist with prob p; each person probed ≤ t times; greedy ≥ 1/4 OPT.
  2. Stochastic matching with few queries: "Ignorance Is Almost Bliss" (Blum, Dickerson et al., Oper. Res.);
     O(1) queries per vertex ≈ full optimum. Our asks = edge-revealing queries.
  3. Fully online matching: "How to Match when All Vertices Arrive Online" (Huang et al., STOC 2018); vertices
     arrive and have deadlines; Ranking is 0.5211-competitive on general graphs.
  4. Online matching with stochastic rewards (Mehta & Panigrahi, FOCS 2012); a match pays off with probability p.
  Key question for her: which model fits best, and which algorithm or proof idea should we use?
- **Friend (friend-suggestion system, ~6 features, own maths):** ask about his features, scoring formula, how he
  combines two directions, missing data, cold start, validation. Caution: friend suggestion = link prediction on a
  social graph (mutual friends); our people have no social graph → feature-similarity parts transfer, network parts may not.
  Update 7 Oct: user is solo; friend approved use without credit (do not publish his work before him).

### Findings 7 Oct (details in RESEARCH.md)
- 100k filtering: all methods identical (7,970,144 pairs). Columnar numpy 0.21 ms/arrival, 6.1 s all pairs;
  user's row idea 21.7 ms, 791 s. → adopt columnar.
- "Which rule failed" is NOT needed for known failures (one 0 = pair dead). Ask bundle costs 3 for ALL hard
  fields anyway, so per-field detail only helps estimate whether a Pending person will be compatible.
- Blocked (refused) people: never matchable, never ask, still in score denominator. Nothing to do. (User agrees.)
- Soft weights by logistic regression on packets: 4 soft fields best; adding mutual fields hurts held-out
  log-loss → mutual stays filter-only. Shift scenario flips weights → learn online. AUC ~0.55 → coverage matters more.
- Combining both directions: all rules identical (symmetric features). Use product.
- Asker prediction (donor imputation) unlocks 1.32 partners per ask vs 0.62 random (hindsight 2.90).
- Friend's GitHub (LeafyChan): no public recommendation/matching repo.

### Friend's math appendix (7 Oct) — adopted pieces (details RESEARCH.md §3.5)
- Funnel elasticity: raise the cheapest stage (number of valid introductions) since scorer AUC is only ~0.55.
- Floor ≥ 1 from b-matching: boost never-introduced people (coverage = tie-breaker #1).
- Power analysis: comparing policies on MSMI needs ~79 episodes per policy for 1.0→1.5 successes/episode;
  iterate on mutual acceptances (~16 episodes), confirm on MSMI.
- EPV ≥ 10: online learning within one episode supports only a few parameters → offline-fitted prior, gentle updates.
- Binding-constraints table format for the Round 1 note.
- Not adopted: uplift (no one meets without intro here), IDF (fixed categories), submodular slates (one intro at a time).

### Prototype ablation (7 Oct, 240 episodes/policy, SKELETON.md §4)
- MSMI unchanged within noise (0.41 baseline). Mutual acceptances +5% from VOI asker (significant).
  Coverage +0.5 pt but already near ceiling (0.41 dev / 0.16 sparse).
- Next levers: unused ask budget (199/720 pts), goal asks for Active people, score full funnel, reply reliability.

### Asker ceiling (7 Oct): even oracle/unlimited asking adds ≤ ~1% → asker is NOT a lever. Earlier +5% did not replicate.

### Theoretical ceilings (7 Oct, SKELETON.md §4)
- Perfect soft scorer +8%, + hidden traits +9%, every allowed pair +40% (unreachable).
- Baseline already uses 75% of allowed pairs; unused: 53% paused after success, 27% left app, 20% capacity.
- Realistic headroom +5–15%. FOCUS: (1) soft-field asks with spare budget, (2) best partners for busy people,
  (3) introduce early. Not: asker order, heavy exploration. Validity first (one invalid pair = disqualified).

### All three kit baselines (7 Oct, 240 episodes each, same seeds as ablation)
- MSMI: greedy 0.410 · random 0.352 (−14%) · no-asks 0.117 (−72%). Our prototype 0.400 (no difference from greedy).
- Mutual acceptances: random = our prototype (+4% vs greedy). Asking is the big lever; pair choice is small.

### Is the ceiling a wall? (7 Oct)
- In the PUBLIC simulator it is arithmetic, not opinion: the policy only picks which allowed pairs, when, and asks.
  Dealbreakers, hidden traits and luck are fixed. E[wins] ≤ Σ over allowed pairs of P(win) = 1.268 vs baseline 0.906
  (+40%, loose: ignores pausing/busy). No idea can beat +40% there; realistic +5–15% is explained; the 15–40% band
  is where to hunt.
- User's point: competitors are strong (professionals, IIT students) → baseline +5% is not enough; validity is table
  stakes, not an edge. Keep hunting levers. Untested from code: front-load before day 35 (drift), prior strength
  in shift, reply reliability (MSMI needs each person to answer twice → r² per person).
- Hidden worlds: families are public, seeds are private (evaluate.py uses kit.generate). Still stress-test
  beyond them → STRESS_TESTS.md (incl. user's partial-profile idea, 10 s limit at larger pools).

### Missing-dealbreaker groups (7 Oct, development, 10 worlds, arrived by day 59)
| Missing dealbreakers | People/world | Has ≥1 allowed partner once answered | Introduced by baseline |
|---|---|---|---|
| 0 (complete) | 69.9 | 58% | 57% |
| 1 or 2 | 0 | – | – |
| 3–6 | 0.1 | – | – |
| 7–9 | 21.2 | 63% | 60% |
| 10–11 | 44.2 | 61% | 59% |
| Refused (blocked) | 64.6 | never | never |
- Nobody is "almost complete": askable people miss 7–11 answers, and the 3-point bundle answers all at once.
- Once answered they are as matchable as complete people, and the baseline already introduces almost everyone
  who has any partner (57% of 58%) → coverage is at its ceiling.

### Decisions 8 Oct (tables, filter, arrivals, asker, score band)
- Tables = user's 6 (TABLES.md) + **Pending** as a named list (not ready, not blocked, not busy/retired) → asker input only.
  Filter runs on ready people only.
- Allowed-pairs cache: 200 people → recompute daily (≤26 ms). 100k (from earlier benchmark): recompute all pairs
  ≈ 6 s/day columnar vs ≈ 0.2 ms per new person incremental → cache matters for a real app. But the hackathon carries
  ≤1 MiB memory between calls and 100k gives ~8M allowed pairs (~64 MB) → cannot carry; real app keeps it in a database.
- Simultaneous arrivals: the app is day-based; everyone arriving on day d appears together and is checked against
  everyone (new×new included) because we recompute daily. Incremental design must do new×(old ∪ new).
- Asker (user's sandbox idea = imputation asker already built, 1.32 vs 0.62 partners/ask). Cheaper exact half:
  age, gender, zone are always visible → count ready people whose preferences accept the pending person (no guessing).
  Asker order caps at ~1% → keep cheap.
- Score band idea: upper cut has no reason (higher = better). Lower floor = user's earlier waiting-time threshold;
  scorer is weak (AUC 0.55) and partners are scarce → expect ≤0 gain; testable.

### Decisions 8 Oct (part 2)
- Report filter scalability with the 100k numbers; say it is meaningless at 200 but cheap, so used from day one.
  Scope honestly: 100k test = filter only.
- Real-app allowed-pairs table with scores, ranked per person; simultaneous-arrival fix (insert-then-check, pair key,
  queue/transaction + nightly sweep) → TABLES.md.
- Asker sandbox: answers are multi-valued (age ranges, zone lists, gender lists) → enumerating all answer combinations
  explodes; sampling K answers from similar complete people covers realistic combinations. No precomputed
  "hypothesis pairs" (the real answer arrives the same day and the filter takes ms). Pending×pending only counts
  if both get asked → small weight. Asker order ≤1% → keep cheap.
- Visible for pending people = who they ARE (age, gender, zone), not what they WANT → we can check only the half
  "does this ready person accept them".
- User's "upper cutoff" = fairness/averaging: already done by max-total matching (A-B-C-D) + coverage boost. Formal
  version if wanted: maximise Σ log(score) (proportional fairness) → testable.
- User's floor idea = multiplier boost (already: ×1.5 never introduced, ×(1+0.5/options)); a boost that grows with
  days waited is not yet built.
- Leaving: random at creation (12%, days 22–59), unrelated to policy → cannot reduce, only introduce early.
- Age fixed in episode (no DOB); real app: store DOB.
- Data ageing lives in the scorer (old replies × 0.98/day; drift scenario from day 35). Profile answers never go stale
  in the simulator (preferences fixed); in a real app, re-confirm old answers.

### Decisions 8 Oct (part 3)
- Asker priority (user): pending people who could pair with READY people are asked first; pending people whose only
  possible partners are other pending people are asked only when no such pairs exist.
- Arrival queue handles each newcomer within seconds; the nightly sweep is only a backup (joining today does not
  mean waiting until tomorrow). In the hackathon everything happens once per day anyway.
- Open design parts (user): 1 scorer · 2 asker · 3 introducer (which allowed pairs to introduce; fairness
  research running) · 4 post-introduction data → TABLES.md "What comes back after an introduction".
- New lever from feedback: per-person reply reliability (24% of replies missing; 29% of people miss ≥ half).
- NOTE_CHECKLIST.md = running list of things that must appear in the final document.

### Decision 8 Oct: fairness / upper cutoff (RESEARCH.md §1)
- Objective stays Σ score with maxcardinality (most pairs first). No upper cutoff: real systems use floors/quotas for the
  disadvantaged, never caps on the best. Averaging in real dating apps exists because popular users get flooded;
  the simulator has no flooding. The "taken" problem here is over time → urgency/scarcity boosts. Optional tests:
  √q, log q + 10, coverage-first.

### Decisions 8 Oct (part 4): scorer
- Target = whole journey (user). Journey score ∝ P(A yes)·P(B yes)·rA²·rB² (SCORER.md v2, measured).
- Ageing γ = 1 in the simulator (proof in SCORER.md); Muth formula for the real app.
- Soft-field asks with spare budget, no enumeration: value of each single question alone (linear cost); ask the goal of
  people with unknown goal who have ≥2 allowed options (a choice exists); skip 0–1 options. Greedy one-at-a-time
  is near-optimal for diminishing-returns information (adaptive submodularity, Golovin & Krause 2011, from memory).
  72% unused = only 199 of 720 points spent per episode (no pending people left after ~day 17).
- Evolution "knows" only through a fitness function we write: run the policy with the given knobs on training
  worlds → mean expected wins. DE proposes knob sets, keeps the better ones, mixes them, repeats; checked on held-out worlds.

### Findings 8 Oct (scorer data, all 6 scenarios; SCORER.md v3)
- Busy timings (8 days; until date + 6) come from the organisers' simulator code (kit.py); their written spec only says
  "occupied through the response/date window" and "repeated pair not permitted within an episode".
- 3 extra soft fields have no effect. Shift: pace strongest, goal weak, lifestyle reversed.
- 61–64% of soft fields unknown at decision time (cold start 81–83%). ~25 replies in the first 10 days → slow learning.
- Median 2 introductions per person → little per-person data.
- Best possible AUC: fields known 0.64; + pickiness 0.71; + shared luck 0.74. Ours ~0.55 → the gap is mostly unknown
  fields → soft-field asks are the scorer's biggest lever. ASKER.md collects the asker rules.
- Evolution offline cost: one fitness evaluation ≈ 20 worlds × ~5 s = 100 s; 20 candidates × 30 rounds ≈ 17 CPU-hours
  (≈ 4 h on 4 cores); cut with 10 worlds, fewer rounds, faster code. Possible and free, but not before the Round 1 deadline.

### Scorer v2 test (8 Oct, 60 episodes/policy, seeds 7100–7109; SCORER.md end)
- Expected wins vs kit: old prototype +2.3%, v2 +2.4%, v2 + soft asks +2.7% (each ≈ 4–5 SE). MSMI at 10 seeds = noise.
- Soft asks spent only +24 points (rule "≥2 options" rarely true); unknown fields 71% → 59%; AUC 0.540 → 0.553.
- Shift weakest for v2 (prior wrong for lifestyle). Tuning list → TUNING.md.
- User: why does someone who said "no" stay busy 8 days? Simulator rule (busy = day+8 for both at the introduction,
  regardless of the answer); the policy cannot release them. Real-app point for the note: free people as soon as a
  "no" arrives.

### Three external suggestions checked against the rules (8 Oct)
- Smart defaults (guess blank soft fields from other answers): writing a guess in = NOT allowed (INTEGRATION.md: "never
  fabricate a default preference"; DATA_CONTRACT: declined "must not be inferred or bypassed"). Also useless: kit.generate
  draws every soft field independently and uniformly → other answers carry zero information.
- Dynamic prompts = 1-point soft-field asks → allowed (resolve_asks) and already planned (ASKER.md rule 4).
- Context switch (detect shift): allowed if detection uses only observed replies and the candidate weight sets are
  declared training assets fitted on public variants (PROBLEM_STATEMENT §205). Not allowed: seeds, hidden objects.
  Method: soft Bayesian blend of 2 weight sets by likelihood of observed replies (not a hard switch). Detection speed
  to be measured.
- Peer personas: allowed with observed age/zone/gender (never infer who they want to meet from gender). Useless in the
  simulator: pickiness and reply habit are drawn independently of the profile → persona average = global average
  (already our prior). Real-app idea, with a stereotype/fairness caution.

### Tuning round 1 (8 Oct; ROUND1_NOTE.md §9.3)
- Soft asks for 1+ options: AUC +0.024 ± 0.006, blanks 57% → 41%, wins unchanged → adopted (default now 1).
- Normaliser 12 instead of 40: −0.0118 ± 0.0027 expected wins → rejected. Pickiness k = 3: no gain. Pickiness off: AUC −0.016.
- v2 + soft asks vs kit: +6.3% (7200s), +2.7% (7100s) → report ≈ +4.5% with the spread.
- Round 1 note: first full draft in ROUND1_NOTE.md (~5,500 words).

### External review + experiments (8 Oct evening; ROUND1_NOTE.md §9.4–9.8)
- Block 7300: current best vs kit +0.0006 ± 0.0047 (no gain). Pooled over 3 blocks +0.0099 ± 0.0018 (≈ +2.6%),
  heterogeneous (Q = 7.9, df 2).
- Coverage boost costs ≈ 0.004 expected wins (1.5 SE); opportunity cost λ = 0.5 best (+0.0050 ± 0.0027 vs best) but
  ≈ removing the boost → H6 (option value) open.
- Margin asker: same wins, 18% fewer ask points. Simple fixed scorecard ≥ online learner; posterior mean +0.38 ± 0.14
  mutual vs Thompson → Round 2 default: simple scorecard + margin asking, no coverage boost.
- Checks: 5-point Gauss–Hermite error ≤ 4e-7. Day 35–49 "dip" did not replicate on 60 fresh worlds (chance).
- Same seed → development/delayed/drift share world and luck draws (rand_for keyed on seed, pair, day).
- Note revised with evidence labels, lexicographic objective, allowed-pair definition, AUC definition, untouched
  confirmation block 50000–50019, AI disclosure; PDF rendered (ROUND1_NOTE.pdf).

### Experiment 4 + final note revision (8 Oct night; ROUND1_NOTE.md §0, §9.6)
- New block 7400–7419 (120 eps): candidate R1 (frozen scorecard, broad soft asks, no coverage boost) vs kit +0.0205 ±
  0.0051 cluster-robust expected wins; realised MSMI −0.096 ± 0.050 (kit realised 0.46 vs expected 0.37) → confirmation needed.
- Online learning changed 8.6% (population) / 14.9% (personal) of daily matchings, no gain (F2 −0.0023 ± 0.0014).
- Broad asks beat margin asks (+0.0043 ± 0.0019); margin asker lost in cold start; VOI asker +0.0013 vs margin (not vs broad).
- Degree boost: no measured effect. Delayed 30-day factor = 5368/5488 = 0.9781, exact constant.
- Note reorganised around the evidence-supported candidate; H7 closed-loop feedback; safer AI disclosure.

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

## 7e. Lecture 2 (7 Oct): "Building robust ML systems from messy data" (car-park demand forecasting case)
Case: weekly occupancy forecast for 18 car parks / 3 terminals at an airport, to support dynamic pricing.
Pipeline: data provenance → objective → modelling (configurable pipeline, hyperparameter search) → evaluation
(actual vs residual, failure analysis, revenue simulation).
Key result: XGBoost had the lowest error (MAE), but on the business metric (simulated revenue shortfall against
perfect information) the naive "same as last week" won (£1.29M vs £1.56M; 8-week planning baseline £2.08M).
Conclusion: use the model *alongside* handcrafted rules (hybrid).

Lessons → what changes for us:
| Lecture idea | Our version | Status |
|---|---|---|
| Perfect-forecast benchmark (theoretical ceiling) | Perfect-information ceiling (theory_ceilings.py); report "% of achievable gap closed" | ceiling done; add metric |
| Judge on the business metric, not model accuracy | Choose pieces by MSMI / expected wins in simulation, not scorer AUC or log-loss | adopt |
| Simple baselines can beat ML | Random pairs = our prototype on mutual acceptances; greedy = prototype on MSMI → say so openly | adopt (honest report) |
| Use only information available at prediction time; filters learned on training data only | Policy reads only the observation (no truth, no seed); tune on training seeds only | adopt + audit test |
| Grouped hold-out (split by quarter/terminal/car park) | Split by **seed** (world): tuning seeds ≠ report seeds; report per scenario | adopt |
| Failure categories: accurate / under / over / extreme / no output | Funnel failure table per scenario: success · one said no · no reply · date did not happen · second answer late/no · person left · never introduced | to build |
| Data provenance: original → derived → combined → external | Profile + feedback (original); degree, waiting days, reply reliability (derived); pair match/differ features (combined); no external data | for note |
| Configurable pipeline + automated search | cfg knobs (urgency 1.5/0.5, prior strength 40, γ 0.98, ask mix) tuned by evolutionary search offline | to build |
| Revenue simulation states its assumptions ("illustrative, not measured impact") | State simulator caveats (kit: simulator performance ≠ relationship prediction) | for note |
| Hybrid: model alongside rules | Kit greedy kept as fallback (time guard, errors) | to build |

Our own retrospective echo: the asker's +5% did not replicate (like a low-MAE model that loses on revenue).

Lecturer's public repo, code read (keith-17/data-projects @ 8221616): the car-park project notebook uses
`GroupShuffleSplit` by (quarter, terminal, car park), GridSearchCV, toggles (`naive_split_bool`, `use_weekly`), a CSV
checkpoint cache, versioned Excel report export. Its feature list includes same-week `total_revenue`/`bookings_count`
(computed from the same bookings as the target) → likely why MAE looked very low while "same as last week" won on
revenue (our inference). numerai notebooks: `GroupKFold` by era. research_center_assignment: experiments dict
(named configs → same evaluation → comparison table), FastAPI + Docker + regression tests with mocks.
No evolutionary/GA code in the repo; the physics project (wavetime) is unrelated except numba speed-ups.

Organiser Q&A (7 Oct, anonymised):
- networkx may be added if pinned, licensed (BSD-3) and included in the Docker image.
- You may challenge the problem framing: say what the statement misses, why it matters, how addressing it improves
  sequential matching, and show it with experiments; still answer the core challenge.
- What judges want (user's conversation with organisers): which existing solutions we use and why, how well we
  handle delayed responses, retrospection and introspection (what went wrong, what we learnt). Aim for ≥10 pages.
- User: we must try evolutionary methods (lecture 1 also: free simulator evaluations → GA/DE offline).
- Chat question "a model per terminal = divide and conquer, better than one model?" → for us: matching splits
  exactly by connected components (same answer, faster); for learning, pooled + per-group adjustment beats
  separate small models when data is scarce.

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
  - User's original form: for new person X, compute a 1/0 per dealbreaker for every other person (all 1 = match).
    Same result as bitsets; bitsets compute the whole column at once. Keep the per-dealbreaker 1/0 vector
    for "?"/near-miss pairs — it tells WHICH rule fails or is unknown (useful for the asker and explanations).
  - **Benchmark (7 Oct, all 11 dealbreakers, experiments/bench_filtering.py) — all methods give IDENTICAL pairs:**
    | pool size | complete people | official | user 1/0 row | user row + early exit | bitsets |
    |---|---|---|---|---|---|
    | 200 | 81 | 0.0109s | 0.0044s | **0.0006s** | 0.0009s |
    | 1,000 | 356 | 0.224s | 0.096s | 0.014s | **0.007s** |
    | 3,000 | 1,026 | – | – | 0.103s | **0.046s** |
    | 10,000 | 3,464 | – | – | 1.63s | **0.71s** |
    - Correction: earlier "60× faster" compared against the slow official checker; vs the user's idea with
      early exit, bitsets are ~2× faster at scale and about equal at our size (200).
    - **Decision: hybrid.** Bitsets answer "who passes everything" (scales best); user's per-dealbreaker 1/0 row
      answers "which rule fails / is unknown" for near-miss and "?" pairs (feeds the asker + explanations).
  - Industry: bitmap indexes / roaring bitmaps (Elasticsearch, Spark) do exactly this boolean filtering.
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

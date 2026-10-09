# Asker rules collected so far (user asked to keep these for the asker part)

1. **Never ask** blocked people (a refusal is permanent) or busy/retired people (the kit forbids asking unavailable people).
2. **Priority 1, dealbreakers (3 points):** pending people who could pair with **ready** people (user's rule). Cheap exact check: age, gender and zone are always visible, so count the ready people whose preferences accept this person. Optional extra: guess the missing answers by copying from similar complete people (6 samples).
3. **Pending people whose only possible partners are other pending people** are asked only when no priority-1 person is left (user's rule).
4. **Priority 2, soft fields (1 point each) with the leftover budget:** 72% of the budget is unused (199 of 720 points per episode).
   - Ask a person's **goal** first (strongest clue in 5 of 6 scenarios); then pace; then lifestyle.
   - Only ask people with **≥ 2 allowed partners** (a choice exists). With 0–1 options the answer cannot change the decision.
   - Never ask the 3 no-effect fields (emotional availability, space for relationship, relocate).
   - Bonus: every soft answer also speeds up learning (SCORER.md v3: learning is slow, and 61–83% of fields are unknown).
5. **No exponential blow-up:** judge each question on its own ("could this one answer change today's choice?"). Never enumerate combinations of answers. Greedy one-question-at-a-time is near-optimal when answers have diminishing returns (adaptive submodularity, Golovin & Krause 2011, cited from memory).
6. Order of dealbreaker asks matters ≤ 1% (oracle test), so keep it cheap.
7. **Evolution's role:** tune the asker's *rule numbers* offline (e.g. the minimum options needed to ask a soft field, field order, how much budget to keep for soft fields), not individual answers.

## Idea (9 Oct): value-driven hard asks — "guess the dealbreakers to decide whom to ask"
**Idea (user).** For each waiting person, imagine their possible dealbreaker answers. See which ready people they could then be matched with, value that with the scorer, and spend the 3-credit bundle on whoever would improve the day's matching most. Spend leftover credits on soft questions.
**Rule kept:** guesses only choose *whom to ask*. They never allow an introduction; only real answers plus the official `eligibility()` do.
**Facts from the kit code:**
- Only two question types exist: `constraints` (the whole dealbreaker bundle, 3 credits) or one soft field (1 credit). A single dealbreaker field cannot be bought for 1–2 credits (`kit.py` `resolve_asks`; `POLICY_INTERFACE.md`).
- "Two credits left → soft questions" already happens: the asker does at most 12 // 3 = 4 bundles a day, then fills the rest with soft questions.
- No need to list profile combinations (millions in full). The generator draws each dealbreaker field independently, apart from age and zone, so P(A becomes allowed with B) could be computed field by field. That independence must first be confirmed in the public training data; estimates must come from that data, never from generator seeds.
**Ceiling already measured (HEADROOM.md, stage A).** O2h gives every waiting person's dealbreaker answers free on day one, keeping all 12 credits for soft questions. No hard-ask strategy can beat it. Result: +0.0012 ± 0.0034 per 100 vs the candidate, about +0.3% (≤ about 2% at the top of the interval). Reason: the market is thin, so a person unlocked a few days later usually meets the same partner anyway.
**Decision:** not built now. If built later, it is a bounded test, kept only if it gains ≥ 1% on two seed blocks.

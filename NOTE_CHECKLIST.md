# Must appear in the final Round 1 note (running list)

Things the user asked to make sure are written into the final document.

- [ ] **Scalability:** the filter tested at 100,000 people: 0.21 ms per new person vs 21.7 ms pair-by-pair; 6.1 s vs 791 s for all pairs; identical results. Meaningless at 200 people, but cheap, so used from day one.
- [ ] **Real growth is gradual:** a real app never receives 100k people at once; arrivals trickle in, so the per-new-person cost (0.21 ms) is the number that matters.
- [ ] **Scope of the 100k test:** filter only. Exact matching at that size would be done within separate groups or with a greedy approximation.
- [ ] **Simultaneous arrivals:** insert-then-check, each pair stored once by (smaller ID, larger ID), one arrival queue, nightly full re-check as a backup.
- [ ] **Age / date of birth:** age is fixed in the 60-day simulator; a real app must store the date of birth and recompute age daily, because people can cross an age-range boundary.
- [ ] **Leaving is random in the simulator** (12%, days 22–59), not linked to anything visible; real apps' churn depends on getting matches.
- [ ] **AI use:** an AI assistant was used for coding and testing ideas (match the wording to what was actually done).
- [ ] **Delayed feedback:** waiting ≠ no; replies arrive up to 7 days later, second-date answers up to 26 days later.
- [ ] **Data ageing:** old replies × 0.98 per day (drift scenario).
- [ ] **Honest results:** random pairs = our prototype on first "yes"; asker order matters ≤1%; ceiling +40% (loose), realistic +5–15%.
- [ ] **Arrival queue (user's decision):** every new person enters one first-in-first-out queue. Each is processed within seconds (added to the tables, then checked against everyone, including earlier arrivals still in the batch), so two people joining at the same moment are never lost. Nightly full re-check as a backup.
- [ ] **Edge cases** (EDGE_CASES.md): time, competition, data and validity, each with its handling and status.
- [ ] **"We questioned our own idea":** upper score cutoff → researched → not used, and why (no flooding of popular users in the simulator; real systems use floors, not ceilings).
- [ ] **Framing point (organisers welcome these):** in the simulator, a person who says "no" on day 1 is still busy for 8 days (busy is set at the introduction for both, whatever the answer). A real app should free them as soon as the "no" arrives; that would add introductions without any cost.
- [ ] **Scorer v2 results** (+2.7% expected wins over the kit, with honest noise discussion) and the tuning list.

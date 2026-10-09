# Round 2 headroom study

**Question.** Where can more wins still come from? Each oracle arm is allowed to see one kind of hidden information. The gap between an arm and our candidate (R1) is the most that fixing that one weakness could give, assuming the rest of the policy stays the same.

**Rules of the study.**
- The arms use hidden values **only to measure**. None of them is a policy we could submit.
- New development seeds: 7500–7519, 6 scenario families, 120 paired episodes per arm. The confirmation seeds (50000+) are untouched.
- Metric: expected wins per 100 arrived members. This is the exact success chance, summed over introductions, and has the same expectation as MSMI (note §1.4).
- ± is one cluster-robust standard error over the 20 seeds.

Code: `experiments/headroom.py` and `experiments/headroom_summary.py`. Raw data: `experiments/results/headroom_A_*.jsonl`. Full table: `experiments/results/headroom_A_summary.txt`.

## Stage A: same-day oracles (done, 960 episodes)

| Arm | What it may see | Expected wins /100 | vs kit greedy | vs R1 |
|---|---|---|---|---|
| K | kit greedy baseline | 0.3520 | – | −0.0149 ± 0.0040 |
| **R1** | **our candidate** | **0.3669** | **+0.0149 ± 0.0040 (+4.2%)** | – |
| O1 | true success chances (R1's questions) | 0.3690 | +4.8% | +0.0021 ± 0.0027 |
| O1n | as O1, without "most pairs first" | 0.3704 | +5.2% | +0.0035 ± 0.0024 |
| O2h | every askable dealbreaker answer free | 0.3681 | +4.6% | +0.0012 ± 0.0034 |
| O2hs | every askable answer free, hard and soft (our scorer) | 0.3692 | +4.9% | +0.0023 ± 0.0039 |
| O12 | everything free + true chances | 0.3711 | +5.4% | +0.0042 ± 0.0041 |
| O12x | O12 + who leaves within 8 days | 0.3716 | +5.6% | +0.0047 ± 0.0040 |

**What it means.**
1. **The candidate replicates on fresh seeds:** +4.2% over the kit, about 3.7 SE (block 7400 gave +5.5%).
2. **Same-day decisions are nearly exhausted.** Even with every answer free and the true success chance of every pair, a same-day matcher gains only about **+1.2% of the kit's score beyond R1** (+0.0042 ± 0.0041). Each separate lever is worth under 1%:
   - true scores: +0.0021 ± 0.0027;
   - free dealbreaker answers: +0.0012 ± 0.0034;
   - free soft answers on top: +0.0011 ± 0.0023;
   - knowing departures: +0.0005 ± 0.0002. On a full test world, only 2 days had any allowed pair involving someone about to leave, and "most pairs first" already took them.
3. **"Most pairs first" is not costing anything measurable** (O1n − O1 = +0.0014 ± 0.0015).
4. **Consequence for the Round 2 target.** A +10% target cannot be reached by improving the scorer, the asker or the same-day matching. These levers together leave about 1% above R1. Anything more must come from **timing**: holding people back, or choosing today's pairs for the people they keep free for later days. Stage B measures that.

## Stage B: look-ahead oracle (running)

- **O4** = O12, plus each day it compares candidate matchings by simulating the next 10 days in the **real** future. It knows the true arrivals and departures, and the luck of new introductions is resampled. The candidate matchings are:
  - the usual matching;
  - the matching without "most pairs first";
  - holding back each of the two weakest pairs;
  - swapping each of them out for the best alternative.
- **O4c** is the same, but leaves the usual matching only for a look-ahead gain above 2%. With only 2 sampled futures per option, the best-looking option is often just a lucky estimate.
- Cost: about 130 s per episode, so this stage uses 10 seeds per family (60 episodes per arm).
- First world: O4 made 90 introductions against O12's 102, and scored lower. One world is noise, but this is the pattern expected if lucky estimates make "wait" win too often.

## Constraint values ("shadow prices", workshop 3: hard rules, soft goals)
A shadow price is how much the result would improve if one hard limit were loosened by one unit. For us there are two candidates.

**1. The daily question budget (12 units).**
- The kit leaving 521 of 720 units unused does **not** show the budget is worthless. It only shows that the kit's question rule stops early.
- What we have measured is the extreme case: a strong asker with an **unlimited** budget, from stage A above.
  - Every dealbreaker answer free (O2h vs R1): +0.0012 ± 0.0034.
  - Every answer free, dealbreaker and soft (O2hs vs R1): +0.0023 ± 0.0039.
  - With perfect scores on both sides (O12 vs O1): +0.0021.
- So removing the limit entirely is worth well under 1% of the kit's score to the candidate.
- [plan] A budget sweep for R1 at B ∈ {0, 3, 6, 9, 12, 15, 18}, with values above 12 as counterfactual diagnostics only. It should report expected wins, realised MSMI, hard and soft questions asked, the share of answers that changed the day's matching, the share of answered people later introduced, blank soft fields, and results by scenario. Cost: about 6 s per episode.

**2. Availability (each introduction occupies both people for 8+ days).**
- Price = (best future value if a person stays free) − (best future value if they are occupied).
- This is open question 1 in the note. Stage B (look-ahead oracle) measures it. Stage B has been run; results below.

**What the measurements decide:** improve the asker if the budget curve is still rising at 12, or the introducer's timing if the availability price is large. If both are small, the remaining work is robustness rather than score.

## Which levers are left (decision rules from review 5, applied to stage A)
| Lever | Oracle test (seeds 7500–7519, paired, per 100) | Share of kit score | Decision |
|---|---|---|---|
| Scorer (perfect pair chances, same timing) | O1 − R1 = +0.0021 ± 0.0027 | +0.6% | below 2%: stop scorer work |
| "Most pairs first" too aggressive? | O1n − O1 = +0.0014 ± 0.0015 | +0.4% | keep |
| Degree boost (block 7400) | D0 − R0 = +0.0009 ± 0.0018 | – | provisional; remove if simpler |
| Shift detector ceiling (true shifted weights, shift scenario only) | O1 − R1 = −0.0022 ± 0.0064 | ≈ 0 | low priority |
| Hard-question asker | O2h − R1 = +0.0012 ± 0.0034 | +0.3% | low priority |
| All information free plus true chances (same-day ceiling) | O12 − R1 = +0.0042 ± 0.0041 | +1.2% | same-day work is nearly exhausted |
| Timing (future-aware look-ahead) | O4 − O12 = −0.0011 ± 0.0040; O4c − O12 = +0.0001 ± 0.0027 (seeds 7500–7509) | ≈ 0 | below 2%: stop dynamic work |

**Arithmetic toward 10%.** On fresh seeds the candidate is +4.2% over the kit, so reaching 10% needs about +5.6% more. A perfect same-day policy reaches +5.4% over the kit. So 10% is possible only if timing is worth roughly 4–5% at oracle level, and a real policy captures only part of an oracle's gain.

**Stage B rule:**
- below 2% over O12: stop dynamic work and put the effort into robustness;
- 2–5%: test selective waiting;
- above 5%: build a one-day rollout.

## Stage B result (done, 120 episodes: seeds 7500–7509 × 6 scenarios × 2 arms)
| Comparison (paired, per 100) | Result |
|---|---|
| O4 (look-ahead using the real future) − O12 (best same-day oracle) | −0.0011 ± 0.0040 |
| O4c (cautious look-ahead) − O12 | +0.0001 ± 0.0027 |
| O4c − R1 (our candidate) | −0.0006 ± 0.0065 |
| Introductions: O12 / O4 / O4c | 72.2 / 70.8 / 71.3 per episode |

Raw data: `experiments/results/headroom_B_*.jsonl`. Summary: `results/headroom_B_summary.txt`.

**Reading.**
- Knowing the real future does not help the kinds of timing move a practical policy could make: holding back or swapping the weakest pairs, or dropping "most pairs first".
- The bold version held people back more often and lost slightly. The cautious version matched same-day results.
- On these 60 worlds, every oracle (true chances, free answers, look-ahead) sits within ±0.002 of the candidate R1.

**Limits of this test.** The look-ahead is short (10 days). It considers only 6 alternative matchings per day, and averages 2 sampled futures. So it bounds simple waiting and swapping, not every conceivable plan. The upper end of its 95% interval is about +2% over O12.

**Conclusion for Round 2.**
- On every lever we can measure, the candidate is at or near the ceiling: scoring, clarification, same-day allocation and simple timing.
- A +10% target is **not supported** by the evidence. A realistic claim is about +4–5% over the kit, already achieved, pending confirmation.
- Round 2 effort goes to:
  1. reliability: time guard, edge-case and JSON tests, Docker, the 1 MiB memory check;
  2. simplification: drop the degree boost if neutral;
  3. the one-time confirmation run on seeds 50000–50019.

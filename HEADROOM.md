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

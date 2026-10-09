# The Sequential Matching Problem: research and policy (solo team)

Entry for the Vouchsafe Sequential Matching Hackathon. Organiser kit: [RomeoJulietLove/The-Sequential-Matching-Problem](https://github.com/RomeoJulietLove/The-Sequential-Matching-Problem) (participant specification 1.0.0, kit commit `a8e26b35118cfa8e886a02f93984923e43ab64f6`).

## Round 1 research note
- **[ROUND1_NOTE.pdf](ROUND1_NOTE.pdf)** is the submitted note; [ROUND1_NOTE.md](ROUND1_NOTE.md) is its source.
- **[CHECKSUMS.txt](CHECKSUMS.txt)** gives the exact note commit, the measured-code commit and the PDF's SHA-256.

**In one paragraph.** The policy is built as sequential, constrained allocation. Each day it:
1. filters pairs by every hard constraint in both directions;
2. spends its 12-point question budget on dealbreaker bundles first, then on soft fields;
3. scores pairs with a fixed offline scorecard;
4. picks a maximum-cardinality, maximum-weight matching.

On a fresh 120-episode development block it improved expected MSMI by about 5.5% over the kit's greedy baseline (rough 95% range 2.8–8.2%). Offline oracles show little remaining headroom (§0 of the note, [HEADROOM.md](HEADROOM.md)).

## Repository layout
| Path | What it holds |
|---|---|
| `experiments/` | Every script behind the note's numbers (policy prototypes, tuning rounds, checks, oracles) |
| `experiments/results/` | Raw per-episode results (JSONL) and summaries for every experiment |
| [HEADROOM.md](HEADROOM.md) | Oracle headroom study (scoring, clarification, timing) and the Round 2 priorities |
| [SCORER.md](SCORER.md), [TUNING.md](TUNING.md) | How the scorer was built, and every tunable setting with its reason |
| [ASKER.md](ASKER.md), [TABLES.md](TABLES.md) | Clarification (asking) rules; data tables and member lifecycle design |
| [EDGE_CASES.md](EDGE_CASES.md), [STRESS_TESTS.md](STRESS_TESTS.md) | Edge cases and stress-world designs for Round 2 testing |
| [RESEARCH.md](RESEARCH.md), [NOTES.md](NOTES.md) | Papers and code reviewed; running working notes |

## Reproducing a result
Scripts run from the organiser kit folder, with `experiments/` on the Python path. For example:
```
PYTHONPATH=<this repo>/experiments python <this repo>/experiments/tune_v3.py 7300 10 development > out.jsonl
python <this repo>/experiments/summarise_scorer_v2.py out.jsonl
```
Environment: Python 3.13.16, numpy 2.5.3, networkx 3.4.2. §12 of the note maps each section to its script.

## Status
- Round 1 note: submitted.
- Round 2 (12–18 October): reliability work (time guard, edge-case and JSON tests, Docker), then one frozen confirmation run on seeds 50000–50019.

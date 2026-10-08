# Everything we can fine-tune, and why

All tunable numbers live in `KNOBS` in `experiments/scorer_v2_policy.py`. Each row says what the knob does, why it has its current value, a sensible range to search, and the risk if it is wrong.

**How to tune:**
- Use **training worlds** only, then confirm on separate worlds.
- Judge by **expected wins** (low noise), and confirm with MSMI.
- Search method: differential evolution (offline), or a small grid for 1–2 knobs.

## Scorer
| Knob | Now | Why this value | Search range | If wrong |
|---|---|---|---|---|
| `prior_w` (log-odds shift for same/different, per field) | development fit | Fitted offline on development replies | refit per scenario mix: pooled over all 6, or development only | Shift scenario: lifestyle points the wrong way until data overturns it |
| `base_rate` | 0.48 | Measured P(yes \| replied) | fixed (measured) | – |
| `k_field` (normaliser strength per field) | 40 (12 tested: −0.0118 ± 0.0027 expected wins → rejected) | Learning is slow (~25 replies in 10 days), so the prior must carry early decisions | 5 – 200 | Too high: never learns shift. Too low: noisy early scores |
| `k_base` | 20 | Base rate is learned fast (every reply counts) | 5 – 100 | small effect |
| `reply_prior` | 0.76 | Measured P(reply) | fixed (measured) | – |
| `k_reply` (normaliser for reply habit) | 10 | Median 2 introductions per person, so keep it gentle | 2 – 50 | Too low: one ignored message condemns a person |
| `k_pick` (normaliser for pickiness) | 10 (3 tested: no gain; off: AUC −0.016) | Same reason | 2 – 50 | Too low: noise; too high: no effect |
| `reply_power` | 2 | Reply habit is needed twice (introduction and second date) | 0 – 3 | 0 switches it off |
| `use_reply`, `use_pick` | on | Measured: reply habit 0.77 vs 0.68 and pickiness 0.51 vs 0.44 carry over | on/off (ablation) | – |
| `gamma` (ageing per day) | 1.0 | Proof: effects are constant within an episode (SCORER.md) | 0.95 – 1.0 (to confirm the proof empirically) | <1 wastes data |
| `mode` | thompson | Explores uncertain pairs (lecture; Chapelle & Li 2011) | thompson / mean | mean = no exploration |

## Introducer (matching)
| Knob | Now | Why | Range | If wrong |
|---|---|---|---|---|
| `u_new` (boost for never-introduced people) | 1.5 | Coverage is tie-breaker #1; friend's "floor ≥ 1" | 1 – 5 | Too high: weak pairs win just to raise coverage |
| `u_deg` (boost for few options) | 0.5 | Scarce people first (edge case A1; Akbarpour et al.) | 0 – 3 | Too high: ignores pair quality |
| waiting-days boost | not built | User's waiting-time idea | 0 – 0.1 per day | – |
| front-load before day 35 | not built | Drift scenario (edge case A5) | on/off | – |
| objective | Σ score, most pairs first | Fairness research: no upper cutoff | √score, log score + 10, coverage-first | small differences expected |

## Asker
| Knob | Now | Why | Range | If wrong |
|---|---|---|---|---|
| `soft_asks` | off in S2, on in S3 | 62% of fields are unknown; the best-possible-AUC gap is mostly unknown fields | on/off | – |
| `soft_min_options` | **1** (tuning round 1: AUC +0.024 ± 0.006 vs 2) | An answer only matters if a choice exists | 1 – 3 | 1 asks more (also helps learning); 3 asks fewer |
| `soft_order` | goal, pace, lifestyle, conversations | Goal strongest in 5 of 6 scenarios; pace strongest in shift | permutations | – |
| dealbreaker ask order | kit order | Oracle test: order matters ≤ 1% | – | – |

## Measured per run (so every change has a reason)
- expected wins (low noise) · MSMI · mutual acceptances · coverage · ask cost
- scorer AUC and calibration (predicted P(yes) vs actual) · share of unknown fields at decision time

"""Summarise test_scorer_v2.py output. Usage: python summarise_scorer_v2.py results/scorer_v2_*.jsonl"""
import json, sys, math, statistics as st, collections
rows = [json.loads(l) for f in sys.argv[1:] for l in open(f) if l.strip()]
pol = list(dict.fromkeys(r['policy'] for r in rows)); var = sorted({r['variant'] for r in rows})
by = collections.defaultdict(list)
for r in rows: by[r['policy'], r['variant']].append(r)
se = lambda x: st.stdev(x) / len(x) ** .5 if len(x) > 1 else 0
mean = lambda x: st.mean([v for v in x if not (isinstance(v, float) and math.isnan(v))])
print(f"{len(rows)} episodes, {len(rows)//len(pol)} per policy, scenarios: {', '.join(var)}\n")
print(f"{'policy':32s} {'exp.wins/100':>12s} {'vs K (paired)':>16s} {'MSMI':>6s} {'mutual':>7s} {'cover':>6s} {'asks':>5s} {'AUC':>6s} {'unknown':>8s}")
K = pol[0]
for p in pol:
    allr = [r for v in var for r in by[p, v]]
    d = [a['expected_wins'] - b['expected_wins'] for v in var for a, b in zip(sorted(by[p, v], key=lambda r: r['seed']), sorted(by[K, v], key=lambda r: r['seed']))]
    base = mean([r['expected_wins'] for r in by[K, v] for v in var]) if False else None
    print(f"{p:32s} {mean([r['expected_wins'] for r in allr]):12.4f} {st.mean(d):+8.4f} ± {se(d):.4f} {mean([r['msmi'] for r in allr]):6.2f} "
          f"{mean([r['mutual'] for r in allr]):7.2f} {mean([r['coverage'] for r in allr]):6.3f} {mean([r['ask_cost'] for r in allr]):5.0f} "
          f"{mean([r['auc'] for r in allr]):6.3f} {mean([r['unknown_share'] for r in allr]):8.2f}")
print('\nexpected wins per 100 by scenario:')
for p in pol: print(f"  {p:32s} " + '  '.join(f"{v[:6]}={mean([r['expected_wins'] for r in by[p, v]]):.3f}" for v in var))
print('\nscorer AUC by scenario:')
for p in pol: print(f"  {p:32s} " + '  '.join(f"{v[:6]}={mean([r['auc'] for r in by[p, v]]):.3f}" for v in var))
print('\ncalibration (mean predicted P(yes) vs actual yes-rate):')
for p in pol:
    allr = [r for v in var for r in by[p, v]]
    print(f"  {p:32s} predicted {mean([r['pred_mean'] for r in allr]):.3f}  actual {mean([r['yes_rate'] for r in allr]):.3f}")

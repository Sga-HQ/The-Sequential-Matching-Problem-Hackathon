"""Summarise ablation JSONL files: per-scenario and overall means with standard errors.
Usage: python summarise_ablation.py results/*.jsonl
"""
import json, sys, statistics, collections

rows = [json.loads(l) for f in sys.argv[1:] for l in open(f) if l.strip()]
by = collections.defaultdict(list)
for r in rows: by[(r['policy'], r['variant'])].append(r)
policies = sorted({r['policy'] for r in rows}); variants = sorted({r['variant'] for r in rows})
se = lambda xs: statistics.stdev(xs) / len(xs) ** .5 if len(xs) > 1 else 0

print(f"episodes: {len(rows)}  ({len(rows)//max(1,len(policies))} per policy)\n")
for metric in ('msmi', 'mutual', 'coverage', 'intros'):
    print(f'== {metric} (mean over scenarios; per-scenario means) ==')
    base = None
    for p in policies:
        fam = [statistics.mean(r[metric] for r in by[p, v]) for v in variants]
        overall = statistics.mean(fam)
        # paired difference vs A0 per seed, pooled over scenarios
        diffs = [a[metric] - b[metric] for v in variants
                 for a, b in zip(sorted(by[p, v], key=lambda r: r['seed']), sorted(by[policies[0], v], key=lambda r: r['seed']))]
        if base is None: base = overall
        rel = f"{100*(overall-base)/base:+.0f}%" if base else ''
        print(f"  {p:34s} {overall:7.3f}  vs A0 {statistics.mean(diffs):+.3f} ± {se(diffs):.3f} ({rel})   " +
              '  '.join(f"{v[:5]}={x:.2f}" for v, x in zip(variants, fam)))
    print()

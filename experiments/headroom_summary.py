"""Summarise headroom.py output: each arm vs the candidate (R1) and vs kit greedy (K), paired on the same worlds.
Uncertainty: one cluster-robust standard error over seeds (development, delayed and drift share a world per seed).
    python headroom_summary.py results/headroom_*.jsonl
"""
import collections, json, math, sys

rows = [json.loads(l) for f in sys.argv[1:] for l in open(f) if l.strip()]
by = collections.defaultdict(dict)                       # (seed, variant) -> arm -> row
for r in rows: by[r['seed'], r['variant']][r['policy']] = r
arms = sorted({r['policy'] for r in rows}, key=lambda a: ['K', 'R1', 'O1', 'O1n', 'O2h', 'O2hs', 'O12', 'O12x', 'O4'].index(a))

def paired(arm, ref, metric, variant=None):
    """Mean difference arm - ref and cluster-robust SE (clusters = seeds), over worlds where both ran."""
    cl = collections.defaultdict(list)
    for (seed, v), d in by.items():
        if arm in d and ref in d and (variant is None or v == variant): cl[seed].append(d[arm][metric] - d[ref][metric])
    n = sum(len(x) for x in cl.values())
    if n == 0: return float('nan'), float('nan'), 0
    m = sum(sum(x) for x in cl.values()) / n; G = len(cl)
    se = math.sqrt(G / max(1, G - 1) * sum((sum(x) - len(x) * m) ** 2 for x in cl.values())) / n if G > 1 else float('nan')
    return m, se, n

def mean(arm, metric, variant=None):
    xs = [d[arm][metric] for (s, v), d in by.items() if arm in d and (variant is None or v == variant)]
    return sum(xs) / len(xs) if xs else float('nan')

base = mean('K', 'expected_wins')
print(f"Expected wins per 100 arrived (unbiased for MSMI); greedy K = {base:.4f}. ± = 1 cluster-robust SE over seeds.\n")
print(f"{'arm':5s} {'n':>4s} {'exp.wins':>9s} {'vs K':>18s} {'vs K %':>7s} {'vs R1':>18s} {'intros':>7s} {'coverage':>8s} {'MSMI':>6s}")
for a in arms:
    dk = paired(a, 'K', 'expected_wins'); dr = paired(a, 'R1', 'expected_wins')
    print(f"{a:5s} {dk[2]:4d} {mean(a, 'expected_wins'):9.4f} {dk[0]:+9.4f} ± {dk[1]:.4f} {100 * dk[0] / base:+6.1f}% "
          f"{dr[0]:+9.4f} ± {dr[1]:.4f} {mean(a, 'intros'):7.1f} {mean(a, 'coverage'):8.3f} {mean(a, 'msmi'):6.3f}")
print("\nBy scenario: expected wins vs R1 (paired)")
variants = sorted({v for _, v in by})
print(f"{'arm':5s} " + ' '.join(f"{v:>18s}" for v in variants))
for a in arms:
    if a == 'R1': continue
    print(f"{a:5s} " + ' '.join("{:+8.4f} ± {:.4f}".format(*paired(a, 'R1', 'expected_wins', v)[:2]) for v in variants))
print("\nBy scenario: greedy K expected wins: " + ', '.join(f"{v} {mean('K', 'expected_wins', v):.3f}" for v in variants))

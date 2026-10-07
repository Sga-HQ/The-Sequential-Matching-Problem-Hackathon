"""Learn soft-field weights from simulator 'packets' and test whether mutual fields add anything.
Run from the organiser kit folder (needs kit.py):  python soft_weights.py
Packets use ONLY what was observable at introduction time + the later observed reply (yes/no; no-reply dropped).
Train seeds 1000-1029, test seeds 2000-2014 (disjoint).
"""
import sys, math, random
sys.path.insert(0, '.')
import kit
import numpy as np

SOFT = kit.SOFT
FOUR = ['relationship_goal', 'relationship_pace', 'lifestyle', 'conversations']

def packets(seed, variant):
    sim = kit.Simulator(kit.generate(seed, 200, 'pk', variant)); rows = []
    for day in range(60):
        sim.resolve_asks(kit.baseline_asks(sim.observe()))
        s = sim.observe(); M = {m['member_id']: m for m in s['members']}
        pairs = kit.baseline_match(s)
        snap = {}
        for a, b in pairs:
            for x, y in ((a, b), (b, a)):
                snap[(x, y)] = (M[x]['fields'], M[y]['fields'], M[x], M[y])
        sim.advance(pairs)
        for (x, y), v in snap.items(): rows.append((x, y, sim.introductions[-1]['assigned_day'], v))
    resp = {}
    for e in sim.events:
        if e['event'] == 'introduction_response' and e['value'] is not None: resp[e['member_id'], e['introduction_id']] = e['value'] == 'yes'
    intro_of = {(i['user_a'], i['user_b']): i['introduction_id'] for i in sim.introductions}
    intro_of.update({(i['user_b'], i['user_a']): i['introduction_id'] for i in sim.introductions})
    out = []
    for x, y, _, (fx, fy, mx, my) in rows:
        k = (x, intro_of[(x, y)])
        if k in resp: out.append((feat(fx, fy, mx, my), resp[k]))
    return out

def feat(fx, fy, mx, my):
    f = {}
    for k in SOFT:
        a, b = fx[k], fy[k]
        f[k + '=match'] = float(a is not None and b is not None and a == b)
        f[k + '=differ'] = float(a is not None and b is not None and a != b)
    wc = {fx['wants_children'], fy['wants_children']}
    f['mutual:wants_children_same'] = float(len(wc) == 1 and 'unsure' not in wc)
    f['mutual:wants_children_unsure'] = float('unsure' in wc)
    f['mutual:schedule_overlap_n'] = float(len(set(fx['schedule']) & set(fy['schedule'])))
    f['mutual:same_zone'] = float(mx['zone'] == my['zone'])
    f['mutual:age_gap'] = abs(mx['age'] - my['age']) / 10
    return f

def fit(X, y, l2=1.0, it=50):  # logistic regression, Newton's method
    X = np.hstack([np.ones((len(X), 1)), X]); w = np.zeros(X.shape[1])
    for _ in range(it):
        p = 1 / (1 + np.exp(-X @ w)); g = X.T @ (p - y) + l2 * np.r_[0, w[1:]]
        H = (X * (p * (1 - p))[:, None]).T @ X + l2 * np.diag(np.r_[0, np.ones(len(w) - 1)])
        w -= np.linalg.solve(H, g)
    return w
def logloss(w, X, y):
    X = np.hstack([np.ones((len(X), 1)), X]); p = np.clip(1 / (1 + np.exp(-X @ w)), 1e-9, 1 - 1e-9)
    return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
def auc(w, X, y):
    X = np.hstack([np.ones((len(X), 1)), X]); s = X @ w; o = np.argsort(s); r = np.empty(len(s)); r[o] = np.arange(len(s))
    pos = y == 1; return (r[pos].sum() - pos.sum() * (pos.sum() - 1) / 2) / (pos.sum() * (~pos).sum())

for variant in ('development', 'shift'):
    tr = [p for s in range(1000, 1030) for p in packets(s, variant)]
    te = [p for s in range(2000, 2015) for p in packets(s, variant)]
    keys = list(tr[0][0])
    sets = {
        'base rate only': [],
        '4 soft (goal,pace,lifestyle,convo)': [k for k in keys if k.split('=')[0] in FOUR],
        'all 7 soft': [k for k in keys if not k.startswith('mutual')],
        '7 soft + mutual/other': keys,
    }
    ytr = np.array([v for _, v in tr], float); yte = np.array([v for _, v in te], float)
    print(f'\n=== variant={variant}  train replies={len(tr)}  test replies={len(te)}  yes-rate={ytr.mean():.2f}')
    for name, ks in sets.items():
        Xtr = np.array([[f[k] for k in ks] for f, _ in tr]).reshape(len(tr), len(ks)); Xte = np.array([[f[k] for k in ks] for f, _ in te]).reshape(len(te), len(ks))
        w = fit(Xtr, ytr)
        print(f'  {name:36s} test log-loss={logloss(w, Xte, yte):.4f}  test AUC={auc(w, Xte, yte):.3f}')
        if name == '7 soft + mutual/other':
            for k, v in sorted(zip(ks, w[1:]), key=lambda t: -abs(t[1])): print(f'      weight {v:+.2f}  {k}')

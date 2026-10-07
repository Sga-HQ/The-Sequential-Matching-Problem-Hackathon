"""Which way of combining P(A yes) and P(B yes) best predicts 'both said yes'?
Compares product (independence), harmonic mean (RECON), uninorm (chaos-rrs), minimum, arithmetic mean.
Uses soft_weights.py packets: train seeds 1000-1029, test 2000-2014. Run from organiser kit folder.
"""
import sys
sys.path.insert(0, '.')
import numpy as np
import kit
from soft_weights import feat, fit, auc, FOUR

def pair_packets(seed, variant='development'):
    sim = kit.Simulator(kit.generate(seed, 200, 'pk', variant)); rows = []
    for day in range(60):
        sim.resolve_asks(kit.baseline_asks(sim.observe()))
        s = sim.observe(); M = {m['member_id']: m for m in s['members']}
        pairs = kit.baseline_match(s)
        for a, b in pairs: rows.append((a, b, M[a], M[b]))
        sim.advance(pairs)
    iid = {(i['user_a'], i['user_b']): i['introduction_id'] for i in sim.introductions}
    iid.update({(b, a): v for (a, b), v in iid.items()})
    resp = {(e['member_id'], e['introduction_id']): e['value'] for e in sim.events if e['event'] == 'introduction_response'}
    out = []
    for a, b, ma, mb in rows:
        k = iid[(a, b)]; ra, rb = resp.get((a, k)), resp.get((b, k))
        if ra is None or rb is None: continue           # need both replies to know the pair outcome
        out.append((feat(ma['fields'], mb['fields'], ma, mb), feat(mb['fields'], ma['fields'], mb, ma), ra == 'yes', rb == 'yes'))
    return out

tr = [p for s in range(1000, 1030) for p in pair_packets(s)]
te = [p for s in range(2000, 2015) for p in pair_packets(s)]
keys = [k for k in tr[0][0] if k.split('=')[0] in FOUR]
X = lambda f: [f[k] for k in keys]
Xtr = np.array([X(fa) for fa, fb, ya, yb in tr] + [X(fb) for fa, fb, ya, yb in tr])
ytr = np.array([ya for *_, ya, yb in tr] + [yb for *_, ya, yb in tr], float)
w = fit(Xtr, ytr)
p = lambda f: 1 / (1 + np.exp(-(w[0] + np.dot(w[1:], X(f)))))
pa = np.array([p(fa) for fa, fb, ya, yb in te]); pb = np.array([p(fb) for fa, fb, ya, yb in te])
both = np.array([ya and yb for *_, ya, yb in te], float)
print(f'test pairs with both replies: {len(te)}   both-yes rate: {both.mean():.3f}')
rules = {
    'product  (A·B)': pa * pb,
    'harmonic mean (RECON)': 2 * pa * pb / (pa + pb),
    'uninorm (chaos-rrs)': pa * pb / (pa * pb + (1 - pa) * (1 - pb)),
    'minimum': np.minimum(pa, pb),
    'arithmetic mean': (pa + pb) / 2,
}
Z = np.zeros((len(te), 0))
for name, s in rules.items():
    print(f'  {name:24s} AUC for both-yes = {auc(np.array([0.0, 1.0]), s.reshape(-1, 1), both):.3f}')

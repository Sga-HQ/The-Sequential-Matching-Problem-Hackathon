"""(1) Accuracy of the 5-point Gauss-Hermite win probability vs a 60-point reference.
(2) Does a pair's realized MSMI chance depend on the assignment day? (kit greedy baseline, 20 worlds x 6 scenarios)"""
import math, random, collections, sys, numpy as np, kit
from policy import decide
from test_scorer_v2 import p_win, weights, sig
# (1)
xs, ws = np.polynomial.hermite.hermgauss(60)
def p_ref(a, b, variant, day):
    ta, tb = a['truth'], b['truth']; W = weights(variant)
    fit = sum(w * (1 if ta[k] == tb[k] else -.5) for k, w in W.items()); drift = -.5 if variant == 'drift' and day >= 35 else 0
    goal = .4 * (ta['relationship_goal'] == tb['relationship_goal']); t = 0
    for x, wt in zip(xs, ws):
        s = x * math.sqrt(2) * .45
        acc = a['response_rate'] * b['response_rate'] * sig(-.25 + a['bias'] + fit + s + drift) * sig(-.25 + b['bias'] + fit + s + drift)
        sec = (a['response_rate'] * .6 * sig(.15 + a['second_bias'] + s + goal)) * (b['response_rate'] * .6 * sig(.15 + b['second_bias'] + s + goal))
        t += wt / math.sqrt(math.pi) * acc * .78 * sec
    return t
rng = random.Random(1); err = []; rel = []
for seed in range(9600, 9610):
    M = kit.generate(seed, 200, 'gh', 'development')['members']
    for _ in range(300):
        a, b = rng.sample(M, 2); p5, pr = p_win(a, b, 'development', 0), p_ref(a, b, 'development', 0)
        err.append(abs(p5 - pr)); rel.append(abs(p5 - pr) / pr)
print(f'(1) 3000 random pairs: max abs error {max(err):.2e}, max relative error {max(rel):.2%}, mean relative {sum(rel)/len(rel):.3%}')
# (2)
B = [(0, 9), (10, 19), (20, 34), (35, 49), (50, 59)]
for V in ['development', 'sparse', 'cold_start', 'delayed', 'shift', 'drift']:
    n = collections.Counter(); m = collections.Counter()
    for seed in range(9700, 9720):
        sim = kit.Simulator(kit.generate(seed, 200, 'day', V))
        for d in range(60):
            r = decide({'phase': 'ask', 'state': sim.observe(), 'memory': None}); sim.resolve_asks(r['asks'])
            r = decide({'phase': 'match', 'state': sim.observe(), 'memory': None}); sim.advance(r['pairs'])
        for _ in range(40): sim.advance([])
        ev = collections.defaultdict(list)
        for e in sim.receive_feedback(): ev[e['introduction_id']].append(e)
        for i in sim.introductions:
            es = ev[i['introduction_id']]; ds = [e for e in es if e['event'] == 'date_happened' and e['value'] is True]
            ss = [e for e in es if e['event'] == 'second_meeting_intention']
            ok = bool(ds) and ds[0]['occurred_day'] - i['assigned_day'] <= 30 and len(ss) == 2 and all(e['value'] == 'yes' and e['occurred_day'] - ds[0]['occurred_day'] <= 3 for e in ss)
            k = next(j for j, (lo, hi) in enumerate(B) if lo <= i['assigned_day'] <= hi); n[k] += 1; m[k] += ok
    print(f'(2) {V:11s} ' + '  '.join(f'days {lo}-{hi}: {100*m[k]/max(1,n[k]):.1f}% of {n[k]}' for k, (lo, hi) in enumerate(B)))

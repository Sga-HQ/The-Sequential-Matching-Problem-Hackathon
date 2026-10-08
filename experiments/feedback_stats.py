"""What data comes back after introductions (kit greedy baseline, development, 10 worlds)."""
import collections, statistics, kit
from policy import decide
c = collections.Counter(); lag = collections.defaultdict(list); rel = []
for seed in range(9100, 9110):
    sim = kit.Simulator(kit.generate(seed, 200, 'fb', 'development'))
    for d in range(60):
        r = decide({'phase': 'ask', 'state': sim.observe(), 'memory': None}); sim.resolve_asks(r['asks'])
        r = decide({'phase': 'match', 'state': sim.observe(), 'memory': None}); sim.advance(r['pairs'])
    for _ in range(40): sim.advance([])
    intro = {i['introduction_id']: i for i in sim.introductions}
    per = collections.defaultdict(lambda: [0, 0])
    for e in sim.receive_feedback():
        v = e['value']; k = (e['event'], 'none' if v is None else str(v))
        c[k] += 1
        lag[e['event']].append(e['observed_day'] - intro[e['introduction_id']]['assigned_day'])
        if e['event'] == 'introduction_response':
            per[e['member_id']][0] += 1; per[e['member_id']][1] += v is None
    rel += [m / n for n, m in per.values() if n >= 2]
print('intros/world', len(sim.introductions))
for k, v in sorted(c.items()): print(k, round(v / 10, 1), 'per world')
for k, v in lag.items(): print(k, 'days after intro: median', statistics.median(v), 'max', max(v))
print('people with >=2 intros: share of their replies missing — mean', round(statistics.mean(rel), 2), ' share with >=50% missing', round(sum(x >= .5 for x in rel) / len(rel), 2))

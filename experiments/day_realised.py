"""Realised MSMI rate per introduction by assignment-day bucket (kit greedy, development) on new worlds."""
import collections, sys, kit
from policy import decide
B = [(0, 9), (10, 19), (20, 34), (35, 49), (50, 59)]
n = collections.Counter(); m = collections.Counter()
for seed in range(int(sys.argv[1]), int(sys.argv[2])):
    sim = kit.Simulator(kit.generate(seed, 200, 'day2', 'development'))
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
print(' '.join(f'{k}:{m[k]}/{n[k]}' for k in range(5)))

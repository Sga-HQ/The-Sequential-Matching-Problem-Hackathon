"""Weight of Evidence / Information Value of each soft field (same / different / unknown at decision time)
for the introduction reply (yes = 'good', no = 'bad'). Kit greedy baseline, 15 worlds per scenario."""
import collections, math, sys, kit
from policy import decide
from kit import SOFT
V = sys.argv[1]
cnt = collections.defaultdict(lambda: [0, 0])
for seed in range(9500, 9515):
    sim = kit.Simulator(kit.generate(seed, 200, 'iv', V)); snap = {}
    for d in range(60):
        r = decide({'phase': 'ask', 'state': sim.observe(), 'memory': None}); sim.resolve_asks(r['asks'])
        st = sim.observe(); M = {m['member_id']: m for m in st['members']}
        r = decide({'phase': 'match', 'state': st, 'memory': None})
        for a, b in r['pairs']: snap[frozenset((a, b)), d] = {a: M[a]['fields'], b: M[b]['fields']}
        sim.advance(r['pairs'])
    for _ in range(10): sim.advance([])
    I = {i['introduction_id']: i for i in sim.introductions}
    for e in sim.receive_feedback():
        if e['event'] != 'introduction_response' or e['value'] is None: continue
        i = I[e['introduction_id']]; me = e['member_id']; ot = i['user_b'] if i['user_a'] == me else i['user_a']
        F = snap[frozenset((me, ot)), i['assigned_day']]
        for f in SOFT:
            s = 'unknown' if F[me][f] is None or F[ot][f] is None else ('same' if F[me][f] == F[ot][f] else 'different')
            cnt[f, s][0 if e['value'] == 'yes' else 1] += 1
print('==', V)
for f in SOFT:
    G = sum(cnt[f, s][0] for s in ('same', 'different', 'unknown')); B = sum(cnt[f, s][1] for s in ('same', 'different', 'unknown'))
    iv = 0; parts = []
    for s in ('same', 'different', 'unknown'):
        g, b = cnt[f, s][0] / G, cnt[f, s][1] / B
        woe = math.log((g + 1e-9) / (b + 1e-9)); iv += (g - b) * woe; parts.append(f'{s} {woe:+.2f}')
    print(f'  {f:23s} IV {iv:.3f}   WoE: ' + '  '.join(parts))

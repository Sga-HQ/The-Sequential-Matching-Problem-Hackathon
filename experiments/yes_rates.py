"""Yes-rate of introduction replies by soft-field match/differ/unknown, as the policy would see it (observed fields only)."""
import collections, kit
from policy import decide
FIELDS = ['relationship_goal', 'relationship_pace', 'lifestyle', 'conversations']
cnt = collections.defaultdict(lambda: [0, 0]); base = [0, 0]
for seed in range(9200, 9230):
    sim = kit.Simulator(kit.generate(seed, 200, 'yr', 'development'))
    for d in range(60):
        r = decide({'phase': 'ask', 'state': sim.observe(), 'memory': None}); sim.resolve_asks(r['asks'])
        r = decide({'phase': 'match', 'state': sim.observe(), 'memory': None}); sim.advance(r['pairs'])
    for _ in range(10): sim.advance([])
    st = sim.observe(); M = {m['member_id']: m for m in st['members']}; I = {i['introduction_id']: i for i in st['introductions']}
    for e in st['feedback']:
        if e['event'] != 'introduction_response' or e['value'] is None: continue
        i = I[e['introduction_id']]; me = M[e['member_id']]; ot = M[i['user_b'] if i['user_a'] == e['member_id'] else i['user_a']]
        y = e['value'] == 'yes'; base[0] += y; base[1] += 1
        for f in FIELDS:
            a, b = me['fields'][f], ot['fields'][f]
            s = 'unknown' if a is None or b is None else ('match' if a == b else 'differ')
            cnt[f, s][0] += y; cnt[f, s][1] += 1
print(f'all replies: {base[1]}  yes-rate {base[0]/base[1]:.2f}')
for f in FIELDS:
    print(f'{f:18s}', '  '.join(f'{s}: {cnt[f,s][0]/max(1,cnt[f,s][1]):.2f} (n={cnt[f,s][1]})' for s in ('match', 'differ', 'unknown')))

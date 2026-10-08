"""Data a scorer needs, per scenario (kit greedy baseline, 15 worlds each).
1. Yes-rate by each of the 7 soft fields (match / differ / unknown) using fields KNOWN AT DECISION TIME.
2. Share of introductions where each field is unknown at decision time.
3. Replies available to learn from, by day (how fast can a learner learn?).
4. Introductions per person (how much per-person data exists).
5. Ceiling of any scorer (offline, uses hidden truth): AUC of the yes/no reply predicted by
   (a) the true soft-field effect only, (b) + the person's hidden pickiness, (c) + the pair's shared luck."""
import collections, math, sys, statistics, kit
from policy import decide
from kit import SOFT, rand_for
V = sys.argv[1]
yes = collections.defaultdict(lambda: [0, 0]); unk = collections.Counter(); n_dir = 0
by_day = collections.Counter(); per_person = []; preds = {'fields': [], 'fields+pickiness': [], 'fields+pickiness+shared': []}; ys = []
W = {'relationship_goal': .7, 'relationship_pace': .4, 'lifestyle': .25, 'conversations': .2}
if V == 'shift': W = {'relationship_goal': .25, 'relationship_pace': .8, 'lifestyle': -.25, 'conversations': .5}
def auc(s, y):
    pos = [a for a, b in zip(s, y) if b]; neg = [a for a, b in zip(s, y) if not b]
    allv = sorted((v, i) for i, v in enumerate(s)); rank = [0] * len(s)
    for r, (v, i) in enumerate(allv): rank[i] = r + 1
    rp = sum(rank[i] for i, b in enumerate(y) if b)
    return (rp - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))
for seed in range(9400, 9415):
    world = kit.generate(seed, 200, 'sd', V); sim = kit.Simulator(world)
    snap = {}   # introduction pair -> fields at decision time
    for d in range(60):
        r = decide({'phase': 'ask', 'state': sim.observe(), 'memory': None}); sim.resolve_asks(r['asks'])
        st = sim.observe(); M = {m['member_id']: m for m in st['members']}
        r = decide({'phase': 'match', 'state': st, 'memory': None})
        for a, b in r['pairs']: snap[(a, b, d)] = (M[a]['fields'], M[b]['fields'])
        sim.advance(r['pairs'])
    for _ in range(10): sim.advance([])
    T = {m['member_id']: m for m in world['members']}
    cnt = collections.Counter()
    I = {i['introduction_id']: i for i in sim.introductions}
    for e in sim.receive_feedback():
        if e['event'] != 'introduction_response': continue
        i = I[e['introduction_id']]; a, b, d = i['user_a'], i['user_b'], i['assigned_day']
        key = (a, b, d) if (a, b, d) in snap else (b, a, d)
        fa, fb = snap[key] if key[0] == a else snap[key][::-1]
        me = e['member_id']; mf, of = (fa, fb) if me == a else (fb, fa)
        other = b if me == a else a
        cnt[me] += 0
        if e['value'] is None: continue
        y = e['value'] == 'yes'; n_dir += 1; by_day[e['observed_day'] // 10] += 1
        for f in SOFT:
            s = 'unk' if mf[f] is None or of[f] is None else ('match' if mf[f] == of[f] else 'differ')
            yes[f, s][0] += y; yes[f, s][1] += 1; unk[f] += s == 'unk'
        tm, to = T[me]['truth'], T[other]['truth']
        fit = sum(w * (1 if tm[k] == to[k] else -.5) for k, w in W.items())
        shared = rand_for(world['seed'], *sorted((a, b)), d).gauss(0, .45) if False else rand_for(world['seed'], a, b, d).gauss(0, .45)
        preds['fields'].append(fit); preds['fields+pickiness'].append(fit + T[me]['bias'])
        preds['fields+pickiness+shared'].append(fit + T[me]['bias'] + shared); ys.append(y)
    c = collections.Counter(u for i in sim.introductions for u in (i['user_a'], i['user_b']))
    per_person += list(c.values())
print(f'== {V}: {n_dir} yes/no replies over 15 worlds; overall yes-rate {sum(ys)/len(ys):.2f}')
for f in SOFT:
    m, dd, u = (yes[f, s] for s in ('match', 'differ', 'unk'))
    print(f'  {f:23s} same {m[0]/max(1,m[1]):.2f}  different {dd[0]/max(1,dd[1]):.2f}  unknown at decision {unk[f]/n_dir:.0%}')
print('  replies arriving per 10-day block (per world):', [round(by_day[k] / 15, 1) for k in sorted(by_day)])
print(f'  introductions per introduced person: median {statistics.median(per_person)}, mean {statistics.mean(per_person):.1f}, max {max(per_person)}')
for k, v in preds.items(): print(f'  best possible AUC using {k:26s} {auc(v, ys):.3f}')

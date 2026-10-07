"""Why do allowed pairs go unused under the kit baseline? Diagnosis using hidden truth (measurement only).
Run from the organiser kit folder: python why_unused.py
"""
import sys,copy,itertools,collections;sys.path.insert(0,'.');import kit
C=collections.Counter(); lostp=collections.Counter()
import math
sig=lambda z:1/(1+math.exp(-z))
for seed in range(6000,6010):
    w=kit.generate(seed,200,'ablation','development'); M={}
    for m in w['members']:
        if m['arrived_day']>59 or any(m['field_status'][k]=='declined' for k in kit.HARD): continue
        t=copy.deepcopy(m); t['fields']={**m['fields'],**{k:m['truth'][k] for k in kit.HARD}}; M[m['member_id']]=t
    E=[(a,b) for a,b in itertools.combinations(M,2) if kit.eligibility(M[a],M[b])['status']=='feasible']
    sim=kit.Simulator(w); busy_days=collections.Counter()
    first_free={}
    for d in range(60):
        s=sim.observe()
        for m in s['members']:
            if m['available'] and all(m['fields'][k] is not None for k in kit.HARD): first_free.setdefault(m['member_id'],d)
        sim.resolve_asks(kit.baseline_asks(s)); sim.advance(kit.baseline_match(sim.observe()))
    I={frozenset((i['user_a'],i['user_b'])) for i in sim.introductions}
    paused=set()
    for e in sim.events:
        if e['event']=='pause_after_mutual_interest' and e['observed_day']<=59:
            i=next(x for x in sim.introductions if x['introduction_id']==e['introduction_id']); paused|={i['user_a'],i['user_b']}
    nint=collections.Counter(u for i in sim.introductions for u in (i['user_a'],i['user_b']))
    for a,b in E:
        if frozenset((a,b)) in I: continue
        ma,mb=sim.members[a],sim.members[b]
        if a in paused or b in paused: r='a person already found a match (paused)'
        elif min(ma['exit_day'],mb['exit_day'])<60: r='a person left the app'
        elif max(first_free.get(a,99),first_free.get(b,99))>=45: r='a person became matchable late (day 45+)'
        elif max(nint[a],nint[b])>=4: r='a person was busy with many other introductions'
        else: r='other timing (both never free on the same day)'
        C[r]+=1
tot=sum(C.values())
for r,c in C.most_common(): print(f'{c/10:5.1f} per world ({100*c/tot:.0f}%)  {r}')

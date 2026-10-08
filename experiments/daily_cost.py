"""Measure the daily work of the matching step on real 200-person worlds (development variant)."""
import time, statistics, random, sys
import networkx as nx
import kit
from prototype_policy import decide, make_scorer, complete
from kit import eligibility
rows = []
for seed in range(9000, 9005):
    sim = kit.Simulator(kit.generate(seed, 200, 'cost', 'development'))
    for day in range(60):
        r = decide({'phase': 'ask', 'state': sim.observe(), 'memory': None}); sim.resolve_asks(r['asks'])
        st = sim.observe()
        t0 = time.perf_counter()
        free = [m for m in st['members'] if m['available'] and complete(m)]
        past = {frozenset((i['user_a'], i['user_b'])) for i in st['introductions']}
        checks = 0; edges = []
        for i, a in enumerate(free):
            for b in free[i+1:]:
                checks += 1
                if frozenset((a['member_id'], b['member_id'])) not in past and eligibility(a, b)['status'] == 'feasible':
                    edges.append((a, b))
        t1 = time.perf_counter()
        p = make_scorer(st, 'thompson', random.Random(day)); w = [p(a, b) * p(b, a) for a, b in edges]
        t2 = time.perf_counter()
        G = nx.Graph(); [G.add_edge(a['member_id'], b['member_id'], weight=int(x*1e6)+1) for (a, b), x in zip(edges, w)]
        M = nx.max_weight_matching(G, maxcardinality=True)
        t3 = time.perf_counter()
        rows.append(dict(day=day, arrived=len(st['members']), free=len(free), checks=checks, edges=len(edges), pairs=len(M),
                         filt=1000*(t1-t0), score=1000*(t2-t1), match=1000*(t3-t2)))
        r = decide({'phase': 'match', 'state': st, 'memory': None}); sim.advance(r['pairs'])
def show(lo, hi):
    sel = [r for r in rows if lo <= r['day'] < hi]
    print(f"days {lo:2d}-{hi-1:2d}: " + "  ".join(f"{k}={statistics.mean(r[k] for r in sel):.1f}" for k in ['arrived','free','checks','edges','pairs','filt','score','match']) +
          f"  max_total_ms={max(r['filt']+r['score']+r['match'] for r in sel):.0f}")
for lo, hi in [(0,1),(1,10),(10,20),(20,40),(40,60)]: show(lo, hi)
t=time.perf_counter(); import numpy; import networkx; print('import ms', round(1000*(time.perf_counter()-t)))

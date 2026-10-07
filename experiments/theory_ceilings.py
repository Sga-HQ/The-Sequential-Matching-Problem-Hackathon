"""Theoretical ceilings from the simulator's own success formula (kit.py), no episode simulation.
For every allowed pair, compute its exact chance of becoming a win (MSMI), integrating over the shared
random term. Hidden values are used ONLY to measure ceilings, never in a policy.
Run from the organiser kit folder: python theory_ceilings.py
"""
import sys, copy, itertools, math, statistics as st
sys.path.insert(0, '.')
import kit
sig = lambda z: 1 / (1 + math.exp(-z))
W = {'relationship_goal': .7, 'relationship_pace': .4, 'lifestyle': .25, 'conversations': .2}
# Gauss-Hermite nodes for shared ~ N(0, 0.45)
NODES = [(-2.0201828, 0.0199532), (-0.9585725, 0.3936193), (0.0, 0.9453087), (0.9585725, 0.3936193), (2.0201828, 0.0199532)]

def p_win(a, b, use_hidden=True):
    ta, tb = a['truth'], b['truth']
    fit = sum(w * (1 if ta[k] == tb[k] else -.5) for k, w in W.items())
    goal = .4 * (ta['relationship_goal'] == tb['relationship_goal'])
    ba, bb = (a['bias'], b['bias']) if use_hidden else (0, 0)
    sa, sb = (a['second_bias'], b['second_bias']) if use_hidden else (0, 0)
    ra, rb = (a['response_rate'], b['response_rate']) if use_hidden else (.765, .765)
    tot = 0
    for x, wt in NODES:
        s = x * math.sqrt(2) * .45
        acc = ra * rb * sig(-.25 + ba + fit + s) * sig(-.25 + bb + fit + s)
        sec = (ra * .6 * sig(.15 + sa + s + goal)) * (rb * .6 * sig(.15 + sb + s + goal))   # answer, on time (<=3 of 1..5), yes
        tot += wt / math.sqrt(math.pi) * acc * .78 * sec
    return tot

def greedy_b(edges, cap, key):
    used = {}; out = []
    for e in sorted(edges, key=key, reverse=True):
        u, v = e
        if used.get(u, 0) < cap.get(u, 0) and used.get(v, 0) < cap.get(v, 0):
            out.append(e); used[u] = used.get(u, 0) + 1; used[v] = used.get(v, 0) + 1
    return out

res = []
for seed in range(6000, 6010):
    w = kit.generate(seed, 200, 'ablation', 'development')
    M = {}
    for m in w['members']:
        if m['arrived_day'] > 59 or any(m['field_status'][k] == 'declined' for k in kit.HARD): continue
        t = copy.deepcopy(m); t['fields'] = {**m['fields'], **{k: m['truth'][k] for k in kit.HARD}}; M[m['member_id']] = t
    E = [(a, b) for a, b in itertools.combinations(M, 2) if kit.eligibility(M[a], M[b])['status'] == 'feasible']
    P = {e: p_win(M[e[0]], M[e[1]]) for e in E}
    Pobs = {e: p_win(M[e[0]], M[e[1]], use_hidden=False) for e in E}
    sim = kit.Simulator(w)
    for d in range(60):
        sim.resolve_asks(kit.baseline_asks(sim.observe())); sim.advance(kit.baseline_match(sim.observe()))
    I = [tuple(sorted((i['user_a'], i['user_b']))) for i in sim.introductions]
    I = [e if e in P else (e[1], e[0]) for e in I]; I = [e for e in I if e in P]
    cap = {}
    for u, v in I: cap[u] = cap.get(u, 0) + 1; cap[v] = cap.get(v, 0) + 1
    res.append(dict(
        baseline=sum(P[e] for e in I),
        soft_oracle=sum(P[e] for e in greedy_b(E, cap, key=lambda e: Pobs[e])),      # perfect knowledge of soft-field effects
        full_oracle=sum(P[e] for e in greedy_b(E, cap, key=lambda e: P[e])),         # also knows hidden pickiness + reply rate
        all_pairs=sum(P.values()), n_intro=len(I), n_edges=len(E),
        p_min=min(P.values()), p_mean=st.mean(P.values()), p_max=max(P.values())))
b = st.mean(r['baseline'] for r in res)
print(f"expected wins per episode, development, 10 worlds (same number of introductions per person as baseline):")
for k, label in [('baseline', 'kit greedy (measured pairs)'), ('soft_oracle', 'perfect soft-field scorer'),
                 ('full_oracle', 'perfect scorer incl. hidden pickiness/reply rate'), ('all_pairs', 'use EVERY allowed pair')]:
    v = st.mean(r[k] for r in res); print(f"  {label:48s} {v:.3f}  ({100*(v-b)/b:+.0f}%)")
print(f"  introductions used {st.mean(r['n_intro'] for r in res):.0f} of {st.mean(r['n_edges'] for r in res):.0f} allowed pairs")
print(f"  per-pair win chance: min {st.mean(r['p_min'] for r in res):.4f}  mean {st.mean(r['p_mean'] for r in res):.4f}  max {st.mean(r['p_max'] for r in res):.4f}")

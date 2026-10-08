"""Round 2 headroom study: offline ORACLE policies that each see one kind of hidden information.
Hidden values are used here ONLY to measure where improvement is possible; no arm is a submittable policy.
Run from the organiser kit folder (with this folder on PYTHONPATH):
    python headroom.py <first_seed> <n_seeds> <variant> <arm,arm,...> > out.jsonl
Arms:
  K     kit greedy baseline                         R1   current candidate (fixed scorecard, broad soft asks)
  O1    R1 asks + TRUE pair success chances          O1n  as O1 but plain max-weight (no "most pairs first")
  O2h   all askable hard answers free + R1 scorer    O2hs all askable hard AND soft answers free + R1 scorer
  O12   all answers free + true chances              O12x O12 + knows who leaves within 8 days (priority)
  O4    O12 + 10-day look-ahead in the REAL future (true arrivals/departures; new luck resampled)
Metric: expected wins per 100 arrived (exact success probability summed over introductions; unbiased for MSMI).
"""
import copy, json, random, sys, time
sys.path.insert(0, '.')
import networkx as nx
import kit
from kit import eligibility, HARD
import scorer_v2_policy as v2
from test_scorer_v2 import p_win

FROZEN = dict(k_field=1e6, k_base=1e6, use_reply=False, use_pick=False, mode='mean')
R1 = dict(FROZEN, soft_asks=True, soft_min_options=1, soft_rule='all', u_new=1.0, u_deg=0.5)
SOFT = list(kit.OPTIONS)

def reveal(sim, keys):
    """Relaxed oracle: every arrived member's non-declined answers for `keys` become visible at no cost."""
    for m in sim.members.values():
        if m['arrived_day'] > sim.day: continue
        for k in keys:
            if m['fields'][k] is None and m['field_status'][k] != 'declined':
                m['fields'][k] = copy.deepcopy(m['truth'][k]); m['field_status'][k] = 'observed'
                m['field_observed_day'][k] = sim.day

def true_matching(state, T, variant, maxcard=True, exit_soon=None, drop=(), extra_weight=None):
    """Same-day matching on currently feasible pairs weighted by the TRUE success chance."""
    members, edges = v2.allowed_edges(state)
    G = nx.Graph()
    for a, b in edges:
        i, j = a['member_id'], b['member_id']
        if frozenset((i, j)) in drop: continue
        w = p_win(T[i], T[j], variant, state['day'])
        if exit_soon and (i in exit_soon or j in exit_soon): w *= 2.0
        G.add_edge(i, j, weight=int(w * 1e9) + 1)
    return [tuple(sorted(e)) for e in nx.max_weight_matching(G, maxcardinality=maxcard)], G

def rollout_value(sim, T, variant, first_pairs, horizon, luck):
    """Expected wins of `first_pairs` today plus what the O12 rule would add over the next horizon-1 days,
    in a copy of the simulator: true future arrivals/departures; luck of new introductions resampled."""
    s = copy.deepcopy(sim); s.world['seed'] = luck
    val = sum(p_win(T[a], T[b], variant, s.day) for a, b in first_pairs)
    s.advance([list(p) for p in first_pairs])
    for _ in range(horizon - 1):
        if s.day >= 60: break
        reveal(s, list(HARD) + SOFT)
        pairs, _ = true_matching(s.observe(), T, variant)
        val += sum(p_win(T[a], T[b], variant, s.day) for a, b in pairs)
        s.advance([list(p) for p in pairs])
    return val

def lookahead_pairs(sim, st, T, variant, horizon=10, samples=2, n_alt=2):
    base, G = true_matching(st, T, variant)
    if not base: return base
    cands = {('base',): base}
    nc, _ = true_matching(st, T, variant, maxcard=False)
    cands[('nocard',)] = nc
    weakest = sorted(base, key=lambda e: G[e[0]][e[1]]['weight'])[:n_alt]
    for e in weakest:
        cands[('wait',) + e] = [p for p in base if p != e]                               # hold this pair back
        cands[('swap',) + e] = true_matching(st, T, variant, drop={frozenset(e)})[0]     # best matching without it
    seed = sim.world['seed']
    scores = {k: sum(rollout_value(sim, T, variant, v, horizon, hash((seed, sim.day, s)) & 0x7fffffff)
                     for s in range(samples)) for k, v in cands.items()}
    return cands[max(scores, key=lambda k: (scores[k], k == ('base',)))]

def run(world, arm):
    sim = kit.Simulator(world); T = {m['member_id']: m for m in world['members']}; variant = world['variant']
    from policy import decide as kit_decide
    t0 = time.time()
    for day in range(60):
        if arm in ('O2h',): reveal(sim, HARD)
        if arm in ('O2hs', 'O12', 'O12x', 'O4'): reveal(sim, list(HARD) + SOFT)
        st = sim.observe()
        if arm == 'K': asks = kit_decide({'phase': 'ask', 'state': st, 'memory': None})['asks']
        else: asks = v2.decide({'phase': 'ask', 'state': st, 'memory': None}, R1)['asks']
        sim.resolve_asks(asks); st = sim.observe()
        if arm == 'K': pairs = kit_decide({'phase': 'match', 'state': st, 'memory': None})['pairs']
        elif arm in ('R1', 'O2h', 'O2hs'): pairs = v2.decide({'phase': 'match', 'state': st, 'memory': None}, R1)['pairs']
        elif arm in ('O1', 'O12'): pairs = true_matching(st, T, variant)[0]
        elif arm == 'O1n': pairs = true_matching(st, T, variant, maxcard=False)[0]
        elif arm == 'O12x':
            soon = {i for i, m in T.items() if day < m['exit_day'] <= day + 8}
            pairs = true_matching(st, T, variant, exit_soon=soon)[0]
        elif arm == 'O4': pairs = lookahead_pairs(sim, st, T, variant)
        sim.advance([list(p) for p in pairs])
    arrived = {m['member_id'] for m in sim.observe()['members'] if m['arrived_day'] <= 59}
    ew = sum(p_win(T[i['user_a']], T[i['user_b']], variant, i['assigned_day']) for i in sim.introductions)
    for _ in range(40): sim.advance([])
    res = sim.metrics(); n = max(1, len(arrived))
    served = {u for i in sim.introductions for u in (i['user_a'], i['user_b'])}
    return dict(expected_wins=100 * ew / n, msmi=100 * res['mutual_second_meeting_intention'] / n,
                mutual=100 * res['mutual_acceptances'] / n, intros=res['assignments'],
                coverage=len(served & arrived) / n, ask_cost=res['ask_cost'], secs=round(time.time() - t0, 1))

if __name__ == '__main__':
    first, count, variant, arms = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4].split(',')
    for seed in range(first, first + count):
        world = kit.generate(seed, 200, 'headroom', variant)
        for arm in arms:
            print(json.dumps(dict(seed=seed, variant=variant, policy=arm, **run(world, arm))), flush=True)

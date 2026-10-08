"""Scorer v2 policy (8 Oct). Uses ONLY the observable request (state) and the kit's public eligibility().

What is new compared with prototype_policy.py (see SCORER.md v2/v3):
  - target = the whole journey: score(A,B) = P(A yes) * P(B yes) * rA^2 * rB^2   (r = reply habit, needed twice)
  - per-person reply habit r ~ Beta(prior) + that person's answered / ignored messages
  - per-person pickiness: the person's own yes-rate, shrunk hard toward the base rate
  - no ageing by default (GAMMA = 1, proof in SCORER.md)
  - Thompson draws for every uncertain number (or posterior means, for diagnostics)
  - optional soft-field asks with the budget left after dealbreaker asks (ASKER.md rule 4)
Every number that can be tuned lives in KNOBS and can be overridden through cfg.
"""
import math, random
import networkx as nx
from kit import eligibility, HARD, baseline_asks

FIELDS = ['relationship_goal', 'relationship_pace', 'lifestyle', 'conversations']
KNOBS = dict(
    prior_w={'relationship_goal': (0.71, -0.37), 'relationship_pace': (0.33, -0.35),   # offline fit, development
             'lifestyle': (0.23, -0.30), 'conversations': (0.07, -0.19)},             # log-odds shift (same, different)
    base_rate=0.48,          # P(yes | replied), measured
    k_field=40,              # pseudo-replies behind each field prior (the "normaliser")
    k_base=20,               # pseudo-replies behind the base rate
    reply_prior=0.76,        # P(reply), measured
    k_reply=10,              # pseudo-messages behind each person's reply habit
    k_pick=10,               # pseudo-replies behind each person's pickiness
    reply_power=2,           # reply habit counts twice in the journey
    use_reply=True, use_pick=True,
    gamma=1.0,               # ageing per day (1 = none)
    mode='thompson',         # 'thompson' | 'mean'
    u_new=1.5, u_deg=0.5,    # urgency: never introduced, few options
    soft_asks=False, soft_min_options=1,   # tuning round 1: 1 beats 2 on AUC (+0.024 ± 0.006)
    soft_order=['relationship_goal', 'relationship_pace', 'lifestyle', 'conversations'],
)

sig = lambda z: 1 / (1 + math.exp(-z))
logit = lambda p: math.log(max(1e-6, min(1 - 1e-6, p)) / (1 - max(1e-6, min(1 - 1e-6, p))))
complete = lambda m: all(m['fields'][k] is not None for k in HARD)

def field_state(a, b, f):
    x, y = a['fields'][f], b['fields'][f]
    return None if x is None or y is None else ('same' if x == y else 'diff')

def _draw(rng, a, b, mode):
    return rng.betavariate(a, b) if mode == 'thompson' else a / (a + b)

def make_scorer(state, K, rng):
    """Returns journey(a, b) and p_yes(a, b) built from today's observable history."""
    M = {m['member_id']: m for m in state['members']}
    intro = {i['introduction_id']: i for i in state['introductions']}
    cell, base = {}, [0.0, 0.0]
    replied, ignored, pyes, pno = {}, {}, {}, {}
    for e in state['feedback']:
        if e['event'] not in ('introduction_response', 'second_meeting_intention'): continue
        me = e['member_id']; w = K['gamma'] ** max(0, state['day'] - e['observed_day'])
        if e['value'] is None: ignored[me] = ignored.get(me, 0) + w; continue
        replied[me] = replied.get(me, 0) + w
        if e['event'] != 'introduction_response': continue
        i = intro[e['introduction_id']]; other = i['user_b'] if i['user_a'] == me else i['user_a']
        y = e['value'] == 'yes'
        base[0 if y else 1] += w
        (pyes if y else pno)[me] = (pyes if y else pno).get(me, 0) + w
        if me in M and other in M:
            for f in FIELDS:
                s = field_state(M[me], M[other], f)
                if s: c = cell.setdefault((f, s), [0.0, 0.0]); c[0 if y else 1] += w
    mode = K['mode']
    b0 = _draw(rng, K['base_rate'] * K['k_base'] + base[0], (1 - K['base_rate']) * K['k_base'] + base[1], mode)
    shift = {}
    for f, (ws, wd) in K['prior_w'].items():
        for s, w in (('same', ws), ('diff', wd)):
            p0 = sig(logit(K['base_rate']) + w); y, n = cell.get((f, s), (0, 0))
            th = _draw(rng, p0 * K['k_field'] + y, (1 - p0) * K['k_field'] + n, mode)
            shift[f, s] = logit(th) - logit(K['base_rate'])
    cache_r, cache_p = {}, {}
    def reply(i):
        if i not in cache_r:
            cache_r[i] = _draw(rng, K['reply_prior'] * K['k_reply'] + replied.get(i, 0),
                               (1 - K['reply_prior']) * K['k_reply'] + ignored.get(i, 0), mode)
        return cache_r[i]
    def pick(i):   # log-odds shift for this person's own tendency to say yes
        if i not in cache_p:
            th = _draw(rng, b0 * K['k_pick'] + pyes.get(i, 0), (1 - b0) * K['k_pick'] + pno.get(i, 0), mode)
            cache_p[i] = logit(th) - logit(b0)
        return cache_p[i]
    def p_yes(x, y):
        z = logit(b0) + sum(shift[f, s] for f in FIELDS for s in [field_state(x, y, f)] if s)
        if K['use_pick']: z += pick(x['member_id'])
        return sig(z)
    def journey(a, b):
        v = p_yes(a, b) * p_yes(b, a)
        if K['use_reply']: v *= (reply(a['member_id']) * reply(b['member_id'])) ** K['reply_power']
        return v
    return journey, p_yes

def allowed_edges(state):
    members = [m for m in state['members'] if m['available'] and complete(m)]
    past = {frozenset((i['user_a'], i['user_b'])) for i in state['introductions']}
    return members, [(a, b) for i, a in enumerate(members) for b in members[i + 1:]
                     if frozenset((a['member_id'], b['member_id'])) not in past and eligibility(a, b)['status'] == 'feasible']

def ask(state, K):
    asks = baseline_asks(state)                           # dealbreaker bundles, kit order (order matters <= 1%)
    left = state['ask_budget_remaining'] - 3 * len(asks)
    if not K['soft_asks'] or left <= 0: return asks
    _, edges = allowed_edges(state)
    deg, by_id = {}, {}
    for a, b in edges:
        for u in (a, b): deg[u['member_id']] = deg.get(u['member_id'], 0) + 1; by_id[u['member_id']] = u
    cands = sorted((i for i, d in deg.items() if d >= K['soft_min_options']), key=lambda i: -deg[i])
    for f in K['soft_order']:                             # goal for everyone first, then pace, ...
        for i in cands:
            if left <= 0: return asks
            if by_id[i]['fields'][f] is None and by_id[i]['field_status'][f] != 'declined':
                asks.append({'member_id': i, 'field': f}); left -= 1
    return asks

def match(state, K, rng):
    members, edges = allowed_edges(state)
    if not edges: return []
    journey, _ = make_scorer(state, K, rng)
    introduced = {u for i in state['introductions'] for u in (i['user_a'], i['user_b'])}
    deg = {}
    for a, b in edges:
        for u in (a, b): deg[u['member_id']] = deg.get(u['member_id'], 0) + 1
    G = nx.Graph()
    for a, b in edges:
        w = journey(a, b)
        for u in (a, b):
            if u['member_id'] not in introduced: w *= K['u_new']
            w *= 1 + K['u_deg'] / deg[u['member_id']]
        G.add_edge(a['member_id'], b['member_id'], weight=int(w * 1e9) + 1)
    M = {m['member_id']: m for m in members}
    return [sorted([u, v]) for u, v in nx.max_weight_matching(G, maxcardinality=True)
            if eligibility(M[u], M[v])['status'] == 'feasible']

def decide(request, cfg=None):
    K = {**KNOBS, **(cfg or {})}
    state = request['state']; memory = request.get('memory') or {}
    rng = random.Random(7919 * state['day'] + (1 if request['phase'] == 'ask' else 2))
    if request['phase'] == 'ask': return {'asks': ask(state, K), 'memory': memory}
    return {'pairs': match(state, K, rng), 'memory': memory}

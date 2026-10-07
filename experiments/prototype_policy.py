"""Prototype policy assembled from the research pieces (see RESEARCH.md / SKELETON.md).
Uses ONLY the observable request (state + memory) and the kit's public eligibility() checker.
Each piece can be switched off for ablations via the `cfg` dict.

Pieces and where they came from:
  asker   - value of information (lecture slide 21) + donor imputation (user idea, tested in asker_prediction.py)
            + 'help people with few options' (friend's appendix §7 floor)
  scorer  - logistic weights fitted offline on simulator packets (soft_weights.py) used as a prior,
            discounted Beta counts updated from replies (SMPyBandits DiscountedBeta),
            Thompson draw (lecture slides 19-20; Chapelle & Li 2011), gentle updates (friend's §14 EPV)
  urgency - floor >= 1 / coverage boost (friend's §7), waiting-time aging (user idea)
  matcher - maximum-weight matching, max cardinality, integer weights (networkx blossom; funnel argument §2)
  safety  - official eligibility() re-check before returning
"""
import math, random
import networkx as nx
from kit import eligibility, HARD

FIELDS = ['relationship_goal', 'relationship_pace', 'lifestyle', 'conversations']
# Offline fit (development variant, soft_weights.py): log-odds shift for match / differ
PRIOR_W = {'relationship_goal': (0.71, -0.37), 'relationship_pace': (0.33, -0.35),
           'lifestyle': (0.23, -0.30), 'conversations': (0.07, -0.19)}
PRIOR_STRENGTH = 40      # pseudo-observations behind each prior (gentle online updates)
GAMMA = 0.98             # daily discount of old replies
DEFAULT = dict(asker='voi', scorer='thompson', urgency=True, matcher='maxweight')

sig = lambda z: 1 / (1 + math.exp(-z))
logit = lambda p: math.log(p / (1 - p))
complete = lambda m: all(m['fields'][k] is not None for k in HARD)
refused = lambda m: any(m['field_status'][k] == 'declined' for k in HARD)

def state_of(a, b, f):
    x, y = a['fields'][f], b['fields'][f]
    return None if x is None or y is None else ('match' if x == y else 'differ')

# ---------------------------------------------------------------- scorer
def reply_counts(state):
    """Discounted yes/no counts per (field, match/differ) from replies observed so far."""
    M = {m['member_id']: m for m in state['members']}
    intro = {i['introduction_id']: i for i in state['introductions']}
    cnt, base = {}, [0.0, 0.0]
    for e in state['feedback']:
        if e['event'] != 'introduction_response' or e['value'] is None: continue
        i = intro[e['introduction_id']]; me = e['member_id']; other = i['user_b'] if i['user_a'] == me else i['user_a']
        if me not in M or other not in M: continue
        w = GAMMA ** max(0, state['day'] - e['observed_day']); y = e['value'] == 'yes'
        base[0 if y else 1] += w
        for f in FIELDS:
            s = state_of(M[me], M[other], f)
            if s:
                c = cnt.setdefault((f, s), [0.0, 0.0]); c[0 if y else 1] += w
    return cnt, base

def make_scorer(state, mode, rng):
    cnt, base = reply_counts(state)
    b0 = (base[0] + 20) / (sum(base) + 40)                        # base yes-rate, prior 0.5
    shift = {}
    for f, (wm, wd) in PRIOR_W.items():
        for s, w in (('match', wm), ('differ', wd)):
            p0 = sig(logit(0.49) + w); a = p0 * PRIOR_STRENGTH; b = (1 - p0) * PRIOR_STRENGTH
            y, n = cnt.get((f, s), [0, 0])
            if mode == 'fixed': theta = p0
            elif mode == 'mean': theta = (a + y) / (a + b + y + n)
            else: theta = rng.betavariate(a + y, b + n)              # Thompson draw
            shift[f, s] = logit(min(max(theta, 1e-4), 1 - 1e-4)) - logit(b0 if mode != 'fixed' else 0.49)
    def p_yes(x, y):
        z = logit(b0 if mode != 'fixed' else 0.49)
        for f in FIELDS:
            s = state_of(x, y, f)
            if s: z += shift[f, s]
        return sig(z)
    return p_yes

# ---------------------------------------------------------------- asker
def ask(state, cfg, rng):
    budget = state['ask_budget_remaining'] // 3
    members = state['members']
    pending = [m for m in members if m['available'] and not complete(m) and not refused(m)]
    if not pending or budget == 0: return []
    if cfg['asker'] == 'baseline':
        return [{'member_id': m['member_id'], 'field': 'constraints'} for m in pending[:budget]]
    active = [m for m in members if m['available'] and complete(m)]
    donors = {}
    for m in members:
        if complete(m): donors.setdefault(m['gender'], []).append(m)
    past = {frozenset((i['user_a'], i['user_b'])) for i in state['introductions']}
    deg = {a['member_id']: 0 for a in active}
    for i, a in enumerate(active):
        for b in active[i + 1:]:
            if frozenset((a['member_id'], b['member_id'])) not in past and eligibility(a, b)['status'] == 'feasible':
                deg[a['member_id']] += 1; deg[b['member_id']] += 1
    K = 6; scores = []
    for p in pending:
        pool = donors.get(p['gender']) or [m for v in donors.values() for m in v]
        if not pool: scores.append((0, p['member_id'])); continue
        val = 0.0
        for _ in range(K):
            d = rng.choice(pool)
            q = dict(p); q['fields'] = {k: (p['fields'][k] if p['fields'][k] is not None else d['fields'][k]) for k in p['fields']}
            for a in active:
                if eligibility(q, a)['status'] == 'feasible':
                    val += 1 + 1 / (1 + deg[a['member_id']])   # partner value + extra for people with few options
        scores.append((val / K, p['member_id']))
    scores.sort(reverse=True)
    return [{'member_id': i, 'field': 'constraints'} for _, i in scores[:budget]]

# ---------------------------------------------------------------- matcher
def match(state, cfg, rng):
    members = [m for m in state['members'] if m['available'] and complete(m)]
    past = {frozenset((i['user_a'], i['user_b'])) for i in state['introductions']}
    introduced = {u for i in state['introductions'] for u in (i['user_a'], i['user_b'])}
    edges = [(a, b) for i, a in enumerate(members) for b in members[i + 1:]
             if frozenset((a['member_id'], b['member_id'])) not in past and eligibility(a, b)['status'] == 'feasible']
    if not edges: return []
    if cfg['matcher'] == 'greedy_baseline':
        from kit import baseline_match
        return baseline_match(state)
    p_yes = make_scorer(state, cfg['scorer'], rng)
    deg = {}
    for a, b in edges:
        for u in (a, b): deg[u['member_id']] = deg.get(u['member_id'], 0) + 1
    G = nx.Graph()
    for a, b in edges:
        w = p_yes(a, b) * p_yes(b, a)                              # both say yes (failure-aware, kidney_solver idea)
        if cfg['urgency']:
            for u in (a, b):
                uid = u['member_id']
                if uid not in introduced: w *= 1.5                # floor >= 1 / coverage (friend §7)
                w *= 1 + 0.5 / deg[uid]                           # few options -> act now (Akbarpour et al.)
        G.add_edge(a['member_id'], b['member_id'], weight=int(w * 1e6) + 1)   # integer weights (networkx docs)
    M = {m['member_id']: m for m in members}
    pairs = []
    for u, v in nx.max_weight_matching(G, maxcardinality=True):
        if eligibility(M[u], M[v])['status'] == 'feasible':          # safety re-check
            pairs.append(sorted([u, v]))
    return pairs

def decide(request, cfg=None):
    cfg = {**DEFAULT, **(cfg or {})}
    state = request['state']; memory = request.get('memory') or {}
    rng = random.Random(7919 * state['day'] + (1 if request['phase'] == 'ask' else 2))
    if request['phase'] == 'ask':
        return {'asks': ask(state, cfg, rng), 'memory': memory}
    return {'pairs': match(state, cfg, rng), 'memory': memory}

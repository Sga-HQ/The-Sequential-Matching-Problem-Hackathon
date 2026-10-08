"""Test scorer v2 on NEW worlds against the kit greedy baseline and the old prototype.
Same protocol as evaluate.py (60 decision days + 40 follow-up). Run from the organiser kit folder:
    python test_scorer_v2.py <first_seed> <n_seeds> <variant> > out.jsonl
Extra, low-noise metric: expected_wins = sum over introduced pairs of their exact win chance from the
simulator's formula (hidden truth used ONLY here, for measurement). Diagnostics for each scorer: AUC and
calibration of its predicted P(yes) at decision time against the replies that came back.
"""
import json, math, random, sys
sys.path.insert(0, '.')
import kit
import prototype_policy as old
import scorer_v2_policy as v2

sig = lambda z: 1 / (1 + math.exp(-z))
NODES = [(-2.0201828, 0.0199532), (-0.9585725, 0.3936193), (0.0, 0.9453087), (0.9585725, 0.3936193), (2.0201828, 0.0199532)]
def weights(variant):
    if variant == 'shift': return {'relationship_goal': .25, 'relationship_pace': .8, 'lifestyle': -.25, 'conversations': .5}
    return {'relationship_goal': .7, 'relationship_pace': .4, 'lifestyle': .25, 'conversations': .2}

def p_win(a, b, variant, day):
    ta, tb = a['truth'], b['truth']; W = weights(variant)
    fit = sum(w * (1 if ta[k] == tb[k] else -.5) for k, w in W.items())
    drift = -.5 if variant == 'drift' and day >= 35 else 0
    goal = .4 * (ta['relationship_goal'] == tb['relationship_goal'])
    tot = 0
    for x, wt in NODES:
        s = x * math.sqrt(2) * .45
        acc = a['response_rate'] * b['response_rate'] * sig(-.25 + a['bias'] + fit + s + drift) * sig(-.25 + b['bias'] + fit + s + drift)
        sec = (a['response_rate'] * .6 * sig(.15 + a['second_bias'] + s + goal)) * (b['response_rate'] * .6 * sig(.15 + b['second_bias'] + s + goal))
        tot += wt / math.sqrt(math.pi) * acc * .78 * sec
    return tot   # (ignores the delayed scenario's 30-day date rule: a small overestimate there, same for all policies)

def auc(s, y):
    pos = sum(y); neg = len(y) - pos
    if not pos or not neg: return float('nan')
    order = sorted(range(len(s)), key=lambda i: s[i]); rank = [0] * len(s)
    for r, i in enumerate(order): rank[i] = r + 1
    return (sum(rank[i] for i in range(len(y)) if y[i]) - pos * (pos + 1) / 2) / (pos * neg)

POLICIES = {
    'K  kit greedy baseline':         ('kit', None),
    'P  old prototype (A4)':          ('old', dict(asker='voi', scorer='thompson', urgency=True)),
    'S2 scorer v2':                   ('v2', dict(soft_asks=False)),
    'S3 scorer v2 + soft-field asks': ('v2', dict(soft_asks=True)),
}

def run(world, kind, cfg):
    from policy import decide as kit_decide
    sim = kit.Simulator(world); T = {m['member_id']: m for m in world['members']}
    preds = {}   # (member, intro day, other) -> predicted P(yes) by this policy's scorer (posterior mean)
    unknown = [0, 0]
    for day in range(60):
        st = sim.observe()
        if kind == 'kit': asks = kit_decide({'phase': 'ask', 'state': st, 'memory': None})['asks']
        elif kind == 'old': asks = old.decide({'phase': 'ask', 'state': st, 'memory': None}, cfg)['asks']
        else: asks = v2.decide({'phase': 'ask', 'state': st, 'memory': None}, cfg)['asks']
        sim.resolve_asks(asks); st = sim.observe()
        if kind == 'kit': pairs = kit_decide({'phase': 'match', 'state': st, 'memory': None})['pairs']
        elif kind == 'old': pairs = old.decide({'phase': 'match', 'state': st, 'memory': None}, cfg)['pairs']
        else: pairs = v2.decide({'phase': 'match', 'state': st, 'memory': None}, cfg)['pairs']
        if pairs:
            M = {m['member_id']: m for m in st['members']}
            if kind == 'v2': _, p_yes = v2.make_scorer(st, {**v2.KNOBS, **cfg, 'mode': 'mean'}, random.Random(0))
            else: p_yes = old.make_scorer(st, 'mean', random.Random(0))
            for a, b in pairs:
                for x, y in ((a, b), (b, a)):
                    preds[(x, day, y)] = p_yes(M[x], M[y])
                    for f in v2.FIELDS: unknown[0] += v2.field_state(M[x], M[y], f) is None; unknown[1] += 1
        sim.advance(pairs)
    arrived = {m['member_id'] for m in sim.observe()['members'] if m['arrived_day'] <= 59}
    ew = sum(p_win(T[i['user_a']], T[i['user_b']], world['variant'], i['assigned_day']) for i in sim.introductions)
    for _ in range(40): sim.advance([])
    res = sim.metrics(); n = max(1, len(arrived))
    I = {i['introduction_id']: i for i in sim.introductions}
    s, y = [], []
    for e in sim.receive_feedback():
        if e['event'] != 'introduction_response' or e['value'] is None: continue
        i = I[e['introduction_id']]; other = i['user_b'] if i['user_a'] == e['member_id'] else i['user_a']
        k = (e['member_id'], i['assigned_day'], other)
        if k in preds: s.append(preds[k]); y.append(e['value'] == 'yes')
    served = {u for i in sim.introductions for u in (i['user_a'], i['user_b'])}
    return dict(msmi=100 * res['mutual_second_meeting_intention'] / n, expected_wins=100 * ew / n,
                mutual=100 * res['mutual_acceptances'] / n, coverage=len(served & arrived) / n,
                intros=res['assignments'], ask_cost=res['ask_cost'],
                auc=auc(s, y), pred_mean=sum(s) / max(1, len(s)), yes_rate=sum(y) / max(1, len(y)), n_replies=len(y),
                unknown_share=unknown[0] / max(1, unknown[1]))

if __name__ == '__main__':
    first, count, variant = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    for seed in range(first, first + count):
        world = kit.generate(seed, 200, 'scorer_v2', variant)
        for name, (kind, cfg) in POLICIES.items():
            print(json.dumps(dict(seed=seed, variant=variant, policy=name, **run(world, kind, cfg))), flush=True)

"""Ablation: add research pieces one at a time and measure against the kit's greedy baseline.
Same episode protocol and metrics as the organiser evaluate.py (60 decision days + 40 follow-up),
run in-process for speed. Run from the organiser kit folder:
    python run_ablation.py <first_seed> <n_seeds> <variant> > out.jsonl
"""
import json, sys, statistics
sys.path.insert(0, '.')
import kit
from prototype_policy import decide

POLICIES = {
    'A0 kit greedy baseline':           dict(asker='baseline', matcher='greedy_baseline'),
    'A1 + max-weight matching':         dict(asker='baseline', scorer='fixed', urgency=False),
    'A2 + value-of-information asker':  dict(asker='voi', scorer='fixed', urgency=False),
    'A3 + coverage/urgency boost':      dict(asker='voi', scorer='fixed', urgency=True),
    'A4 + Thompson online learning':    dict(asker='voi', scorer='thompson', urgency=True),
}

def episode(world, cfg):
    sim = kit.Simulator(world)
    for _ in range(60):
        r = decide({'phase': 'ask', 'state': sim.observe(), 'memory': None}, cfg); sim.resolve_asks(r['asks'])
        r = decide({'phase': 'match', 'state': sim.observe(), 'memory': None}, cfg); sim.advance(r['pairs'])
    arrived = {m['member_id'] for m in sim.observe()['members'] if m['arrived_day'] <= 59}
    for _ in range(40): sim.advance([])
    res = sim.metrics(); n = max(1, len(arrived))
    served = {u for i in sim.introductions for u in (i['user_a'], i['user_b'])}
    return dict(msmi=100 * res['mutual_second_meeting_intention'] / n, mutual=100 * res['mutual_acceptances'] / n,
                coverage=len(served & arrived) / n, intros=res['assignments'], ask_cost=res['ask_cost'])

if __name__ == '__main__':
    first, count, variant = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    for seed in range(first, first + count):
        world = kit.generate(seed, 200, 'ablation', variant)
        for name, cfg in POLICIES.items():
            print(json.dumps(dict(seed=seed, variant=variant, policy=name, **episode(world, cfg))), flush=True)

"""How much could a better asker help? Upper bounds using hidden truth (for measurement ONLY, never in a policy).
Askers compared, all with the same matcher (prototype A3 settings: max-weight + urgency, fixed scorer):
  random     - 4 random Pending people per day
  baseline   - kit order (first 4 Pending)
  ours       - value-of-information with donor imputation (prototype)
  oracle     - top 4 by TRUE number of partners unlocked (cheating upper bound for a 4-per-day asker)
  unlimited  - every Pending person answered every day (cheating upper bound for asking at all)
Run from organiser kit folder: python asker_bounds.py <first_seed> <n> <variant>
"""
import json, sys, copy, random
sys.path.insert(0, '.')
import kit
from prototype_policy import ask as voi_ask, match, complete, refused

CFG = dict(asker='voi', scorer='fixed', urgency=True, matcher='maxweight')

def true_unlocks(sim, p, active):
    t = copy.deepcopy(p); t['fields'] = {**p['fields'], **{k: sim.members[p['member_id']]['truth'][k] for k in kit.HARD}}
    return sum(kit.eligibility(t, a)['status'] == 'feasible' for a in active)

def episode(world, mode, seed):
    sim = kit.Simulator(world); rng = random.Random(seed)
    for day in range(60):
        s = sim.observe()
        pend = [m for m in s['members'] if m['available'] and not complete(m) and not refused(m)]
        if mode == 'unlimited':
            for p in pend:                                   # reveal directly, bypassing the 12-point budget (bound only)
                m = sim.members[p['member_id']]
                for k in kit.HARD:
                    if m['field_status'][k] != 'declined':
                        m['fields'][k] = m['truth'][k]; m['field_status'][k] = 'observed'; m['field_observed_day'][k] = day
            asks = []
        elif mode == 'random':
            asks = [{'member_id': p['member_id'], 'field': 'constraints'} for p in rng.sample(pend, min(4, len(pend)))]
        elif mode == 'baseline':
            asks = kit.baseline_asks(s)
        elif mode == 'ours':
            asks = voi_ask(s, CFG, random.Random(day))
        elif mode == 'oracle':
            active = [m for m in s['members'] if m['available'] and complete(m)]
            ranked = sorted(pend, key=lambda p: -true_unlocks(sim, p, active))
            asks = [{'member_id': p['member_id'], 'field': 'constraints'} for p in ranked[:4]]
        sim.resolve_asks(asks)
        s = sim.observe(); sim.advance(match(s, CFG, random.Random(1000 + day)))
    arrived = {m['member_id'] for m in sim.observe()['members'] if m['arrived_day'] <= 59}
    for _ in range(40): sim.advance([])
    r = sim.metrics(); n = len(arrived)
    served = {u for i in sim.introductions for u in (i['user_a'], i['user_b'])}
    return dict(msmi=100 * r['mutual_second_meeting_intention'] / n, mutual=100 * r['mutual_acceptances'] / n,
                coverage=len(served & arrived) / n, intros=r['assignments'])

if __name__ == '__main__':
    first, count, variant = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    for seed in range(first, first + count):
        w = kit.generate(seed, 200, 'ablation', variant)
        for mode in ('random', 'baseline', 'ours', 'oracle', 'unlimited'):
            print(json.dumps(dict(seed=seed, variant=variant, policy=mode, **episode(w, mode, seed))), flush=True)

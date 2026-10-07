"""Can we predict how many allowed partners a Pending person will unlock BEFORE asking?
Method: 'donor imputation' - fill a Pending person's unknown dealbreakers by copying them from random
complete-profile people of the same gender (30 samples), count allowed partners among Active people.
Truth (hidden answers) is used ONLY to score the prediction, never by the method.
Run from the organiser kit folder:  python asker_prediction.py
"""
import sys, copy, random, statistics
sys.path.insert(0, '.')
import kit

def run(seed):
    w = kit.generate(seed, 200, 'ap', 'development'); truth = {m['member_id']: m['truth'] for m in w['members']}
    s = kit.Simulator(w).observe(); M = [m for m in s['members'] if m['available']]
    full = lambda m: all(m['fields'][k] is not None for k in kit.HARD)
    refused = lambda m: any(m['field_status'][k] == 'declined' for k in kit.HARD)
    active = [m for m in M if full(m)]; pending = [m for m in M if not full(m) and not refused(m)]
    donors = {}
    for m in active: donors.setdefault(m['gender'], []).append(m)
    r = random.Random(seed); pred, real = {}, {}
    for p in pending:
        cnt = []
        for _ in range(30):
            q = copy.deepcopy(p); d = r.choice(donors.get(p['gender']) or active)
            for k in kit.HARD:
                if q['fields'][k] is None: q['fields'][k] = d['fields'][k]
            cnt.append(sum(kit.eligibility(q, a)['status'] == 'feasible' for a in active))
        pred[p['member_id']] = statistics.mean(cnt)
        t = copy.deepcopy(p)
        for k in kit.HARD: t['fields'][k] = truth[p['member_id']][k]
        real[p['member_id']] = sum(kit.eligibility(t, a)['status'] == 'feasible' for a in active)
    ids = list(pred)
    top4 = sorted(ids, key=lambda i: -pred[i])[:4]
    rand4 = statistics.mean(statistics.mean(real[i] for i in r.sample(ids, 4)) for _ in range(500))
    best4 = sorted(ids, key=lambda i: -real[i])[:4]
    corr = statistics.correlation([pred[i] for i in ids], [real[i] for i in ids])
    zero_pred = [i for i in ids if pred[i] < 0.5]
    return len(pending), corr, statistics.mean(real[i] for i in top4), rand4, statistics.mean(real[i] for i in best4), sum(real[i] == 0 for i in zero_pred), len(zero_pred)

rows = [run(s) for s in range(301, 311)]
print('seed-avg over 10 worlds (day 0):')
print(f'  pending people per world          {statistics.mean(r[0] for r in rows):.1f}')
print(f'  correlation predicted vs real     {statistics.mean(r[1] for r in rows):.2f}')
print(f'  real partners unlocked, top-4 by prediction  {statistics.mean(r[2] for r in rows):.2f}')
print(f'  real partners unlocked, random 4             {statistics.mean(r[3] for r in rows):.2f}')
print(f'  real partners unlocked, perfect hindsight 4  {statistics.mean(r[4] for r in rows):.2f}')
print(f'  predicted ~0 partners: really 0 in {sum(r[5] for r in rows)} of {sum(r[6] for r in rows)} cases')

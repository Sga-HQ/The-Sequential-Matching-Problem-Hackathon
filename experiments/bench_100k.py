"""Filtering benchmark at 100,000 people (all 11 dealbreakers, both directions).
Run from the organiser kit folder (needs kit.py):  python bench_100k.py
Methods:
  A user_row      - user's idea: for person X, check every other person rule by rule (early exit)
  B blocking      - inverted index by (gender, zone) -> only scan people X could want, then check rest
  C bitmap        - bitmap index: one bitset per answer value, combined with AND (Elasticsearch-style)
  D columnar      - column store: numpy arrays, one vectorised boolean mask per query (analytics-DB style)
"""
import sys, time, random
sys.path.insert(0, '.')
import kit
import numpy as np

N = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
FULL = '--full' in sys.argv
G = ['woman', 'man', 'non_binary']; S = ['weekday_evening', 'weekend_day', 'weekend_evening']
t = time.perf_counter()
P = [m for m in kit.generate(5, N, 'evaluation', 'development')['members'] if all(m['fields'][k] is not None for k in kit.HARD)]
n = len(P); print(f'people generated={N}  with complete dealbreakers={n}  ({time.perf_counter()-t:.1f}s)')
Z = sorted({m['zone'] for m in P} | {z for m in P for z in m['fields']['acceptable_zones']})
SMOKER = lambda f: f['smoking'] in ('yes', 'occasionally')

def ok_rest(x, y):  # rules after gender/zone/age
    fx, fy = x['fields'], y['fields']
    if fx['relationship_structure'] != fy['relationship_structure']: return False
    if {fx['wants_children'], fy['wants_children']} == {'yes', 'no'}: return False
    if not set(fx['schedule']) & set(fy['schedule']): return False
    if fx['partner_smoking'] == 'no_smoking' and SMOKER(fy): return False
    if fy['partner_smoking'] == 'no_smoking' and SMOKER(fx): return False
    if fx['partner_children'] == 'no_children' and fy['has_children']: return False
    if fy['partner_children'] == 'no_children' and fx['has_children']: return False
    return True

# ---- A user_row ----
def A_query(i):
    x = P[i]; fx = x['fields']; out = []
    for j, y in enumerate(P):
        if j == i: continue
        fy = y['fields']
        if y['gender'] not in fx['who_to_meet'] or x['gender'] not in fy['who_to_meet']: continue
        if not (fx['age_min'] <= y['age'] <= fx['age_max'] and fy['age_min'] <= x['age'] <= fy['age_max']): continue
        if y['zone'] not in fx['acceptable_zones'] or x['zone'] not in fy['acceptable_zones']: continue
        if ok_rest(x, y): out.append(j)
    return out

# ---- B blocking ----
def B_build():
    idx = {}
    for j, y in enumerate(P): idx.setdefault((y['gender'], y['zone']), []).append(j)
    return idx
def B_query(i, idx):
    x = P[i]; fx = x['fields']; out = []
    for g in fx['who_to_meet']:
        for z in fx['acceptable_zones']:
            for j in idx.get((g, z), ()):
                if j == i: continue
                y = P[j]; fy = y['fields']
                if x['gender'] not in fy['who_to_meet'] or x['zone'] not in fy['acceptable_zones']: continue
                if not (fx['age_min'] <= y['age'] <= fx['age_max'] and fy['age_min'] <= x['age'] <= fy['age_max']): continue
                if ok_rest(x, y): out.append(j)
    return sorted(out)

# ---- C bitmap ----
def C_build():
    col = {}
    def add(k, j): col[k] = col.get(k, 0) | (1 << j)
    for j, y in enumerate(P):
        f = y['fields']
        add(('g', y['gender']), j); add(('z', y['zone']), j); add(('age', y['age']), j)
        for g in f['who_to_meet']: add(('wants', g), j)
        for z in f['acceptable_zones']: add(('acc', z), j)
        for s in f['schedule']: add(('sch', s), j)
        add(('st', f['relationship_structure']), j); add(('wc', f['wants_children']), j)
        if SMOKER(f): add(('smoker',), j)
        if f['partner_smoking'] == 'no_smoking': add(('nosmoke',), j)
        if f['has_children']: add(('kids',), j)
        if f['partner_children'] == 'no_children': add(('nokids',), j)
    # "accepts age a" columns built as prefix sets: amin<=a and amax>=a
    for a in range(18, 66):
        col[('accage', a)] = 0
    for j, y in enumerate(P):
        f = y['fields']
        for a in range(f['age_min'], f['age_max'] + 1): col[('accage', a)] |= (1 << j)
    return col
def C_query(i, col):
    x = P[i]; f = x['fields']; c = lambda k: col.get(k, 0)
    m = 0
    for g in f['who_to_meet']: m |= c(('g', g))
    zz = 0
    for z in f['acceptable_zones']: zz |= c(('z', z))
    aa = 0
    for a in range(f['age_min'], f['age_max'] + 1): aa |= c(('age', a))
    m &= zz & aa & c(('wants', x['gender'])) & c(('acc', x['zone'])) & c(('accage', x['age'])) & c(('st', f['relationship_structure']))
    if f['wants_children'] == 'yes': m &= ~c(('wc', 'no'))
    if f['wants_children'] == 'no': m &= ~c(('wc', 'yes'))
    sc = 0
    for s in f['schedule']: sc |= c(('sch', s))
    m &= sc
    if f['partner_smoking'] == 'no_smoking': m &= ~c(('smoker',))
    if SMOKER(f): m &= ~c(('nosmoke',))
    if f['partner_children'] == 'no_children': m &= ~c(('kids',))
    if f['has_children']: m &= ~c(('nokids',))
    m &= ~(1 << i); out = []
    while m:
        low = m & -m; out.append(low.bit_length() - 1); m ^= low
    return out

# ---- D columnar ----
def D_build():
    gi = {g: k for k, g in enumerate(G)}; zi = {z: k for k, z in enumerate(Z)}; si = {s: k for k, s in enumerate(S)}
    A = lambda fn, dt=np.int32: np.array([fn(y) for y in P], dtype=dt)
    return dict(
        gender=A(lambda y: 1 << gi[y['gender']]), zone=A(lambda y: 1 << zi[y['zone']], np.int64), age=A(lambda y: y['age']),
        wants=A(lambda y: sum(1 << gi[g] for g in y['fields']['who_to_meet'])),
        acc=A(lambda y: sum(1 << zi[z] for z in y['fields']['acceptable_zones']), np.int64),
        amin=A(lambda y: y['fields']['age_min']), amax=A(lambda y: y['fields']['age_max']),
        st=A(lambda y: y['fields']['relationship_structure'] == 'monogamous'),
        wc=A(lambda y: {'yes': 1, 'no': 2, 'unsure': 0}[y['fields']['wants_children']]),
        sch=A(lambda y: sum(1 << si[s] for s in y['fields']['schedule'])),
        smoker=A(lambda y: SMOKER(y['fields']), bool), nosmoke=A(lambda y: y['fields']['partner_smoking'] == 'no_smoking', bool),
        kids=A(lambda y: bool(y['fields']['has_children']), bool), nokids=A(lambda y: y['fields']['partner_children'] == 'no_children', bool))
def D_query(i, d):
    m = ((d['gender'] & d['wants'][i]) > 0) & ((d['wants'] & d['gender'][i]) > 0)
    m &= ((d['zone'] & d['acc'][i]) > 0) & ((d['acc'] & d['zone'][i]) > 0)
    m &= (d['age'] >= d['amin'][i]) & (d['age'] <= d['amax'][i]) & (d['amin'] <= d['age'][i]) & (d['amax'] >= d['age'][i])
    m &= d['st'] == d['st'][i]
    if d['wc'][i]: m &= (d['wc'] == 0) | (d['wc'] == d['wc'][i])
    m &= (d['sch'] & d['sch'][i]) > 0
    if d['nosmoke'][i]: m &= ~d['smoker']
    if d['smoker'][i]: m &= ~d['nosmoke']
    if d['nokids'][i]: m &= ~d['kids']
    if d['kids'][i]: m &= ~d['nokids']
    m[i] = False
    return np.flatnonzero(m).tolist()

builds = {}
for name, b in [('B', B_build), ('C', C_build), ('D', D_build)]:
    t = time.perf_counter(); builds[name] = b(); builds[name + 't'] = time.perf_counter() - t
q = {'A': lambda i: A_query(i), 'B': lambda i: B_query(i, builds['B']), 'C': lambda i: C_query(i, builds['C']), 'D': lambda i: D_query(i, builds['D'])}
names = {'A': 'user_row (your idea)', 'B': 'blocking index', 'C': 'bitmap index', 'D': 'columnar (numpy)'}

sample = random.Random(1).sample(range(n), 200)
ref = {i: sorted(A_query(i)) for i in sample}
print(f'\nONE NEW ARRIVAL vs everyone (avg over {len(sample)} people), results checked identical to user_row:')
for k in 'ABCD':
    t = time.perf_counter(); same = all(sorted(q[k](i)) == ref[i] for i in sample); dt = (time.perf_counter() - t) / len(sample)
    print(f'  {names[k]:22s} build={builds.get(k+"t",0):6.2f}s  per-arrival={dt*1000:8.2f} ms  identical={same}')
print(f'  avg allowed partners per person: {sum(map(len, ref.values()))/len(ref):.1f}')

if FULL:
    print('\nALL PAIRS (every person queried once):')
    for k in 'DCBA':
        t = time.perf_counter(); tot = sum(len(q[k](i)) for i in range(n)) // 2
        print(f'  {names[k]:22s} pairs={tot}  time={time.perf_counter()-t:.1f}s', flush=True)

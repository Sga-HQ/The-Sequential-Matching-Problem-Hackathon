# Benchmark: user 1/0-row idea vs bitsets vs official checker (all 11 dealbreakers).
# Run from the organiser kit folder (needs kit.py): python experiments/bench_filtering.py
import sys, time, itertools, random; sys.path.insert(0,'.')
import kit
H=kit.HARD
G=['woman','man','non_binary']; SCH=['weekday_evening','weekend_day','weekend_evening']
def full(m): return all(m['fields'][k] is not None for k in H)

# ---------- A) USER'S IDEA: for new person X, a 1/0 row per dealbreaker for every other person ----------
def row(x,y):
    fx,fy=x['fields'],y['fields']
    return {
     'gender':   int(y['gender'] in fx['who_to_meet'] and x['gender'] in fy['who_to_meet']),
     'age':      int(fx['age_min']<=y['age']<=fx['age_max'] and fy['age_min']<=x['age']<=fy['age_max']),
     'zone':     int(y['zone'] in fx['acceptable_zones'] and x['zone'] in fy['acceptable_zones']),
     'smoking':  int(not(fx['partner_smoking']=='no_smoking' and fy['smoking'] in('yes','occasionally')) and not(fy['partner_smoking']=='no_smoking' and fx['smoking'] in('yes','occasionally'))),
     'children': int(not(fx['partner_children']=='no_children' and fy['has_children']) and not(fy['partner_children']=='no_children' and fx['has_children'])),
     'plans':    int({fx['wants_children'],fy['wants_children']}!={'yes','no'}),
     'structure':int(fx['relationship_structure']==fy['relationship_structure']),
     'schedule': int(bool(set(fx['schedule'])&set(fy['schedule']))),
    }
def user_idea(M):
    out=set()
    for i,x in enumerate(M):
        for y in M[i+1:]:
            if all(row(x,y).values()): out.add((x['member_id'],y['member_id']))
    return out
# A2) same idea with early exit (stop at first 0, most-eliminating rule first)
ORDER=['gender','age','zone','plans','smoking','structure','schedule','children']
def user_idea_fast(M):
    out=set()
    for i,x in enumerate(M):
        fx=x['fields']
        for y in M[i+1:]:
            fy=y['fields']
            if y['gender'] not in fx['who_to_meet'] or x['gender'] not in fy['who_to_meet']: continue
            if not(fx['age_min']<=y['age']<=fx['age_max'] and fy['age_min']<=x['age']<=fy['age_max']): continue
            if y['zone'] not in fx['acceptable_zones'] or x['zone'] not in fy['acceptable_zones']: continue
            if all(row(x,y).values()): out.add((x['member_id'],y['member_id']))
    return out

# ---------- B) BITSETS: one 1/0 column per answer value, combined with AND ----------
def bitsets(M):
    n=len(M); col={}
    def add(key,i): col[key]=col.get(key,0)|(1<<i)
    for i,m in enumerate(M):
        f=m['fields']
        add(('g',m['gender']),i); add(('z',m['zone']),i); add(('age',m['age']),i)
        for g in f['who_to_meet']: add(('wants',g),i)
        for z in f['acceptable_zones']: add(('acc',z),i)
        for s in f['schedule']: add(('sch',s),i)
        add(('struct',f['relationship_structure']),i); add(('wc',f['wants_children']),i)
        add(('smoker',f['smoking'] in('yes','occasionally')),i); add(('nosmokepref',f['partner_smoking']=='no_smoking'),i)
        add(('kids',bool(f['has_children'])),i); add(('nokidspref',f['partner_children']=='no_children'),i)
        for a in range(18,66):
            if f['age_min']<=a<=f['age_max']: add(('accage',a),i)
    c=lambda k: col.get(k,0)
    out=set()
    for i,x in enumerate(M):
        f=x['fields']
        fwd=0
        for g in f['who_to_meet']: fwd|=c(('g',g))
        z=0
        for zz in f['acceptable_zones']: z|=c(('z',zz))
        ag=0
        for a in range(f['age_min'],f['age_max']+1): ag|=c(('age',a))
        cand=fwd & z & ag & c(('wants',x['gender'])) & c(('acc',x['zone'])) & c(('accage',x['age']))
        cand&=c(('struct',f['relationship_structure']))
        if f['wants_children']=='yes': cand&=~c(('wc','no'))
        if f['wants_children']=='no': cand&=~c(('wc','yes'))
        sch=0
        for s in f['schedule']: sch|=c(('sch',s))
        cand&=sch
        if f['partner_smoking']=='no_smoking': cand&=~c(('smoker',True))
        if f['smoking'] in('yes','occasionally'): cand&=~c(('nosmokepref',True))
        if f['partner_children']=='no_children': cand&=~c(('kids',True))
        if f['has_children']: cand&=~c(('nokidspref',True))
        cand>>=i+1; j=i+1
        while cand:
            if cand&1: out.add((x['member_id'],M[j]['member_id']))
            cand>>=1; j+=1
    return out

# ---------- C) OFFICIAL brute force ----------
def official(M):
    return {(a['member_id'],b['member_id']) for i,a in enumerate(M) for b in M[i+1:] if kit.eligibility(a,b)['status']=='feasible'}

for n in (200,1000,3000):
    M=[m for m in kit.generate(101,n,'evaluation','development')['members'] if full(m)]
    res={}
    for name,fn in [('official',official),('user_idea',user_idea),('user_idea_early_exit',user_idea_fast),('bitsets',bitsets)]:
        if n>1000 and name in('official','user_idea'): continue
        t=time.perf_counter(); r=fn(M); res[name]=(r,time.perf_counter()-t)
    ref=res.get('official',res['user_idea_early_exit'])[0]
    print(f'n={n} complete-profile people={len(M)}')
    for k,(r,s) in res.items(): print(f'   {k:22s} pairs={len(r):5d} same_as_ref={r==ref}  time={s:.4f}s')
print('--- bigger pool ---')
M=[m for m in kit.generate(7,10000,'evaluation','development')['members'] if full(m)]
for name,fn in [('user_idea_early_exit',user_idea_fast),('bitsets',bitsets)]:
    t=time.perf_counter(); r=fn(M); print(f'n=10000 people={len(M)} {name:22s} pairs={len(r)} time={time.perf_counter()-t:.3f}s')

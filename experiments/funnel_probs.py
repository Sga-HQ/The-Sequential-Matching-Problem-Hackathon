"""Conditional probabilities along the whole introduction journey, from what the policy can observe.
Kit greedy baseline, development scenario, 30 worlds. Fields = observed values at the end of the run."""
import collections, sys, kit
from policy import decide
V = sys.argv[1] if len(sys.argv) > 1 else 'development'
C = collections.Counter()
def add(key, ok): C[key + ('n',)] += 1; C[key + ('y',)] += bool(ok)
def rate(*key): n = C[key + ('n',)]; return f"{C[key+('y',)]/n:.2f} (n={n})" if n else '-'
state = lambda a, b, f: 'unk' if a['fields'][f] is None or b['fields'][f] is None else ('match' if a['fields'][f] == b['fields'][f] else 'differ')
for seed in range(9300, 9330):
    sim = kit.Simulator(kit.generate(seed, 200, 'fun', V))
    for d in range(60):
        r = decide({'phase': 'ask', 'state': sim.observe(), 'memory': None}); sim.resolve_asks(r['asks'])
        r = decide({'phase': 'match', 'state': sim.observe(), 'memory': None}); sim.advance(r['pairs'])
    for _ in range(40): sim.advance([])
    st = sim.observe(); M = {m['member_id']: m for m in st['members']}
    ev = collections.defaultdict(list)
    for e in st['feedback']: ev[e['introduction_id']].append(e)
    hist = collections.defaultdict(list)   # per person: sequence of (replied, yes)
    for i in sorted(st['introductions'], key=lambda x: x['assigned_day']):
        a, b = M[i['user_a']], M[i['user_b']]; es = ev[i['introduction_id']]
        rs = {e['member_id']: e['value'] for e in es if e['event'] == 'introduction_response'}
        for me, ot in ((a, b), (b, a)):
            v = rs.get(me['member_id']); replied = v is not None
            h = hist[me['member_id']]
            if h:   # conditional on this person's previous introduction
                add(('reply_given_prev', 'prev_replied' if h[-1][0] else 'prev_silent'), replied)
                if replied and h[-1][0]: add(('yes_given_prev', 'prev_yes' if h[-1][1] else 'prev_no'), v == 'yes')
            h.append((replied, v == 'yes'))
            add(('reply',), replied)
            if replied:
                g, p = state(me, ot, 'relationship_goal'), state(me, ot, 'relationship_pace')
                add(('yes',), v == 'yes'); add(('yes_goal', g), v == 'yes'); add(('yes_goal_pace', g, p), v == 'yes')
        both_yes = len(rs) == 2 and all(x == 'yes' for x in rs.values())
        if both_yes:
            d = [e for e in es if e['event'] == 'date_happened']
            add(('date_given_both_yes',), d and d[0]['value'])
            if d and d[0]['value']:
                ss = [e for e in es if e['event'] == 'second_meeting_intention']
                for e in ss:
                    me = M[e['member_id']]; ot = b if me is a else a
                    add(('second_reply',), e['value'] is not None)
                    if e['value'] is not None:
                        add(('second_yes_goal', state(me, ot, 'relationship_goal')), e['value'] == 'yes')
                        add(('second_on_time',), e['occurred_day'] - d[0]['occurred_day'] <= 3)
print('variant', V)
print('P(reply)                          ', rate('reply'))
print('P(reply | replied last time)      ', rate('reply_given_prev', 'prev_replied'))
print('P(reply | silent last time)       ', rate('reply_given_prev', 'prev_silent'))
print('P(yes | replied)                  ', rate('yes'))
print('P(yes | said yes last time)       ', rate('yes_given_prev', 'prev_yes'))
print('P(yes | said no last time)        ', rate('yes_given_prev', 'prev_no'))
for g in ('match', 'differ', 'unk'): print(f'P(yes | goal {g:6s})              ', rate('yes_goal', g))
for g in ('match', 'differ'):
    for p in ('match', 'differ'): print(f'P(yes | goal {g:6s}, pace {p:6s})', rate('yes_goal_pace', g, p))
print('P(date | both yes)                ', rate('date_given_both_yes'))
print('P(2nd answer arrives | date)      ', rate('second_reply'))
for g in ('match', 'differ', 'unk'): print(f'P(2nd yes | date, goal {g:6s})   ', rate('second_yes_goal', g))
print('P(2nd answer on time | answered)  ', rate('second_on_time'))

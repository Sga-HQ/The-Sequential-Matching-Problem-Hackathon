"""Is the low success of day 35-49 introductions about WHO is introduced (composition), or about timing?
Mean exact win chance (hidden values; diagnostic only) and mean reply rate of introduced people, by assignment-day bucket."""
import collections, statistics as st, sys, kit
from policy import decide
from test_scorer_v2 import p_win
B = [(0, 9), (10, 19), (20, 34), (35, 49), (50, 59)]
for V in sys.argv[1:]:
    pw = collections.defaultdict(list); rr = collections.defaultdict(list); bias = collections.defaultdict(list)
    for seed in range(9700, 9720):
        world = kit.generate(seed, 200, 'day', V); T = {m['member_id']: m for m in world['members']}; sim = kit.Simulator(world)
        for d in range(60):
            r = decide({'phase': 'ask', 'state': sim.observe(), 'memory': None}); sim.resolve_asks(r['asks'])
            r = decide({'phase': 'match', 'state': sim.observe(), 'memory': None}); sim.advance(r['pairs'])
        for i in sim.introductions:
            k = next(j for j, (lo, hi) in enumerate(B) if lo <= i['assigned_day'] <= hi)
            a, b = T[i['user_a']], T[i['user_b']]
            pw[k].append(p_win(a, b, V, i['assigned_day'])); rr[k] += [a['response_rate'], b['response_rate']]; bias[k] += [a['bias'], b['bias']]
    print(f'{V:11s} ' + '  '.join(f"d{lo}-{hi}: win {100*st.mean(pw[k]):.2f}% reply {st.mean(rr[k]):.2f} pick {st.mean(bias[k]):+.2f}" for k, (lo, hi) in enumerate(B)))

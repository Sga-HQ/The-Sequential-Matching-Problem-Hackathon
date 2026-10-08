"""Monte Carlo check of the expected-wins formula against the kit simulator itself.
Usage (from the kit folder): PYTHONPATH=<repo>/experiments python pwin_check.py <variant> 200 300
For random pairs, replay the kit's own advance() under many luck seeds and compare mean MSMI with p_win."""
import sys, copy, math, random
sys.path.insert(0, '.')  # kit folder; this file's folder must be on PYTHONPATH
import kit
from test_scorer_v2 import p_win
variant, npairs, nluck = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
rng = random.Random(1); tot_sim = tot_p = 0; n = 0
w = kit.generate(424242, 200, 'chk', variant)
ms = w['members']
for k in range(npairs):
    a, b = rng.sample(ms, 2)
    day = rng.choice([0, 10, 40]) 
    a = dict(a, arrived_day=0, exit_day=10000); b = dict(b, arrived_day=0, exit_day=10000)
    p = p_win(a, b, variant, day); wins = 0
    for L in range(nluck):
        world = dict(w, seed=1000000 + 7919 * k + L, members=[a, b])
        sim = kit.Simulator(world); sim.day = day
        # bypass only the public eligibility gate (outcome code is untouched)
        orig = kit.eligibility; kit.eligibility = lambda x, y: {'status': 'feasible'}
        sim.advance([(a['member_id'], b['member_id'])]); kit.eligibility = orig
        sim.day = 200
        wins += sim.metrics()['mutual_second_meeting_intention']
    tot_sim += wins; tot_p += p * nluck; n += nluck
print(f"{variant:12s} sims={n} simulated_wins={tot_sim} formula_expects={tot_p:.1f} ratio={tot_sim/tot_p:.3f} z={(tot_sim-tot_p)/math.sqrt(tot_p):+.2f}")

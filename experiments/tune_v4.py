"""Experiment 4 (8 Oct night): closed-loop feedback and decision-aware asking, on NEW development seeds 7400+.
R0 = evidence-supported candidate: frozen offline scorecard (posterior means, no online learning, no personal terms),
     matching-margin soft asking, no coverage boost, degree scarcity kept (provisional).
F1 = R0 + population field-effect learning from replies (posterior mean).
F2 = F1 + personal reply-habit and yes-propensity learning (posterior mean, shrinkage 10).
     F1/F2 also log how often learned feedback changes the day's matching vs the frozen scorecard on the same state.
V  = R0 with matching-VOI soft asking.   D0 = R0 without degree scarcity.
Population stage rates (date 0.78, on-time 0.6, ...) are identical for every pair in the simulator, so learning them
online cannot change any ranking; they are therefore not a separate arm.
Run from the kit folder: python tune_v4.py <first> <n> <variant>"""
import json, sys
sys.path.insert(0, '.')
import kit
from test_scorer_v2 import run
FROZEN = dict(k_field=1e6, k_base=1e6, use_reply=False, use_pick=False, mode='mean')
R0 = dict(FROZEN, soft_asks=True, soft_min_options=2, soft_rule='margin', u_new=1.0, u_deg=0.5)
CONFIGS = {
    'K  kit greedy baseline':                         ('kit', None),
    'R0 frozen scorecard + margin asks (candidate)':  ('v2', R0),
    'F1 R0 + population field learning':              ('v2', dict(R0, k_field=40, k_base=20, _compare=FROZEN)),
    'F2 F1 + personal reply/yes learning':            ('v2', dict(R0, k_field=40, k_base=20, use_reply=True, use_pick=True, _compare=FROZEN)),
    'V  R0 with matching-VOI asks':                   ('v2', dict(R0, soft_rule='voi', soft_min_options=1)),
    'D0 R0 without degree scarcity':                  ('v2', dict(R0, u_deg=0.0)),
}
if __name__ == '__main__':
    first, count, variant = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    for seed in range(first, first + count):
        world = kit.generate(seed, 200, 'tune_v4', variant)
        for name, (kind, cfg) in CONFIGS.items():
            print(json.dumps(dict(seed=seed, variant=variant, policy=name, **run(world, kind, cfg))), flush=True)

"""Round 2 of experiments (8 Oct evening), answering the external review: allocation (opportunity cost, no urgency,
no coverage boost), clarification (matching-margin rule), scorer complexity (simple fixed scorecard, posterior mean).
Development seeds 7300+ (NOT a confirmation set). Run from the kit folder: python tune_v3.py <first> <n> <variant>"""
import json, sys
sys.path.insert(0, '.')
import kit
from test_scorer_v2 import run
B = dict(soft_asks=True, soft_min_options=1)
CONFIGS = {
    'K  kit greedy baseline':                      ('kit', None),
    'B  current best (v2 + soft asks 1+)':         ('v2', B),
    'A1 no urgency (pure max-card, max-weight)':   ('v2', {**B, 'u_new': 1.0, 'u_deg': 0.0}),
    'A2 no coverage boost (u_new=1)':              ('v2', {**B, 'u_new': 1.0}),
    'A3 opportunity cost lambda=0.5 (no urgency)': ('v2', {**B, 'u_new': 1.0, 'u_deg': 0.0, 'opt_lambda': 0.5}),
    'C1 matching-margin asker':                    ('v2', {**B, 'soft_min_options': 2, 'soft_rule': 'margin'}),
    'S1 simple fixed scorecard (no learning)':     ('v2', {**B, 'k_field': 1e6, 'k_base': 1e6, 'use_reply': False, 'use_pick': False, 'mode': 'mean'}),
    'S2 posterior mean (no Thompson)':             ('v2', {**B, 'mode': 'mean'}),
}
if __name__ == '__main__':
    first, count, variant = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    for seed in range(first, first + count):
        world = kit.generate(seed, 200, 'tune_v3', variant)
        for name, (kind, cfg) in CONFIGS.items():
            print(json.dumps(dict(seed=seed, variant=variant, policy=name, **run(world, kind, cfg))), flush=True)

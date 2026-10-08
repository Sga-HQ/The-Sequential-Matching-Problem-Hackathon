"""Tuning round 1 for scorer v2 (8 Oct): the user's three levers, one at a time, on NEW worlds (seeds 7200+).
Run from the organiser kit folder: python tune_v2.py <first_seed> <n_seeds> <variant> > out.jsonl"""
import json, sys
sys.path.insert(0, '.')
import kit
from test_scorer_v2 import run
S3 = dict(soft_asks=True)
CONFIGS = {
    'K  kit greedy baseline':                 ('kit', None),
    'S3 v2 + soft asks (as tested)':          ('v2', S3),
    'T1 asks: soft_min_options=1':            ('v2', {**S3, 'soft_min_options': 1}),
    'T2 prior: k_field=12':                   ('v2', {**S3, 'k_field': 12}),
    'T3 pickiness stronger: k_pick=3':        ('v2', {**S3, 'k_pick': 3}),
    'T4 pickiness off':                       ('v2', {**S3, 'use_pick': False}),
    'T5 T1+T2+T3 combined':                   ('v2', {**S3, 'soft_min_options': 1, 'k_field': 12, 'k_pick': 3}),
}
if __name__ == '__main__':
    first, count, variant = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    for seed in range(first, first + count):
        world = kit.generate(seed, 200, 'tune_v2', variant)
        for name, (kind, cfg) in CONFIGS.items():
            print(json.dumps(dict(seed=seed, variant=variant, policy=name, **run(world, kind, cfg))), flush=True)

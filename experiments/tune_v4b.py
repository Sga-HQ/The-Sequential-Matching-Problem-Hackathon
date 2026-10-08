"""Experiment 4b: same seeds as tune_v4 (7400+). R1 = R0 but broad soft asking (anyone with >= 1 option), because the
margin rule lost expected wins in cold start on block 7300. Episodes are deterministic, so R1 pairs with tune_v4's arms."""
import json, sys
sys.path.insert(0, '.')
import kit
from test_scorer_v2 import run
from tune_v4 import R0
CONFIGS = {'R1 frozen scorecard + broad soft asks': ('v2', dict(R0, soft_rule='all', soft_min_options=1))}
if __name__ == '__main__':
    first, count, variant = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    for seed in range(first, first + count):
        world = kit.generate(seed, 200, 'tune_v4', variant)
        for name, (kind, cfg) in CONFIGS.items():
            print(json.dumps(dict(seed=seed, variant=variant, policy=name, **run(world, kind, cfg))), flush=True)

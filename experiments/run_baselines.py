"""Run the kit's other two required baselines (no_asks, random) in-process, same protocol as run_ablation.py,
on the same seeds so results pair with ablation_6000-6039.jsonl (which already has the greedy baseline).
Run from the organiser kit folder:
    python run_baselines.py <first_seed> <n_seeds> <variant> > out.jsonl
"""
import json, sys
sys.path.insert(0, '.')
import kit, policy
from run_ablation import episode

import run_ablation

if __name__ == '__main__':
    first, count, variant = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    for seed in range(first, first + count):
        world = kit.generate(seed, 200, 'ablation', variant)
        for mode in ('no_asks', 'random'):
            run_ablation.decide = lambda req, cfg, m=mode: policy.decide(req, m)
            print(json.dumps(dict(seed=seed, variant=variant, policy=f'B {mode} baseline', **episode(world, None))), flush=True)

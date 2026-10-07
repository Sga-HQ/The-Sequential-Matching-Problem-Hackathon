# Review: Fresher Friend Matching (architecture + mathematical appendix)

Overall: rigorous and honest work. Every number is derived, assumptions are labelled, and the corrections section shows real care. I spot-checked §10.4, §11.2, §12.2, §13.2 and §15.5; the arithmetic is correct. The suggestions below are about modelling choices, not arithmetic errors.

## High impact

### 1. The A/B power analysis (§11) is too optimistic: users are not independent units
- Each user sees 5 suggestions, so the 1,500 impressions are clustered in 300 users. Accept decisions by the same user are correlated (some people accept everything, some nothing).
- Effective sample size = n / design effect, where design effect = 1 + (m − 1)·ICC, m = 5 impressions per user. With a modest ICC of 0.2: 1 + 4 × 0.2 = 1.8, so 750 per arm behaves like ~417. That is barely above the 356 needed, not "powered with margin".
- Bigger issue: **interference**. A recommendation links two users. If u is in treatment and v in control, the pair belongs to both arms, which breaks the "no interference" assumption behind the two-proportion test.
- Fix: randomise by **cluster** (hostel block, section or branch) so most pairs fall inside one arm, and recompute power with the design effect. Alternatively, alternate whole cohort-weeks between policies (switchback design).

### 2. Fit weights on the accept proxy instead of hand-setting them (§6, §14)
- §14 applies the events-per-variable rule to ~30 durable outcomes, which allows 3 parameters. But accepts are far more plentiful: 405 accepts versus 1,095 non-accepts gives EPV = 405 / 10 ≈ 40 parameters, enough for the 6-weight score.
- Middle ground that keeps your caution: treat the hand-set β as a **prior** and fit a ridge or Bayesian logistic regression on accepts, shrinking toward that prior. Little data keeps β near your judgement; more data moves it. Validate once on the ~12–30 durable outcomes as a sanity check only.
- Note: Peduzzi's "10 EPV" rule is now considered rough. Riley et al. (BMJ 2020, sample size for prediction models) give a principled calculation, and penalised models need fewer events.

### 3. Normalise feature scales before weighting (§6)
- β only means "importance" if features have comparable spread. Here f₂ is a lookup in {0.1, 0.3, 0.9, 1.0}, while f₁ (harmonic MaxSim-IDF) will mostly sit near 0 with a long tail. With equal β, f₂ would dominate the ranking.
- Fix: convert each feature to its percentile rank within the cohort (or z-score), then apply β. Report each feature's spread next to its β.

### 4. Specify how §7 (global b-matching) and §8 (per-user diverse slates) combine
- §7 picks edges globally under degree caps; §8 picks each user's slate greedily for diversity. Run independently, §8 can break §7's caps and floor.
- Fix (one option): add the diversity bonus into the edge weights before the b-matching, or run §8 only to **order** the slate that §7 already chose.

## Medium impact

### 5. Exact b-matching "via flow" holds only for bipartite graphs (§7.3)
Friend graphs are general (non-bipartite). Exact maximum-weight b-matching there needs blossom-type methods or an integer program, not plain max-flow. The greedy ½-approximation is fine at n = 300; just correct the sentence. A cheap upgrade: greedy followed by a few rounds of local swaps (2-opt) usually closes much of the gap.

### 6. Replace fixed ε = 0.2 with Thompson sampling or a decaying ε (§9)
A fixed 20% exploration keeps costing 20% of slots forever (linear regret). Thompson sampling explores more early and less later, automatically. If propensities are needed for IPS, Thompson propensities can be estimated by Monte Carlo (sample the policy many times and count), or keep ε-greedy but decay it.

### 7. IPS on slates needs per-slot treatment (§9.4)
With 5 suggestions shown together, position and neighbouring items change accept rates. A single π₀(v | u) per item ignores that. Log the slot position and use a position-aware or pseudo-inverse estimator for slates (Swaminathan et al., NeurIPS 2017). With only 1,500 impressions, treat IPS results as coarse.

### 8. Guard against optimising the proxy (§2)
Accept rate is the powered metric, but it can rise by recommending already-popular people, which hurts the users the product exists for. Track guardrails alongside it: share of users with ≥ 1 accepted match, and inequality of inbound recommendations (Gini of I_v from §7.1).

### 9. Make the score reciprocal-aware
f₁ uses the harmonic mean of both directions, but S_uv overall is symmetric. Acceptance is two-sided: u may want v while v does not want u. Once the accept model exists (point 2), score P(u accepts) and P(v accepts) separately and combine them; the product is the probability that both accept, assuming independence.

## Small
- §4.3 soft df counts a user's own string in its own df_soft; state whether self-matches are excluded, as this inflates df for every string by about 1.
- §5.2 uplift priors: report a range, not a point, and plan to replace them from the randomised arm (§9.5) as stated.
- §15.5: the no-show caveat is excellent. Consider logging show-up as an outcome in its own right, since it is the stage the whole "activity slot" thesis depends on.
- Add a one-page "decisions and their evidence" table: each design choice, the section that justifies it, and what would change it.

## References
- Riley et al. (2020). Calculating the sample size required for developing a clinical prediction model. *BMJ* 368:m441.
- Swaminathan et al. (2017). Off-policy evaluation for slate recommendation. *NeurIPS*.
- Chapelle & Li (2011). An empirical evaluation of Thompson sampling. *NeurIPS*.
- Pizzato et al. (2010). RECON: a reciprocal recommender for online dating. *RecSys*.

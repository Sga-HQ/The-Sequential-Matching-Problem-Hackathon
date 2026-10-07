# Round 1 — Logic → Math workbook

How we work: **you write the logic in plain words → Claude writes the math, the reason it is correct,
where it comes from, and what our experiments measured.** Each block later becomes a section of the Round 1 note.

Rule for every block: the math must describe **what the policy actually does** (or clearly say "planned"),
and every number must come from our experiments, not a guess.

Sections the organisers require (docs/SUBMISSION.md): problem interpretation · hypothesis · reciprocal
feasibility · optional probability analysis · allocation method · clarification policy · missing and delayed
data · planned baselines · ablations · failure cases.

---

## Block 1 — How we make pairs every day (worked example)

### Your logic (plain words)
1. Each day, find every pair of people who are allowed to meet: both are free, all dealbreakers pass
   **in both directions**, and they have never been introduced.
2. For each allowed pair, estimate how likely **both** people are to say yes.
3. Give extra weight to people who have never been introduced, and to people with very few options.
4. Choose the set of pairs with the **best total**, with each person in at most one pair, rather than taking the single best pair first.
5. Double-check every chosen pair with the official rules before sending it.

### The math

**Notation.** Day $t$. $V_t$ = people who are available today with all dealbreakers known.
For a dealbreaker rule $k$, let $c_k(i \to j) \in \{0,1\}$ be 1 when $j$ satisfies $i$'s rule $k$.

**Step 1: who may meet (reciprocal feasibility).**

$$e_{ij}(t) = \prod_{k=1}^{K} c_k(i\to j)\,c_k(j\to i)\;\cdot\;[\,i,j \in V_t\,]\;\cdot\;[\,ij \text{ never introduced}\,]$$

$$E_t = \{\, ij : e_{ij}(t) = 1 \,\}$$

A single 0 in either direction makes the whole product 0, so "one failed rule kills the pair" falls straight out of the formula.
*Implementation:* each rule is a 0/1 column over all people, and the checks are vector ANDs (columnar numpy).
At 100,000 people this took 0.21 ms per new arrival; the row-by-row version took 21.7 ms. All methods produced the identical 7,970,144 pairs (`experiments/bench_100k.py`).

**Step 2: chance that both say yes.**
One direction, using the soft fields $f \in$ {goal, pace, lifestyle, conversations}:

$$p_{i\to j} = \sigma\Big(b + \sum_f w_{f,\,s_f(i,j)}\Big), \qquad s_f(i,j) \in \{\text{match},\ \text{differ},\ \text{unknown}\}, \quad w_{f,\text{unknown}} = 0$$

where $\sigma(z) = 1/(1+e^{-z})$. An unknown field adds 0, so missing data is **neutral**: it never counts as a mismatch.

Both directions:

$$q_{ij} = p_{i\to j}\cdot p_{j\to i}$$

The product is the true joint chance when the two replies are independent given the profiles. They are in the simulator: each person draws their own reply.

**Step 2b: learning the weights while running (Thompson sampling with ageing).**
Each (field, match/differ) cell keeps a Beta belief about its yes-rate:

$$\theta_{f,s} \sim \text{Beta}\big(\alpha_0 + Y_{f,s},\ \beta_0 + N_{f,s}\big)$$

The prior comes from the offline fit: $p_0 = \sigma(\text{logit}\,0.49 + w^{\text{offline}}_{f,s})$, with $\alpha_0 = 40p_0$ and $\beta_0 = 40(1-p_0)$, which is worth 40 replies.

The counts are aged, so old evidence fades:

$$Y_{f,s} = \sum_{\text{yes replies } r} \gamma^{\,t-\tau_r}, \qquad \gamma = 0.98 \text{ per day}$$

$N_{f,s}$ is the same sum over "no" replies. A reply from 35 days ago counts about half ($0.98^{35} \approx 0.49$).

Each day one $\theta$ is drawn per cell, and the weight becomes $w_{f,s} = \text{logit}\,\theta_{f,s} - \text{logit}\,b$.
Sources: Thompson sampling (lecture slides 19–20; Chapelle & Li 2011) and discounting (SMPyBandits `DiscountedBeta`).

**Step 3: urgency.**

$$u_i = \underbrace{1.5^{[\,i \text{ never introduced}\,]}}_{\text{coverage}} \cdot \underbrace{\Big(1 + \frac{0.5}{d_i}\Big)}_{\text{few options}}, \qquad d_i = |\{j : ij \in E_t\}|$$

$$v_{ij} = q_{ij}\, u_i\, u_j$$

The constants 1.5 and 0.5 are hand-set today. **Planned:** tune them offline on training seeds.

**Step 4: choose the best set (maximum-weight matching).**

$$\max_{x}\ \sum_{ij \in E_t} v_{ij}\, x_{ij} \quad \text{s.t.}\quad \sum_{j} x_{ij} \le 1\ \ \forall i, \qquad x_{ij} \in \{0,1\}$$

Among all matchings with the **most pairs**, we take the one with the highest total value (networkx `max_weight_matching(maxcardinality=True)`, Edmonds' blossom algorithm, $O(n^3)$, with integer weights $\lfloor 10^6 v \rfloor + 1$).

*Why not the best pair first?* The kit's own example: A–B 0.90, C–D 0.05, A–D 0.65, B–C 0.65.
- Best pair first: A–B + C–D = 0.95.
- Best set: A–D + B–C = 1.30.

In the worst case, picking the best pair first can get only about half of the best total (greedy is a ½-approximation for weighted matching).

*Why most pairs first?* Expected wins $= \sum_{ij} x_{ij}\, q_{ij}\, r_{ij}$, where $r_{ij}$ is the chance of the later funnel stages.
Our scorer only weakly separates good pairs from bad (AUC ≈ 0.55), so the $q_{ij}$ differ little between pairs.
Each extra pair adds about $\bar q \bar r$, while reordering pairs adds only the small differences in $q$.
So the number of pairs dominates (the funnel argument).

*Why match today rather than wait?* People leave at unknown times (exit days 22–60). When departures cannot be seen, waiting for a better partner loses more to departures than it gains in quality, and matching every day is close to optimal (Akbarpour, Li & Oveis Gharan 2020).

**Step 5: safety.** Every chosen pair is re-checked with the official `eligibility()`, because one invalid pair disqualifies the whole submission.

### What we measured (honest)
Results are on 240 episodes per policy (`experiments/run_ablation.py`, SKELETON.md §4):
- Best set plus most pairs gives +0.16 ± 0.10 mutual acceptances per 100 members.
- Urgency gives coverage +0.005 ± 0.001, small but very consistent.
- MSMI shows no measurable change; the differences are inside the noise.

The ceiling analysis explains why: the baseline already uses 75% of all allowed pairs, and even a perfect scorer would add about 8% (`experiments/theory_ceilings.py`).

---

## Block 2 — Whom to ask, and what (clarification policy)
### Your logic
_(write here)_
### The math
_(Claude)_

## Block 3 — Missing and delayed data
### Your logic
_(write here)_
### The math
_(Claude)_

## Block 4 — Hypothesis
### Your logic
_(write here)_
### The math / test
_(Claude)_

## Block 5 — Baselines, ablations and how we prove a gain
### Your logic
_(write here)_
### The math
_(Claude: paired differences by seed, standard error, power analysis)_

## Block 6 — Failure cases (sparse supply, withheld answers, delayed feedback, competition for one person)
### Your logic
_(write here)_
### The math
_(Claude)_

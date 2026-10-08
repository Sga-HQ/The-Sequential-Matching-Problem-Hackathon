# START HERE: the whole project on one page

## The game
- There is a fake dating app with **200 people**. It runs for **60 days**.
- Every day our program does two things:
  1. **Ask:** pick a few people to ask questions (12 points per day; asking someone for all their dealbreakers costs 3 points).
  2. **Introduce:** pick pairs of people to introduce. Each person can be in at most one pair that day.
- **We win points** when an introduced pair both say yes, go on a date, and both want a second date. This is rare: about 1 pair in 100.
- **We are disqualified** if we ever introduce a pair that breaks someone's dealbreaker.

## 8 words you need

| Word | Meaning |
|---|---|
| Dealbreaker | A hard rule ("no smokers", "age 25–35", "same city"). Must pass for both people. |
| Allowed pair | Two people who pass each other's dealbreakers |
| Unknown / Pending | The person hasn't told us their dealbreakers yet → we can't pair them until we ask |
| Refused / Blocked | They declined to answer → can never be paired |
| Busy | After an introduction, a person is off the list for 8 days |
| Soft fields | Preferences that aren't rules (goals, pace, lifestyle, chat style). They change the chance of a yes. |
| Score | Chance that both say yes |
| MSMI | The official score: pairs who both want a second date, per 100 people |

## How we make pairs every day (the 5-step routine)
1. **List** everyone who is free today and whose dealbreakers we know.
2. **Find allowed pairs:** check every dealbreaker both ways, and cross out pairs introduced before.
3. **Score** each allowed pair: how likely both say yes, using the soft fields.
4. **Pick the best set,** with each person used at most once, maximising the total.
5. **Double-check** every pair with the official rule checker, then send.

The next day we do it all again **from scratch**: people who became free return to the list, and new arrivals join. Redoing it daily for 200 people takes under a second, so there's no need to remember old pairs, except the "already introduced" list.

## What we found (measured, not guessed)
1. **Asking is essential:** without asks, the score drops 72%. Most people start with unknown dealbreakers.
2. **Each person has only ~3 allowed partners.** The kit's simple method already introduces 75% of all allowed pairs.
3. So clever methods add little: our full prototype ≈ the kit's simple method. **Realistic gain is +5–15%; the hard maximum is +40%.**
4. Most remaining losses: a person already found a match (53%), left the app (27%), or was busy (20%).

## What we must hand in
- **Round 1 (due 9 Oct, 23:59 IST):** a written note (≥10 pages) explaining our method, why, the maths, tests, and what went wrong.
- **Round 2 (12–18 Oct):** the working program.

## Who does what
| You (designer and author) | Claude (engineer and calculator) |
|---|---|
| Decide the rules in plain words | Turn them into code and maths |
| Choose between options when there's a trade-off | Run the tests and report the numbers |
| Own the story of the note: what we believe and why | Draft sections from your logic and our results |
| Check that every sentence makes sense to you | Fix anything you don't understand |

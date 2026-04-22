# Report Tables

Source: `results/phase6_seed20260422_depth3_final/summary.csv`.

Configuration: seat-swapped tournaments, seed `20260422`, fixed-depth minimax
with depth limit `3`, no minimax time cap. Q-learning uses the 50,000-episode
checkpoint documented in `artifacts/qlearning_50k_seed152_metadata.json`.

Wilson intervals are 95% intervals over all games, counting draws as non-wins
for the agent whose win rate is reported.

## Table 1: Agents vs Random

| Agent | Games | Agent wins | Random wins | Draws | Win rate | 95% CI | Avg margin | Avg plies |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random baseline (A) | 100 | 55 | 38 | 7 | 55% | 45.2%-64.4% | 2.24 | 35.1 |
| minimax_h1 | 100 | 100 | 0 | 0 | 100% | 96.3%-100.0% | 26.84 | 24.5 |
| minimax_h2 | 100 | 100 | 0 | 0 | 100% | 96.3%-100.0% | 26.04 | 24.5 |
| minimax_h3 | 100 | 100 | 0 | 0 | 100% | 96.3%-100.0% | 27.32 | 24.4 |
| minimax_h4 | 100 | 100 | 0 | 0 | 100% | 96.3%-100.0% | 27.70 | 24.7 |
| qlearning_50k | 100 | 61 | 36 | 3 | 61% | 51.2%-70.0% | 4.50 | 34.0 |

## Table 2: Q-Learning vs Minimax

| Opponent | Games | Q wins | Opponent wins | Draws | Q win rate | 95% CI | Avg margin for Q | Avg plies |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| minimax_h1 | 100 | 0 | 100 | 0 | 0% | 0.0%-3.7% | -33.00 | 21.5 |
| minimax_h2 | 100 | 0 | 100 | 0 | 0% | 0.0%-3.7% | -27.00 | 25.5 |
| minimax_h3 | 100 | 0 | 100 | 0 | 0% | 0.0%-3.7% | -28.00 | 30.0 |
| minimax_h4 | 100 | 0 | 100 | 0 | 0% | 0.0%-3.7% | -28.00 | 32.5 |

## Table 3: Pairwise Minimax Heuristics

| Matchup | Games | Agent A wins | Agent B wins | Draws | A win rate | Avg margin for A | Avg plies |
|---|---:|---:|---:|---:|---:|---:|---:|
| minimax_h1 vs minimax_h2 | 60 | 30 | 30 | 0 | 50% | 2.00 | 25.5 |
| minimax_h1 vs minimax_h3 | 60 | 30 | 30 | 0 | 50% | -3.00 | 40.5 |
| minimax_h1 vs minimax_h4 | 60 | 30 | 30 | 0 | 50% | 8.00 | 38.0 |
| minimax_h2 vs minimax_h3 | 60 | 30 | 30 | 0 | 50% | 0.00 | 45.5 |
| minimax_h2 vs minimax_h4 | 60 | 30 | 30 | 0 | 50% | 8.00 | 38.0 |
| minimax_h3 vs minimax_h4 | 60 | 30 | 30 | 0 | 50% | 3.00 | 36.5 |

## Report Takeaways

- All four depth-3 minimax heuristics beat random decisively in this batch.
- Q-learning beats random but remains far weaker than depth-3 minimax.
- Pairwise minimax matchups split exactly after seat swapping, so the report
  should not claim a strict heuristic ranking from wins alone.
- Store margin and game length can be used as secondary evidence, with the
  caveat that this is still one seeded experiment batch.
- No game in this batch hit the 200-ply cap.

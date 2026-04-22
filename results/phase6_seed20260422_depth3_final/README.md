# Phase 6 Experiment Batch

Seeded, seat-swapped Ayo tournaments for report inputs.

## Configuration

- Tournament seed: `20260422`
- Minimax depth limit: `3`
- Minimax time limit: none (fixed-depth search)
- Seat swapping: enabled
- Q checkpoint: `artifacts/qlearning_50k_seed152.pkl`
- Q checkpoint SHA-256:
  `bd481d9ec5e07c076fc59770d3e58d0fb29f597efb94a136118f94f1782b1aea`
- Q training: 50,000 self-play episodes, seed `152`, alpha `0.1`,
  gamma `0.99`, epsilon linearly decayed from `1.0` to `0.05`
- Q entries: `980812`

## Summary

| Matchup | Agent A wins | Agent B wins | Draws | Agent A win rate | Avg margin for A | Avg plies |
|---|---:|---:|---:|---:|---:|---:|
| random vs random | 55 | 38 | 7 | 0.55 | 2.24 | 35.1 |
| random vs minimax_h1 | 0 | 100 | 0 | 0.00 | -26.84 | 24.5 |
| random vs minimax_h2 | 0 | 100 | 0 | 0.00 | -26.04 | 24.5 |
| random vs minimax_h3 | 0 | 100 | 0 | 0.00 | -27.32 | 24.4 |
| random vs minimax_h4 | 0 | 100 | 0 | 0.00 | -27.70 | 24.7 |
| qlearning vs random | 61 | 36 | 3 | 0.61 | 4.50 | 34.0 |
| qlearning vs minimax_h1 | 0 | 100 | 0 | 0.00 | -33.00 | 21.5 |
| qlearning vs minimax_h2 | 0 | 100 | 0 | 0.00 | -27.00 | 25.5 |
| qlearning vs minimax_h3 | 0 | 100 | 0 | 0.00 | -28.00 | 30.0 |
| qlearning vs minimax_h4 | 0 | 100 | 0 | 0.00 | -28.00 | 32.5 |
| minimax_h1 vs minimax_h2 | 30 | 30 | 0 | 0.50 | 2.00 | 25.5 |
| minimax_h1 vs minimax_h3 | 30 | 30 | 0 | 0.50 | -3.00 | 40.5 |
| minimax_h1 vs minimax_h4 | 30 | 30 | 0 | 0.50 | 8.00 | 38.0 |
| minimax_h2 vs minimax_h3 | 30 | 30 | 0 | 0.50 | 0.00 | 45.5 |
| minimax_h2 vs minimax_h4 | 30 | 30 | 0 | 0.50 | 8.00 | 38.0 |
| minimax_h3 vs minimax_h4 | 30 | 30 | 0 | 0.50 | 3.00 | 36.5 |

## Interpretation Notes

- The Q-learning agent is stronger than random in this batch but loses
  decisively to depth-3 minimax.
- All four minimax heuristics beat random 100/100 in this seeded sample.
- Pairwise minimax heuristic matches split exactly by seat in this batch
  (`30-30` for all pairs), so do not overclaim heuristic ordering from wins
  alone. Use store margins, game length, and larger/deeper experiments if
  discussing heuristic differences.
- No games reached the 200-ply cap.

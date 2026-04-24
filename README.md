# Ayo Game AI

This repository contains a final project for CS152: Harnessing AI Algorithms. It implements the Yoruba mancala game Ayo, a minimax agent with alpha-beta pruning, a tabular Q-learning agent trained through self-play, a random baseline, a human-play CLI, a Connect Four baseline used to validate the minimax implementation, and a tournament evaluator for comparative analysis.

## Requirements

- Python 3.13 or later
- `pip`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Tests

```bash
pytest tests/ -q
```

## Playing the Game

Human vs. random:

```bash
python -m src.cli --p0 human --p1 random
```

Human vs. minimax:

```bash
python -m src.cli --p0 human --p1 minimax --minimax-time none
```

Human vs. Q-learning:

```bash
python -m src.cli --p0 human --p1 qlearning
```

The CLI supports the following agent names:

- `human`
- `random`
- `minimax`
- `minimax_h1`
- `minimax_h2`
- `minimax_h3`
- `minimax_h4`
- `qlearning`

## Running an Evaluation Batch

Example tournament command:

```bash
python -m src.evaluate \
  --agent-a minimax_h4 --agent-b qlearning \
  --agent-b-q-path artifacts/qlearning_50k_seed152.pkl \
  --out results.csv
```

The evaluator writes per-game CSV output and summary statistics, and it supports seat swapping and seeded runs.

## Repository Structure

```text
src/
  games/         Ayo and Connect Four rules engines
  agents/        Human, random, minimax, and Q-learning agents
  heuristics/    Ayo heuristic evaluation functions
  cli.py         Command-line game runner
  evaluate.py    Tournament and metrics runner
tests/           Automated tests
artifacts/       Trained Q-learning checkpoint and metadata
results/         Evaluation outputs used for the report
report/          Final report source and PDF
```

## Rule Conventions Used in This Implementation

This project uses one explicit computational ruleset for Ayo so that the agents can be evaluated consistently.

- The board has 12 play pits and two store positions used only for accounting captured seeds.
- Stores are never part of sowing.
- Relay sowing is implemented, including skip-origin behavior on the current relay lap.
- If the opponent side is empty, legal moves must satisfy the feeding rule when possible.
- If relay sowing repeats an exact sow-state within a move and cannot terminate normally, that move is treated as illegal.
- A 200-ply cap is used as a computational safeguard against nonterminating full games.

These conventions are documented in the report and tested in `tests/test_ayo_rules.py`.

## Included Artifacts

- Trained Q-learning checkpoint: `artifacts/qlearning_50k_seed152.pkl`
- Q-learning metadata: `artifacts/qlearning_50k_seed152_metadata.json`
- Final evaluation tables and CSVs: `results/phase6_seed20260422_depth3_final/`
- Final report PDF: `report/ayo_ai_report.pdf`

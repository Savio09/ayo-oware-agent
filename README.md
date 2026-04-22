# Ayo-CS152

An AI opponent for **Ayo** — the Yoruba mancala game from Nigeria —
built for Minerva CS152 (Harnessing AI Algorithms).

The project implements Ayo rules/play, reusable minimax (alpha-beta +
iterative deepening), Ayo heuristic evaluation, tabular Q-learning via
self-play, a tournament evaluation harness, and Connect Four as a validation
baseline for the minimax code.

---

## How to run

```bash
# Create / activate the venv (Python 3.13+)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Tests
pytest tests/ -q

# Play human (P0) vs. random (P1)
python -m src.cli

# Run a seeded random-vs-random game
python -m src.cli --p0 random --p1 random --seed 42

# Run a seeded evaluation tournament
python -m src.evaluate \
  --agent-a minimax_h4 --agent-b random \
  --n 20 --seed 42 --out results.csv \
  --minimax-time none
```

The CLI currently supports human and random agents. Minimax is implemented
and validated on Connect Four, with Ayo heuristics ready for minimax play;
Q-learning is implemented as a trainable agent, and `src.evaluate` can run
seat-swapped tournaments with CSV output.

---

## Project layout

```
src/
├── games/      # rules engines (Ayo and Connect Four)
├── agents/     # random, human, minimax, Q-learning
├── heuristics/ # Ayo evaluation functions (H1..H4)
├── cli.py      # human-vs-agent game runner
└── evaluate.py # tournament harness + metrics
tests/          # pytest rule-correctness + agent tests
```

---

## Rule choices (why the code looks the way it does)

Ayoayo has several regional variants. The choices below were made by
comparing Wikipedia's Ayoayo page and Mancala Fandom against Declan's
course spec, then picking one consistent ruleset. Deviating from tradition
in any place is called out explicitly.

- **Board:** 12 play pits in 2 rows of 6, plus **two stores** (one per
  player).
  - Traditional Ayoayo keeps captured seeds off-board. This project uses
    a Kalah-style store abstraction _purely as accounting_: captured
    seeds live at indices 6 (P0) and 13 (P1) of a flat 14-tuple. Stores
    are never sown into, and they do not function as "bonus pits" like
    in Kalah — a seed never ends a move in a store. This is a code
    convenience that makes hashing and scoring uniform across games; it
    does not change the game's strategic surface.
- **Initial setup:** 4 seeds per pit (48 total); stores empty.
- **Sowing:** counterclockwise, one seed per pit. Stores are skipped.
- **Skip-origin:** the pit the move started from is skipped **for the
  current relay lap only**. A later relay lap may sow seeds back into
  the original pit.
- **Relay (multi-lap) sowing:** if the last seed lands in a non-empty
  pit, pick up all seeds there and continue sowing from that pit. Sowing
  stops only when the last seed lands in an **empty** pit.
- **Intra-move relay cycles:** if relay sowing repeats an exact sow-state
  during a move and therefore cannot reach an empty final pit, that move is
  treated as illegal and is filtered out of `legal_moves()`. This is a
  computational convention for nonterminating moves inside one move.
- **Capture:** if sowing stops in an empty pit on the mover's own side
  AND the opposite pit contains seeds, the mover captures the opposite
  pit's seeds **plus the final seed** into their store.
- **Feeding:** if the opponent's side is empty, the mover must play a
  move that leaves at least one seed on the opponent's side _after_
  captures resolve. If no such move exists, the game ends and the mover
  keeps their own remaining seeds.
- **Standard endgame:** if the mover has no seeds on their side at the
  start of their turn, the game ends and the opponent collects all
  remaining board seeds.
- **Grand slam:** emptying the opponent's side via capture is allowed,
  and the capture stands. The feeding rule then applies on the next turn.
- **Ply-limit safety valve (non-traditional):** if the game reaches 200
  plies without terminating, it ends. Seeds still on the board are
  ignored; the winner is decided by store counts, with ties = draws.
  This is a computational safeguard, not a traditional rule.
- **Inter-move repeated positions:** no repeated-position detection is used
  across turns; the 200-ply safety valve is the only inter-move cycle
  safeguard.

The full rules engine and its test suite live in
`src/games/ayo.py` and `tests/test_ayo_rules.py`.

---

## Design notes

- **Immutable states.** `AyoState` is a frozen `dataclass`, so states are
  hashable and safe to use as dictionary keys (needed for Q-learning
  tables and minimax transposition tables).
- **`q_key()` omits ply.** Q-learning should treat the same board
  position identically regardless of how many moves were played to
  reach it, so `AyoState.q_key()` drops the ply counter.
- **Utility vs. heuristics.** `Game.utility` returns only pure terminal
  values (±1 / 0). Heuristic (non-terminal) evaluation lives in
  `src/heuristics/`, to keep the rules engine free of game-playing bias.
- **Awari paper (`awari.pdf`).** Romein & Bal (2002) is cited for
  algorithmic and historical context only. Awari is a _different_ game;
  its rules were not used as a source for Ayo.

---

## Status

| Phase | Description                                  | Status       |
| ----- | -------------------------------------------- | ------------ |
| 1     | Ayo rules engine + tests                     | Done (27/27) |
| 2     | CLI + random agent                           | Done (14/14) |
| 3     | Connect Four + minimax (validation baseline) | Done (17/17) |
| 4     | Minimax for Ayo with heuristics H1–H4        | Done (10/10) |
| 5     | Tabular Q-learning via self-play             | Done (9/9)   |
| 6     | Evaluation harness                           | Done (10/10) |

See `progress.md` for detailed hand-off notes between sessions.

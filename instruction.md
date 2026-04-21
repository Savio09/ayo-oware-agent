# CS152 Final Project: Ayo Game AI

# Overview

You have to carefully read through this assignment instruction


## Context

I'm building an AI opponent for Ayo, the traditional Yoruba mancala game from
Nigeria, for my CS152 (Harnessing AI Algorithms) final project at Minerva
University. The project targets three Learning Outcomes: #aicoding (implementing
AI in Python), #search (minimax, alpha-beta pruning, Q-learning), and
#aiconcepts (historical/philosophical framing of AI game-playing). 

The deliverables are:
1. A playable Ayo game with human-vs-AI interface
2. A minimax AI agent with alpha-beta pruning and iterative deepening
3. A Q-learning AI agent trained via self-play (scope: tabular, on reachable
   states only)
4. A Connect Four implementation as a validation baseline for the minimax code
5. A comparative analysis across agents
6. A 3-page report (I'll write this separately; focus on code for now)

I'm graded on correctness, elegance, analytical depth, and how well the work
synthesizes course material. Functional code is a prerequisite for any grade
above a 3. I'm aiming for a 4-5.

## Game rules (Ayo — Yoruba version)

- Board: 12 pits in 2 rows of 6, plus 2 stores (one per player).
- Initial state: 4 seeds per pit (48 seeds total), stores empty.
- On a turn, a player picks all seeds from one pit on their own side and sows
  them one at a time counterclockwise into subsequent pits.
- Stores are NOT included in sowing (this is specific to Ayo, unlike Kalah).
- If a pit being sown from has enough seeds to loop the board, the originating
  pit is skipped on the loop.
- Capture rule: if the last seed sown lands in an empty pit on the PLAYER'S OWN
  side AND the opposite pit (on opponent's side) contains seeds, the player
  captures the opponent's seeds from that opposite pit AND the final seed. The
  captured seeds go to the player's store.
- "Feeding" rule: if the opponent has no seeds on their side, the current
  player MUST make a move that delivers seeds to the opponent's side if such a
  move exists. If no such move exists, the game ends and the player with seeds
  remaining captures them.
- Game ends when a player cannot move. Remaining seeds go to the opponent's
  store (or the player's own, per the feeding rule above). Winner = most seeds
  in store.

Please verify these rules against authoritative sources before implementing
and flag any ambiguities for me to resolve. Different Nigerian communities
play slight variants, and I want to pick one consistent ruleset and document it.

## Project structure I want

ayo-ai/
├── README.md                    # How to run, what's implemented
├── requirements.txt
├── src/
│   ├── games/
│   │   ├── init.py
│   │   ├── base.py              # Abstract Game interface (state, moves, etc.)
│   │   ├── ayo.py               # Ayo implementation
│   │   └── connect_four.py      # Baseline for validating minimax
│   ├── agents/
│   │   ├── init.py
│   │   ├── base.py              # Abstract Agent interface
│   │   ├── random_agent.py      # Random baseline
│   │   ├── human.py             # CLI input
│   │   ├── minimax.py           # Minimax + alpha-beta + iterative deepening
│   │   └── qlearning.py         # Tabular Q-learning
│   ├── heuristics/
│   │   └── ayo_heuristics.py    # Multiple evaluation functions to compare
│   ├── cli.py                   # Play games from the terminal
│   └── evaluate.py              # Run tournaments, collect metrics
├── tests/
│   ├── test_ayo_rules.py        # Rule correctness — this is critical
│   ├── test_minimax.py
│   └── test_connect_four.py
└── notebooks/
└── analysis.ipynb           # For the report's figures/tables


## Approach and priorities

Please proceed in this order, stopping after each phase for me to review:

**Phase 1: Ayo rules engine + tests.** This is the foundation. Get the game
logic bulletproof before anything else. Write thorough tests — I want to catch
rule bugs before they poison the AI's learning or decisions. Include tests for
edge cases: the skip-originating-pit rule, the feeding rule, capture chains,
endgame seed collection.

**Phase 2: Game-playing CLI + random agent.** So I can play through the game
by hand and sanity-check it feels right before adding AI.

**Phase 3: Connect Four + minimax validation.** Implement Connect Four and
minimax with alpha-beta. Verify the minimax agent plays sensibly (wins against
random, draws/wins against itself at higher depths, demonstrable pruning
speedup). This proves the minimax implementation is correct before I trust it
on Ayo.

**Phase 4: Minimax for Ayo.** Port minimax to Ayo with iterative deepening and
a time budget per move. Implement 3-4 distinct heuristics I can compare:
  - H1: simple seed differential (store_me - store_opponent)
  - H2: seed differential + mobility (number of legal moves)
  - H3: H2 + capture potential on next move
  - H4: H3 + vulnerability penalty (pits with 1-2 seeds on my side)
Make it easy to swap heuristics via a parameter.

**Phase 5: Q-learning.** Tabular, reachable-states-only, trained via self-play.
Be honest about scope — it will underperform minimax, and that's fine. Use a
hashable state representation (tuple of pit counts). Epsilon-greedy policy,
decaying epsilon, reasonable defaults I can tune.

**Phase 6: Evaluation harness.** A script that runs N games between any two
agents and reports win rates, average game length, decision time per move,
search nodes visited (for minimax). Output in a format easy to turn into
tables/figures.

## Code quality expectations

- Type hints throughout.
- Docstrings on all public functions with examples where useful.
- Keep functions small and testable. I want to be able to explain any line to
  my professor.
- No hidden dependencies on global state.
- Prefer clarity over cleverness. This is educational code, not production.
- Comments should explain *why*, not *what*.
- I want to understand everything we build. If you're about to make a design
  decision that has trade-offs, pause and ask rather than picking silently.

## Things I do NOT want

- No ML libraries beyond numpy (no PyTorch, no stable-baselines). Tabular
  Q-learning only — this matches the course syllabus.
- No GUI. CLI is fine. Saves time for actual AI work.
- No copying code from existing Ayo/Oware repos on GitHub. Reference them for
  rule clarification only. Submitted code is checked with TurnItIn.
- Don't optimize prematurely. Get it correct first.

## How to work with me

- Start with Phase 1. Show me the rules engine design (the Game interface,
  state representation, move generation) BEFORE writing the full
  implementation, so I can catch design issues early.
- After each phase, summarize what changed, what tests pass, and what's next.
- If you hit ambiguity (e.g., a rule edge case, a heuristic design choice),
  ask me rather than assuming.
- I want to learn from this project. When you implement something non-obvious
  (minimax recursion, alpha-beta cutoffs, Q-update formula), walk me through
  the logic in plain terms.

Ready? Start with Phase 1 — but first, verify the Ayo rules against at least
two authoritative sources (Wikipedia's Ayoayo page and John Pratt's mancala
rules page are good starts), flag any discrepancies, and propose the Game
interface and state representation for my approval before coding.
# Ayo-CS152 — Handoff / Progress Document

> Hand-off document for the next agent picking up this project. Read this
> end-to-end before touching code. Everything below is already agreed with the
> user (Declan); don't re-open settled questions unless the user asks.
>
> **Convention:** after each approved change, append an entry to §0 (Changelog)
> and update any other sections that drift. Keep the changelog in
> newest-on-top order with ISO dates. The other sections should always
> describe the *current* state, not history.

---

## 0. Changelog

### 2026-04-21 — Phase 2 kickoff

In progress (Phase 2: CLI + random agent):

- **Render updated** to show player-relative pit labels (1..6) above P1's
  row and below P0's row. Each player reads their own row left-to-right as
  "1 2 3 4 5 6". Internal pit indices no longer printed in render.
  `src/games/ayo.py:112-134`.
- **`src/agents/base.py`** created — abstract `Agent[StateT, MoveT]` ABC
  with `select_move(game, state) -> MoveT` and a `name` property.
- **`src/agents/__init__.py`** created (empty).

Pending inside Phase 2: RandomAgent, AyoHumanAgent, `src/cli.py`,
`tests/test_agents.py`.

### 2026-04-21 — Phase 1 cleanup + README

User approved a four-step cleanup batch before starting Phase 2:

- **Step 1 — `_sow` iteration cap (resolves §6a).** Added
  `Ayo._SOW_BUDGET = 10_000` and refactored `_sow` into a bounded `for`
  loop that raises `RuntimeError` on overflow. Defensive only; a legal
  48-seed board terminates in well under 10k steps. `src/games/ayo.py`.
  Tests: 24/24 still pass.
- **Step 2 — `_delivering_moves` helper (resolves §6b).** Extracted
  `_nonempty_pits(state, side)` and `_delivering_moves(state, candidates)`
  on `Ayo`. Both `legal_moves` and `_finalize_if_terminal` now call them
  so the feeding rule has one source of truth. `src/games/ayo.py`.
  Tests: 24/24 still pass.
- **Step 3 — TODO comments in `tests/test_ayo_rules.py`.** The two extra
  tests suggested by the test-trace verifier (final_pos == move start
  after relay; relay tail on opp side with no capture) were NOT written
  — user deferred them. Instead added `# TODO` comments in the capture
  and relay sections so they're not forgotten.
- **Step 4 — `README.md` written (resolves §6d).** One-page README
  covering: how to run, project layout, rule choices (with the Kalah-store
  abstraction documented explicitly), design notes, and a phase-status
  table.

### 2026-04-21 — Phase 1 complete + fact-check

- Phase 1 (Ayo rules engine + tests) implemented. 24 tests in
  `tests/test_ayo_rules.py`, all green.
- Three parallel fact-checker agents verified the work: test-trace
  verifier matched all hand-traces, code reviewer flagged §6a/§6b,
  rules auditor blocked on web permissions (not a blocker since rules
  were manually verified against Wikipedia + Mancala Fandom during the
  design phase).

---

## 1. Project at a glance

- **Course:** Minerva CS152 — Harnessing AI Algorithms. Final project, 20% weight.
- **LOs targeted:** #aicoding, #search, #aiconcepts.
- **Target grade:** 4–5. Functional code is a floor, not a ceiling — depth and
  synthesis matter.
- **Core deliverable:** AI opponent for Ayo (Yoruba mancala).
- **User writes the report separately** (3 pages). Our job is the code, the
  analysis inputs (tables, figures), and an `AI_log.md` accounting of AI usage.
- **Full original spec:** `instruction.md` (still authoritative on what phases
  exist and what the user wants). Read it once.
- **Assignment PDF:** `AI Final Project.pdf` (rubric — grade 4/5 requires
  synthesis, not just correctness).
- **Reference-only paper:** `awari.pdf` (Romein & Bal 2002, solving Awari).
  Historical/algorithmic reference; Awari is a *different* game, don't use it
  as a rules source for Ayo.

### Deliverables (per `instruction.md`)

1. Playable Ayo game with human-vs-AI CLI
2. Minimax agent with alpha-beta pruning + iterative deepening
3. Tabular Q-learning agent (self-play, reachable states only)
4. Connect Four — baseline used to validate minimax before trusting it on Ayo
5. Comparative analysis across agents
6. 3-page report (user handles this)

---

## 2. Where we are right now

**Phase 1 is complete** (rules engine + 24 passing tests + fact-checked +
both flagged issues fixed + README written). **Phase 2 is in progress**
(Agent ABC exists; RandomAgent / HumanAgent / CLI / agent tests still to
go). See §0 for the blow-by-blow.

### What exists on disk

```
ayo-cs152/
├── .flake8                       # max-line-length=100, ignore E203,W503
├── .gitignore                    # .venv, __pycache__, *.pyc, .pytest_cache, .DS_Store
├── .venv/                        # Python 3.13.8 virtualenv (DO NOT use global Python)
├── AI Final Project.pdf          # assignment rubric
├── AI_log.md                     # user-maintained AI usage log (stub)
├── README.md                     # how to run, rule choices, status table
├── awari.pdf                     # reference paper (Awari, different game)
├── instruction.md                # original project spec from the user
├── progress.md                   # this file
├── pytest.ini                    # pythonpath=., testpaths=tests
├── requirements.txt              # numpy>=1.24, pytest>=7.0
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   └── base.py               # abstract Agent[StateT, MoveT] ABC
│   └── games/
│       ├── __init__.py
│       ├── base.py               # abstract Game[StateT, MoveT] ABC
│       └── ayo.py                # AyoState + Ayo rules engine
└── tests/
    ├── __init__.py
    └── test_ayo_rules.py         # 24 passing tests
```

### What does NOT exist yet (to avoid confusion)

- `src/agents/random_agent.py` — Phase 2, next up.
- `src/agents/human.py` — Phase 2, next up.
- `src/cli.py` — Phase 2, next up.
- `tests/test_agents.py` — Phase 2, next up.
- `src/games/connect_four.py` — Phase 3.
- `src/agents/minimax.py` — Phase 3.
- `src/heuristics/` — Phase 4.
- `src/agents/qlearning.py` — Phase 5.
- `src/evaluate.py`, `tests/test_minimax.py`, `tests/test_connect_four.py` —
  later phases.
- `notebooks/analysis.ipynb` — user will deal with this during analysis phase.

### How to run things

```bash
# Activate the venv — always do this first, never use system Python.
source .venv/bin/activate

# Run tests
pytest tests/ -q           # currently: 24 passed

# Lint (the user hasn't asked for lint-on-commit; run when touching files)
flake8 src tests

# Python version
python --version           # should say 3.13.8
```

---

## 3. Rules decisions already locked in

These were resolved after the user and I compared `instruction.md` against
Wikipedia and Mancala Fandom. **Don't revisit these without asking the user.**

| Decision                              | Choice                                                                     |
|---------------------------------------|----------------------------------------------------------------------------|
| Relay (multi-lap) sowing              | Yes — last seed in non-empty pit picks up and continues.                   |
| Sowing stops                          | When last seed lands in an **empty** pit.                                  |
| Store representation                  | Kalah-style stores kept **as accounting abstraction only** (documented).   |
| Capture                               | Final seed is included in the captured pile.                               |
| Skip-origin during sow                | Applies **per lap** only — a later relay lap may sow into the original pit.|
| Stores in sowing path                 | Both stores are skipped during sowing (always).                            |
| Grand slam (emptying opp side)        | Allowed; capture is allowed; feeding rule then kicks in on next turn.      |
| Repeated-position cycle detection     | None. Use a **200-ply safety valve** instead.                              |
| Ply-limit terminal                    | Seeds stay on board; winner decided by **store counts only**; tie = draw.  |
| Utility at terminals                  | Pure ±1 / 0. Heuristics live in a separate module (not in the game class). |
| Q-learning state key                  | `AyoState.q_key()` returns `(pits, to_move)` — **omits ply**.              |
| Awari paper                           | Historical/algorithmic reference only. Not a rules source.                 |

### Board layout (flat 14-tuple)

```
        P1:  [12] [11] [10] [ 9] [ 8] [ 7]
    P1 store: 13                        P0 store: 6
        P0:  [ 0] [ 1] [ 2] [ 3] [ 4] [ 5]
```

Counterclockwise sowing: `0, 1, 2, 3, 4, 5, (skip 6), 7, 8, 9, 10, 11, 12,
(skip 13), wrap to 0`. Opposite pit: `12 - i` for play pits 0..5 ↔ 7..12.
Stores have no opposite.

---

## 4. Design decisions already locked in

- **Immutable state:** `AyoState` is a `@dataclass(frozen=True, slots=True)`
  so it is hashable (needed for Q-learning and transposition tables later).
- **State fields:** `pits: tuple[int, ...]` (length 14), `to_move: int`,
  `ply: int`.
- **`Game` interface (`src/games/base.py`):** ABC generic over `StateT` and
  `MoveT`. Methods: `initial_state`, `current_player`, `legal_moves`,
  `apply_move`, `is_terminal`, `winner`, `utility`, `render`. `is_terminal`
  has a default impl (`len(legal_moves) == 0`). `utility` has a default impl
  that reads `winner` and returns ±1/0 — heuristics do **not** live here.
- **`apply_move` always returns a finalized state.** If the move ends the
  game, any remaining-seed sweeps are already reflected in the returned state.
  Callers never need to call a separate finalize method.
- **Terminal branches inside `_finalize_if_terminal`:**
    1. Mover's own side is empty → opponent sweeps remaining board seeds into
       opponent's store (standard endgame).
    2. Opponent's side is empty AND mover has no delivering (feeding) move →
       mover sweeps their own remaining seeds into their own store.
    3. At or past ply 200 → seeds stay on board; stores alone decide winner.
- **Move type for Ayo:** `int` (pit index, 0..5 for P0 or 7..12 for P1).
- **Render output:** ASCII, multi-line. Shows player-relative pit labels
  (1..6) above P1's row and below P0's row — each player reads their own
  row left-to-right as "1 2 3 4 5 6". Internal pit indices are not printed;
  the mapping (P0 label n → pit n−1; P1 label n → pit 13−n, so P1 label 1
  = pit 12) is documented in README §Rule choices. No fancy colors.
- **No ML libraries beyond numpy.** Tabular Q-learning only — this is in the
  user's "things I do NOT want" list. Do not reach for PyTorch / SB3 /
  Gymnasium.
- **No GUI.** CLI only.
- **No copied code from public Ayo/Oware repos.** TurnItIn will check.
  Reference them for rule clarification only.

---

## 5. Phase 1 test coverage — what's there, what to maybe add

All 24 tests in `tests/test_ayo_rules.py` pass. Coverage hits:

- initial state + 48-seed invariant
- immutability + hashing; `q_key()` ignores ply
- legal moves for P0 and P1, empty-pit skipping
- validation (opponent pit rejected, empty pit rejected)
- basic sowing without relay / without capture
- store-skip during sowing
- capture with final-seed inclusion
- no capture when opposite empty
- no capture when final lands on opp side
- skip-origin per lap (the 12-seed-in-pit-0 test)
- single-relay and compound-relay-with-capture
- feeding rule restricts legal moves
- feeding impossible → terminal; sweep direction correct
- mover-side-empty → opp collects
- ply-limit terminal: winner by stores, draw if tied
- render produces multi-line string

### Suggested additional tests (from the test-trace verifier agent, not yet added)

- **Capture where `final_pos` equals the original move index** — exercises
  the case where the pit you emptied at move start ends up being the final
  landing pit after relays.
- **Relay tail ending on opponent side with no capture** — confirms the
  "final on opp side → no capture" branch works after a relay, not just
  after a single-lap sow.

Neither is strictly required; they'd close small coverage gaps.

---

## 6. Open items from fact-check (status)

| # | Item                                             | Status                                                        |
|---|--------------------------------------------------|---------------------------------------------------------------|
| 6a| `_sow` iteration cap                             | **Resolved 2026-04-21.** `_SOW_BUDGET = 10_000`, raises.      |
| 6b| Duplicated terminal detection                    | **Resolved 2026-04-21.** `_delivering_moves` helper extracted.|
| 6c| Rules auditor blocked on web permissions         | Deferred. Manual verification already done; low priority.     |
| 6d| README documenting Kalah-store abstraction       | **Resolved 2026-04-21.** See `README.md` §Rule choices.       |
| 6e| Two extra edge-case tests (suggested by verifier) | Deferred. TODO comments in `tests/test_ayo_rules.py`.        |

---

## 7. Roadmap — remaining phases

> The user wants to review at phase boundaries. **Stop at the end of each
> phase** and ask for approval before starting the next. When making design
> decisions with real trade-offs, ask rather than silently choosing.

### Phase 2 — Game-playing CLI + random agent (in progress)

**Goal:** the user can play Ayo in the terminal vs. a random opponent to
sanity-check the feel before AI lands.

**Status:** `src/agents/base.py` written (Agent ABC). Render updated with
player-relative labels. Remaining:

- `src/agents/random_agent.py` — uniform-random over
  `game.legal_moves(state)`. Seedable via `seed=` kwarg.
- `src/agents/human.py` — `AyoHumanAgent` that prompts with 1..6 labels,
  re-prompts on non-integer, out-of-range, or illegal pit. Takes
  injectable `input_fn` / `output_fn` so tests can drive it.
- `src/cli.py` — single entrypoint (`python -m src.cli`). Argparse with
  `--p0`, `--p1`, `--seed`. Renders state each turn, prints "P0 plays
  pit 3 (label)", shows final stores and winner.
- `tests/test_agents.py` — random never picks illegal; same seed →
  deterministic; human round-trips labels/pits; re-prompts on bad input;
  `play_game()` runs two random agents to terminal without error.

**Decisions locked in (user):**
- **Pit labels:** 1..6 relative, both players. P0 label 1 = pit 0;
  P1 label 1 = pit 12 (display-left-to-right mapping, so each player
  reads their own row left-to-right from their seated perspective).
- **Entry point:** single `python -m src.cli`. No separate script.
- **Label mapping on-board:** shown in `Ayo.render()` itself (not just
  the CLI), above P1's row and below P0's row.

### Phase 3 — Connect Four + minimax (validation baseline)

**Goal:** prove the minimax implementation is correct on a game we already
understand, *before* trusting it on Ayo.

- `src/games/connect_four.py` — 7×6 board, same `Game` interface.
- `src/agents/minimax.py` — negamax with alpha-beta, iterative deepening
  with a time budget per move, transposition table keyed on the state's
  hash. Return `(move, stats)` with node counts.
- `tests/test_connect_four.py` — mate-in-N puzzles, minimax > random at
  even shallow depth, alpha-beta returns same move as plain minimax.
- Empirical check: at depth N, alpha-beta visits measurably fewer nodes
  than plain minimax on the same position.

Decisions to raise:
- Iterative deepening time budget: seconds, or node budget, or both? Default
  to seconds (more standard for didactic purposes).
- Transposition table: Zobrist hashing is overkill for this size — Python's
  built-in `hash(state)` on the frozen dataclass is fine. Confirm.

### Phase 4 — Minimax for Ayo with 4 heuristics

**Goal:** port the minimax code to Ayo, pluggable heuristics.

- `src/heuristics/ayo_heuristics.py` with 4 functions that take `(AyoState,
  player) -> float`:
    - **H1:** `stores[me] - stores[opp]`
    - **H2:** H1 + mobility bonus `α * (|legal_moves(me)| - |legal_moves(opp)|)`
    - **H3:** H2 + next-move capture potential (count pits where we could
      capture next turn if we had the move)
    - **H4:** H3 − vulnerability penalty (pits on our side holding 1–2 seeds
      that the opponent could capture next turn)
- Minimax takes a `heuristic=` kwarg so you can swap without re-instantiating.
- Unit tests: each heuristic returns opposite signs for (state, 0) vs. (state, 1).

Decisions to raise:
- Weights for H2/H3/H4 mixing terms. Start with 1.0 each; tune empirically.
- Depth bound when time budget exhausted mid-ply: return best-so-far from
  iterative deepening, not partial search. Standard practice — just confirm.

### Phase 5 — Tabular Q-learning via self-play

**Goal:** a working Q-learning agent that plays legal Ayo and improves over
training. Be honest in the report: it will underperform minimax, and that's
expected.

- `src/agents/qlearning.py`
    - `Q: dict[tuple[StateKey, Move], float]` — lazy (missing = 0.0).
    - State key = `state.q_key()` — already omits ply.
    - Policy: epsilon-greedy with decaying epsilon over episodes.
    - Update rule: standard Q-learning bootstrap with `max_{a'} Q(s', a')`
      over **legal moves at s'** only.
    - Self-play: both players update *their own* Q-table (symmetric game, so
      one shared table with role-flipping is fine — document the choice).
    - Hyperparameters exposed as kwargs with sensible defaults (α=0.1,
      γ=0.99, ε₀=1.0, ε_min=0.05, decay linear over training).
    - Save/load Q-table to disk (pickle or JSON — pickle is easier for
      tuple-keyed dicts).
- Tests: Q-update shape (single known transition), never selects illegal
  moves, epsilon=0 agent is deterministic.

Decisions to raise:
- Shared Q-table (flip role) vs. separate tables per seat. Shared is simpler
  and standard for symmetric games; recommend shared.
- Training budget: 50k–200k episodes feels right. Confirm before running.
- Reward shape: ±1 at terminal only, or intermediate shaping via store
  deltas? Start with sparse ±1; mention shaped reward as a discussion point
  in the report.

### Phase 6 — Evaluation harness

**Goal:** reproducible N-game tournaments between any two agents with
metrics ready to drop into the report.

- `src/evaluate.py`
    - CLI: `--p0 minimax --p1 qlearning --n 200 --out results.csv`
    - Per-game metrics: winner, plies, avg decision time per move per side,
      minimax nodes visited, store score margin.
    - Aggregate: win rate, 95% CI on win rate (Wilson interval — numpy
      only), avg game length.
- Output: CSV that pandas can read for the notebook.

Decisions to raise:
- Should we swap seats halfway (P0 = A for games 1..N/2, P0 = B for games
  N/2+1..N) to wash out first-move advantage? Standard practice — recommend
  yes.

---

## 8. Working-with-the-user conventions

Read `memory/` for the long-form versions. Summary:

- **Design-first.** For anything non-trivial, propose the design (options +
  trade-offs) before writing code. The user wants to learn, and wants to
  catch bad decisions before they ossify.
- **Ask when trade-offs are real.** Don't silently pick one. If it's a
  judgment call, name the options and recommend one — but let the user
  decide.
- **Stop at phase boundaries.** Summarize what changed, what tests pass,
  what's next. Wait for approval before continuing.
- **Every phase is tested.** The user explicitly wants "aggressive test
  coverage on edge cases". Don't ship a phase with untested logic.
- **Venv is non-negotiable.** Python 3.13.8 in `.venv/`. Never `pip install`
  into global Python. Always `source .venv/bin/activate` first.
- **No copying from public Ayo/Oware repos.** TurnItIn checks submitted
  code. Reference them *only* for rule clarification.
- **Comments explain WHY, not WHAT.** If a line is doing something
  non-obvious (relay semantics, skip-origin nuance, why ply is in the state
  but not the Q-key), a short comment is welcome. Avoid narrating the
  obvious.
- **Type hints throughout.** Small, testable functions. The user should be
  able to explain any line to their professor.
- **Line length 100** (`.flake8`). `E203` and `W503` ignored.
- **AI_log.md** — user maintains this themselves. If the user attributes a
  suggestion to us, they'll write it.

---

## 9. Exact next action for the incoming agent

Phase 2 is mid-flight. Resume by:

1. Write `src/agents/random_agent.py` (seedable; raises if no legal
   moves).
2. Write `src/agents/human.py` — `AyoHumanAgent` with 1..6 label I/O,
   injectable `input_fn`/`output_fn`, re-prompt on bad input.
3. Write `src/cli.py` — `python -m src.cli --p0 {human,random} --p1 ...
   [--seed N]`. Turn-by-turn render, per-move log, final score.
4. Write `tests/test_agents.py` — cover RandomAgent (legal-only,
   deterministic with seed, raises on terminal), AyoHumanAgent (label/pit
   bijection, valid input, re-prompt on bad/illegal), and a smoke test
   for `play_game()` with two random seeded agents running to terminal.
5. `pytest tests/ -q` should be green. Update §0 changelog with what
   landed, then ask the user to playtest the CLI before moving to Phase
   3. Remind them `source .venv/bin/activate` first.

**Do not** start Phase 3 until the user has actually played a game in
the CLI — that playtest is what Phase 2 exists to enable.

---

## 10. Fact-checker agent reports (context for why the open items exist)

Three agents were run in parallel on the Phase 1 output:

- **Test-trace verifier** (general-purpose subagent): independently
  hand-traced all 5 complex test expected values. **All matched.** High
  confidence the tests are correct, not coincidentally passing. Suggested
  the two additional tests in §5.
- **Code reviewer** (general-purpose subagent): flagged the `_sow` iteration
  cap (§6a) and the duplicated terminal detection (§6b). Confirmed the
  following were *correct*: capture math, opposite-pit domain, store-skip,
  sweep destinations, winner tie-handling, ply-limit semantics, initial
  seed count, validation boundaries.
- **Rules auditor** (claude-code-guide subagent): blocked on web
  permissions. Manual verification against Wikipedia + Mancala Fandom had
  already been done earlier in the design phase, so this is not a blocker.

---

## 11. Small gotchas to remember

- `AyoState.__eq__` compares all three fields including `ply`, but
  `q_key()` intentionally drops `ply`. So `s1 == s2` and `s1.q_key() ==
  s2.q_key()` are different questions. Q-learning uses the latter.
- `apply_move` flips `to_move` and increments `ply` *always* — including
  when the move ends the game. Callers should use `is_terminal(s)` to
  check, not the presence/absence of legal moves (they're equivalent, but
  the intent is clearer).
- `_finalize_if_terminal` runs AFTER the turn has flipped, so "mover with
  empty side" inside that method means *the new player to move has an empty
  side*, i.e. the *previous* mover just took their last seed or captured
  everything. The variable naming in that method follows the post-flip
  convention (`player = state.to_move`, i.e. the new mover). Tests assume
  this — don't rename without checking.
- Relay sowing has a **defensive budget** (`Ayo._SOW_BUDGET = 10_000`)
  that raises `RuntimeError` on overflow. It will never fire on a legal
  48-seed board; if it does, you've built a bug that corrupts state.
- `render()` lays out P1's row left-to-right as pits 12, 11, 10, 9, 8, 7
  (because sowing is counterclockwise from P0 pit 5 → P1 pit 7 → ... →
  pit 12), but the labels shown above it are 1..6 — so P1 reading
  left-to-right sees "1 2 3 4 5 6" even though the underlying pits are
  12..7. Don't "fix" the pit order without also flipping the label-to-pit
  mapping in `AyoHumanAgent` (when that lands) — the two are coupled.
- **Label ↔ pit mapping** (for any code that prompts the user or prints
  moves): P0 label n ∈ {1..6} → pit n−1; P1 label n ∈ {1..6} → pit 13−n.
  Reverse: P0 pit i → label i+1; P1 pit i → label 13−i.



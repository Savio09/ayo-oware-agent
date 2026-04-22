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

### 2026-04-22 — Experiment batch completed and relay-cycle rule accepted

- **Long Q-learning training exposed a rules edge case:** 50k self-play found
  a reachable relay-sowing cycle where a candidate move never reached an empty
  final pit.
- **User-approved computational convention:** intra-move relay cycles are
  distinct from inter-move repeated positions. Moves whose relay sowing repeats
  an exact sow-state are illegal and filtered out of `legal_moves()`. The
  existing 200-ply safeguard remains the only inter-move cycle handling.
- **Ayo legality hardened under that convention:** `legal_moves()` now filters
  out nonterminating relay moves, `_sow()` detects repeated relay states, and
  `apply_move()` rejects cyclic candidates as ordinary illegal moves rather
  than crashing.
- **Regression test added:** `tests/test_ayo_rules.py` covers the discovered
  cyclic state and verifies the nonterminating move is not legal.
- **Independent verification:** three spawned verifier agents reviewed the
  relay-cycle fix, Q-learning path, evaluator contract, and experiment
  methodology. Their low-risk evaluator findings were incorporated.
- **Evaluator cleanup after review:** fixed-depth no-time-cap minimax now
  records a blank `minimax_time_limit_s` in CSV output and the CLI accepts
  `--minimax-time none`. Q-learning agent construction now requires the
  logical side (`A` or `B`) so checkpoint paths cannot be silently mixed.
- **Q-learning checkpoint trained:** `artifacts/qlearning_50k_seed152.pkl`
  was trained for 50,000 self-play episodes. Metadata is recorded in
  `artifacts/qlearning_50k_seed152_metadata.json`; the `.pkl` file is ignored
  by git to avoid committing a 47 MB artifact. This checkpoint was generated
  after the intra-move relay-cycle filter was in place.
- **Final experiment batch completed:** CSVs, metadata, and a summary README
  live under `results/phase6_seed20260422_depth3_final/`. This final batch was
  generated after the intra-move relay-cycle filter was in place.
- **Report tables drafted first:** `results/phase6_seed20260422_depth3_final/report_tables.md`
  groups the final batch into report-ready tables for agents-vs-random,
  Q-learning-vs-minimax, and pairwise minimax comparisons. No extra experiments
  were run for these tables.
- **Headline results:** depth-3 minimax H1-H4 each beat random 100/100;
  the 50k Q-learning checkpoint beat random 61/100 with 3 draws; the same
  Q-learning checkpoint lost 0/100 to each depth-3 minimax heuristic. Pairwise
  minimax heuristic matches split 30/30 after seat swapping in this batch, so
  use margins/game length rather than overclaiming heuristic win ordering.
- **Verification:** full suite is 87/87 passing. `compileall` and
  `git diff --check` pass.

### 2026-04-22 — Phase 6 implemented and verified

- **Evaluation harness added:** `src/evaluate.py` implements testable
  functions (`make_agent`, `run_game`, `run_tournament`, `summarize_results`,
  `write_results_csv`, `wilson_interval`) plus a thin CLI.
- **Reproducibility tightened:** tournaments build fresh agent instances for
  every game. Random agents receive deterministic per-game, per-seat seeds
  derived from the tournament seed, game index, and seat.
- **Seat-swapping default:** Agent A plays P0 for the first half of games and
  Agent B plays P0 for the second half. Odd game counts give Agent A one extra
  P0 game.
- **CSV contract locked:** rows use `winner_player` = `0`, `1`, or `-1` for
  draws; `winner_agent` = `A`, `B`, or `draw`; `store_margin_for_a` always
  means stores(agent A) minus stores(agent B), independent of seat.
- **Measurement fields added:** rows include move counts, timing totals and
  averages, minimax move counts, minimax nodes/cutoffs, minimax depth averages
  over minimax moves only, and minimax depth/time settings.
- **Q-learning checkpoint handling:** CLI supports separate
  `--agent-a-q-path` and `--agent-b-q-path`, so qlearning-vs-qlearning can
  compare different checkpoints without ambiguity.
- **Summary output:** reports Agent A/B wins, draws, Agent A win rate over all
  games, decisive-games win rate, Wilson 95% CI for Agent A wins over all
  games (draws count as non-wins), average plies, store margin, timing, and
  minimax nodes.
- **Phase 6 tests added:** `tests/test_evaluate.py` has 10 tests covering CSV
  output, seat swapping, winner mapping, Agent A store margin, mixed
  random/minimax stat fields, Wilson intervals, all-games CI summary,
  deterministic seeding, Q-learning side-specific paths, fixed-depth CLI
  parsing, and clear bad-input failures.
- **Verification:** full suite is 87/87 passing after the experiment-driven
  relay-cycle regression test. `compileall` and
  `git diff --check` pass.

### 2026-04-22 — Phase 5 implemented and verified

- **Q-learning agent added:** `src/agents/qlearning.py` implements
  `QLearningAgent`, `TrainingStats`, and `train_self_play()` for tabular Ayo
  self-play.
- **Zero-sum update clarified in code:** Q-values are from the current
  player's perspective. Rewards are measured from the player who took the
  action in `state`, not `next_state.to_move`. Nonterminal bootstraps use
  `target = reward - gamma * max_next_q`; terminal next states use reward only.
- **Shared-table semantics locked:** keys are `(state.q_key(), move)`;
  `q_key()` already includes `to_move` and omits `ply`, so no extra
  role-flipping or board canonicalization is used.
- **Exploration isolated to training:** `select_move()` is greedy for normal
  play/evaluation. Self-play uses an internal epsilon-greedy helper with a
  linear decay schedule.
- **Persistence added:** `save()` / `load()` pickle the Q-table plus metadata
  (`format_version`, `alpha`, and `gamma`).
- **Phase 5 tests added:** `tests/test_qlearning.py` has 9 tests covering
  default Q-values, greedy tie-breaking, epsilon legal moves, terminal-state
  raises, acting-player terminal reward, terminal-no-bootstrap behavior via the
  same test, zero-sum nonterminal bootstrapping, illegal update rejection,
  self-play stats including average plies, and save/load round-tripping.
- **Verification:** full suite is 76/76 passing. `compileall` and
  `git diff --check` pass.

### 2026-04-22 — Phase 4 implemented and verified

- **Ayo heuristic module added:** `src/heuristics/ayo_heuristics.py`
  provides `ayo_h1`..`ayo_h4`, `make_ayo_h2`..`make_ayo_h4`, direct helper
  functions for store differential, counterfactual mobility, immediate
  finalized store-gain potential, and deterministic Ayo move ordering.
- **Reuse of Phase 3 minimax confirmed:** Phase 4 did not change
  `MinimaxAgent`; Ayo minimax is configured through `heuristic=` and
  `move_order=`. Terminal states still use the minimax terminal-score path;
  H1-H4 are only nonterminal cutoff evaluations.
- **Design clarifications implemented:** H3/H4 are documented as immediate
  store-gain potential rather than pure capture potential, counterfactual
  `to_move` replacement is documented, tuning weights are factory parameters,
  and the move-order helper documents its extra `apply_move()` cost.
- **Phase 4 tests added:** `tests/test_ayo_heuristics.py` has 10 tests for
  H1-H4, factory weights, helper computations behind H3/H4, deterministic
  move ordering, Ayo minimax integration, robust tactical move choice, and the
  terminal-child path that must bypass heuristics.
- **Verification:** full suite is 67/67 passing. `compileall` and
  `git diff --check` pass.
- `AI_log.md` was initially left untouched until the user later explicitly
  asked for it to be updated.

### 2026-04-22 — Phase 4 heuristic design refined

- User approved the Phase 4 direction but required tighter definitions before
  coding.
- H3/H4 should be described honestly as **immediate store-gain potential**,
  not pure capture potential, because `Ayo.apply_move()` returns finalized
  states and store deltas may include terminal sweeps.
- Mobility and immediate-gain helpers may use `dataclasses.replace(state,
  to_move=player)`, but must document this as a counterfactual heuristic
  feature from each side's perspective on the same board.
- Keep exported defaults (`ayo_h1`..`ayo_h4`) and add factory helpers
  (`make_ayo_h2`..`make_ayo_h4`) so later weight tuning is reproducible without
  editing module globals.
- Ayo move ordering by descending immediate store gain then pit index is
  accepted. Document the extra `apply_move()` overhead and why it is acceptable
  for Ayo's branching factor (at most 6).
- Add direct unit tests for helper computations behind H3/H4, plus a robust
  tactical minimax state where one move has a clearly superior immediate store
  consequence.
- Heuristics are for nonterminal cutoffs only. True terminal states remain
  scored by `MinimaxAgent`'s terminal path.
- Do **not** edit `AI_log.md` during this Phase 4 implementation unless the
  user explicitly asks.

### 2026-04-21 — Phase 4 design approved to begin

- User approved continuing past the Phase 3 boundary.
- Phase 4 is now active at the design step. Do not implement Ayo minimax or
  heuristics until the Phase 4 design proposal is reviewed.

### 2026-04-21 — Phase 3 implemented and verified

- **Connect Four rules engine added:** `src/games/connect_four.py` implements
  immutable `ConnectFourState`, bottom-left row-major board indexing, gravity,
  legal moves, full-column rejection, horizontal/vertical/diagonal win
  detection, draw terminals, and rendering.
- **Reusable minimax agent added:** `src/agents/minimax.py` implements
  `MinimaxAgent`, `SearchStats`, fixed-depth minimax for deterministic tests,
  optional alpha-beta pruning, optional exact-only transposition caching,
  center-first Connect Four move ordering, and a simple Connect Four heuristic.
- **Phase 3 tests added:** `tests/test_connect_four.py` has 9 rule/render tests;
  `tests/test_minimax.py` has 8 tactical/search tests, including immediate win,
  forced block, deterministic tie-breaking, terminal-score dominance,
  alpha-beta equivalence to plain minimax with TT disabled, and alpha-beta node
  reduction with TT disabled.
- **Verification:** full suite is 57/57 passing. `compileall` and
  `git diff --check` pass.

### 2026-04-21 — Phase 3 final design clarifications approved

- User approved the revised Phase 3 direction with final clarifications before
  implementation.
- `heuristic(game, state, player)` must treat `player` as the root/perspective
  player, not necessarily `state.to_move`.
- Terminal search scores must dominate heuristic values. Use a fixed
  `WIN_SCORE` larger than any expected heuristic magnitude; prefer shorter
  wins and longer losses by adjusting terminal scores by distance from root.
- `SearchStats.nodes` means the number of recursive search calls entered. Use
  that definition consistently for plain minimax and alpha-beta comparisons.
- Default Phase 3 Connect Four heuristic: center-column preference plus
  window-of-four scoring for open own/opponent lines, with a stronger penalty
  for immediate opponent threats.

### 2026-04-21 — Phase 3 design review feedback incorporated

- User reviewed the initial Phase 3 proposal and approved the direction but
  required tighter design before implementation.
- Locked Phase 3 design requirements: `MinimaxAgent` must accept a pluggable
  `heuristic=` callable; nonterminal depth-cutoff leaves must use that
  heuristic; Connect Four gets its own simple heuristic for Phase 3.
- Transposition-table rule: do **not** key by raw `hash(state)`. Use frozen
  state objects directly, make entries depth-aware, and keep TT disabled in
  alpha-beta-vs-plain-minimax comparison tests so pruning is isolated from
  caching.
- Determinism rule: use explicit move ordering and tie-breaking. For Connect
  Four, search columns center-first `(3, 2, 4, 1, 5, 0, 6)` and pick the first
  move in that order among equal scores.
- `last_stats` should be a typed `SearchStats` dataclass, reset on every
  search, with fields such as `nodes`, `cutoffs`, `depth_completed`,
  `elapsed_s`, and optional `tt_hits`.
- Connect Four board indexing must be documented before coding.

### 2026-04-21 — Phase 2 playtest passed; Phase 3 kickoff

- **User playtested Phase 2 CLI as P0** through a complete human-vs-random
  game, including invalid input (`banana`) and an empty/illegal pit selection.
  The transcript was replayed through the engine move-by-move; every accepted
  move was legal, every printed state matched the rules engine, seeds stayed
  conserved at 48, and the final result (P0 wins 38-10) was correct.
- **Phase 2 is fully accepted.** The only minor UI note is that terminal boards
  still show `to move: P{next}` after a terminal move because `apply_move`
  flips turns even at game end. This is internally consistent and not a blocker.
- **Phase 3 is now active.** Start with a short design proposal for
  `ConnectFourState`, `ConnectFour`, and the reusable minimax/alpha-beta agent
  before writing code.

### 2026-04-21 — Phase 2 verified on `codex-handoff`

Phase 2 is now code-complete and verified on branch `codex-handoff`:

- **`src/agents/random_agent.py`** exists and implements a seedable
  uniform-random agent over `game.legal_moves(state)`, raising on terminal
  states.
- **`src/agents/human.py`** exists and implements `AyoHumanAgent` with
  player-relative pit labels 1..6, injectable I/O, and re-prompts for
  non-integer, out-of-range, or illegal moves.
- **`src/cli.py`** exists and provides `python -m src.cli` with `--p0`,
  `--p1`, and `--seed`. It renders each turn, logs player-relative labels,
  and prints final stores and result.
- **Phase 2 hardening after review:** `Ayo.apply_move()` now rejects moves
  outside `legal_moves()` (including feeding-illegal moves), and
  `play_game()` fails fast if an agent returns an illegal move.
- **Tests expanded:** `tests/test_ayo_rules.py` now has 26 tests and
  `tests/test_agents.py` now has 14 tests. Added coverage for feeding-illegal
  `apply_move`, render label order, human terminal raises, illegal agent
  output, verbose label logging, and CLI `main(argv)` factory/seed wiring.
  Full suite: 40/40 passing.

### 2026-04-21 — Phase 2 kickoff

Initial Phase 2 work:

- **Render updated** to show player-relative pit labels (1..6) above P1's
  row and below P0's row. Each player reads their own row left-to-right as
  "1 2 3 4 5 6". Internal pit indices no longer printed in render.
  `src/games/ayo.py:112-134`.
- **`src/agents/base.py`** created — abstract `Agent[StateT, MoveT]` ABC
  with `select_move(game, state) -> MoveT` and a `name` property.
- **`src/agents/__init__.py`** created (empty).

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
- **User writes the report separately** (3 pages). Our job is the code and the
  analysis inputs (tables, figures). The user maintains `AI_log.md` unless
  they explicitly ask us to edit it.
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

**Phase 1 is complete** (rules engine + 27 passing tests + fact-checked +
both flagged issues fixed + README written). **Phase 2 is complete and
playtested** (human/random agents, playable CLI, hardened move validation, and
14 agent/CLI tests). **Phase 3 is complete** (Connect Four + reusable minimax
baseline, 17 tests). **Phase 4 is complete** (Ayo H1-H4 heuristics plus
minimax configuration helpers, 10 tests). **Phase 5 is complete** (tabular
Q-learning self-play, 9 tests). **Phase 6 is complete** (evaluation harness,
10 tests). The code phases are complete and the first experiment batch has
been run. Next work is using the CSV outputs for the report. See §0 for the
blow-by-blow.

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
│   ├── cli.py                    # playable human/random terminal runner
│   ├── evaluate.py               # tournament harness + CSV metrics
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py               # abstract Agent[StateT, MoveT] ABC
│   │   ├── human.py              # AyoHumanAgent for CLI play
│   │   ├── minimax.py            # reusable minimax / alpha-beta agent
│   │   ├── qlearning.py          # tabular Ayo Q-learning + self-play
│   │   └── random_agent.py       # seedable random baseline
│   ├── heuristics/
│   │   ├── __init__.py
│   │   └── ayo_heuristics.py     # Ayo H1-H4 + move ordering helpers
│   └── games/
│       ├── __init__.py
│       ├── base.py               # abstract Game[StateT, MoveT] ABC
│       ├── ayo.py                # AyoState + Ayo rules engine
│       └── connect_four.py       # Connect Four validation baseline
└── tests/
    ├── __init__.py
    ├── test_agents.py            # 14 passing Phase 2 tests
    ├── test_ayo_heuristics.py    # 10 passing Phase 4 tests
    ├── test_ayo_rules.py         # 27 passing Ayo rule tests
    ├── test_connect_four.py      # 9 passing Phase 3 rules tests
    ├── test_evaluate.py          # 10 passing Phase 6 tests
    ├── test_minimax.py           # 8 passing Phase 3 search tests
    └── test_qlearning.py         # 9 passing Phase 5 tests
```

### What does NOT exist yet (to avoid confusion)

- `notebooks/analysis.ipynb` — user will deal with this during analysis phase.

### How to run things

```bash
# Activate the venv — always do this first, never use system Python.
source .venv/bin/activate

# Run tests
pytest tests/ -q           # currently: 87 passed

# Play a game: human P0 vs. random P1
python -m src.cli

# Seeded random-vs-random smoke game
python -m src.cli --p0 random --p1 random --seed 42

# Seeded evaluation tournament with CSV output
python -m src.evaluate \
  --agent-a minimax_h4 --agent-b random \
  --n 20 --seed 42 --out results.csv \
  --minimax-time none

# Lint (the user hasn't asked for lint-on-commit; run when touching files)
flake8 src tests           # not installed in the current venv as of 2026-04-21

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
| Inter-move repeated-position handling | None. Use the **200-ply safety valve** only.                               |
| Intra-move relay-cycle handling       | Nonterminating relay moves are illegal and filtered from `legal_moves`.    |
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
- **`apply_move` enforces full move legality.** A move must be in
  `legal_moves(state)`, not just on the mover's side and non-empty. This
  matters for feeding-rule positions and for future search agents.
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

All 27 tests in `tests/test_ayo_rules.py` pass. Coverage hits:

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
- `apply_move` rejects feeding-illegal moves excluded by `legal_moves`
- feeding impossible → terminal; sweep direction correct
- mover-side-empty → opp collects
- ply-limit terminal: winner by stores, draw if tied
- render produces multi-line string and preserves player-relative label order
- nonterminating relay-cycle moves are excluded from `legal_moves`

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

### Phase 2 — Game-playing CLI + random agent (complete)

**Goal:** the user can play Ayo in the terminal vs. a random opponent to
sanity-check the feel before AI lands.

**Status:** implemented, tested, and playtested by the user on 2026-04-21.

- `src/agents/random_agent.py` — uniform-random over
  `game.legal_moves(state)`. Seedable via `seed=` kwarg.
- `src/agents/human.py` — `AyoHumanAgent` that prompts with 1..6 labels,
  re-prompts on non-integer, out-of-range, or illegal pit. Takes
  injectable `input_fn` / `output_fn` so tests can drive it.
- `src/cli.py` — single entrypoint (`python -m src.cli`). Argparse with
  `--p0`, `--p1`, `--seed`. Renders state each turn, prints player-relative
  move labels, shows final stores and winner.
- `tests/test_agents.py` — 14 tests covering RandomAgent, AyoHumanAgent,
  `play_game()`, invalid agent output, verbose move logs, and CLI
  `main(argv)` factory/seed wiring.

**Decisions locked in (user):**
- **Pit labels:** 1..6 relative, both players. P0 label 1 = pit 0;
  P1 label 1 = pit 12 (display-left-to-right mapping, so each player
  reads their own row left-to-right from their seated perspective).
- **Entry point:** single `python -m src.cli`. No separate script.
- **Label mapping on-board:** shown in `Ayo.render()` itself (not just
  the CLI), above P1's row and below P0's row.

### Phase 3 — Connect Four + minimax (validation baseline) (complete)

**Goal:** prove the minimax implementation is correct on a game we already
understand, *before* trusting it on Ayo.

**Status:** implemented and tested on 2026-04-21.

- `src/games/connect_four.py` — 7x6 board, same `Game` interface. Board
  indexing convention must be explicit in the module docstring and render
  tests.
- `src/agents/minimax.py` — reusable negamax/minimax agent with alpha-beta,
  fixed-depth mode for deterministic tests, and seconds-based iterative
  deepening for play. It must take a pluggable `heuristic(game, state, player)`
  callable rather than baking in Connect Four evaluation. The `player`
  argument means the root/perspective player whose score is being evaluated,
  not necessarily `state.to_move`.
- Terminal scoring — use a fixed `WIN_SCORE` that safely dominates heuristic
  values. Prefer shorter wins and longer losses by adjusting terminal values
  with distance from root, e.g. win = `WIN_SCORE - distance`, loss =
  `-WIN_SCORE + distance`.
- `SearchStats` dataclass — stable stats contract for later evaluation:
  `nodes`, `cutoffs`, `depth_completed`, `elapsed_s`, and `tt_hits` if TT is
  enabled. `nodes` means recursive search calls entered.
- Default Connect Four heuristic — center-column preference plus
  window-of-four scoring based on counts of own pieces, opponent pieces, and
  empties. Reward open own twos/threes, score wins very highly, penalize open
  opponent twos/threes, and penalize immediate opponent three-in-a-row threats
  more strongly.
- Move order / ties — deterministic ordering is required. Connect Four should
  use center-first columns `(3, 2, 4, 1, 5, 0, 6)`. Equal scores choose the
  first move in search order.
- Transposition table — optional after plain minimax and alpha-beta are
  correct. If implemented, use frozen state objects directly, never raw
  `hash(state)` ints; entries must be depth-aware. For alpha-beta comparison
  tests, disable TT to isolate pruning.
- `tests/test_connect_four.py` — gravity, legal moves, full-column rejection,
  horizontal/vertical/diagonal wins, draw detection, and render/indexing.
- `tests/test_minimax.py` — immediate win, forced block, alpha-beta same move
  as plain minimax under identical move ordering, and alpha-beta fewer nodes
  than plain minimax with TT disabled. Minimax-vs-random can be kept as a smoke
  test, not a primary correctness proof.
- Full Phase 3 coverage currently: 17 tests.

Approved defaults unless user revises:
- Seconds-based time budgets plus fixed-depth mode for deterministic tests.
- No Zobrist hashing at this scale.

### Phase 4 — Minimax for Ayo with 4 heuristics (complete)

**Goal:** port the minimax code to Ayo, pluggable heuristics.

**Status:** implemented and tested on 2026-04-22.

- `src/heuristics/ayo_heuristics.py` with 4 functions that take
  `(game, state, player) -> float`, where `player` is the root/perspective
  player:
    - **H1:** `stores[me] - stores[opp]`
    - **H2:** H1 + mobility bonus `α * (|legal_moves(me)| - |legal_moves(opp)|)`
    - **H3:** H2 + immediate store-gain potential differential
    - **H4:** H3 − extra vulnerability penalty based on opponent immediate
      store-gain potential
- Minimax takes a `heuristic=` kwarg so you can swap without re-instantiating.
- Provide default exported heuristics plus `make_ayo_h2`, `make_ayo_h3`, and
  `make_ayo_h4` factories for reproducible tuning.
- Unit tests: store differential, mobility, immediate store-gain helpers,
  vulnerability penalty, factory weights, legal Ayo minimax moves, and a
  robust tactical state where minimax chooses the clearly superior immediate
  store-gain move.
- `make_ayo_minimax_agent()` provides a Phase 4 convenience configuration:
  `ayo_h4`, depth 4, 1-second time budget, alpha-beta enabled, TT disabled,
  and immediate-gain move ordering.
- Full Phase 4 coverage currently: 10 tests.

Locked decisions:
- Default weights are placeholders, not tuned values. They are explicit and
  adjustable through factories.
- Ayo move ordering uses immediate store gain then pit index. This costs extra
  `apply_move()` calls but is acceptable because Ayo has at most six legal
  moves.

### Phase 5 — Tabular Q-learning via self-play (complete)

**Goal:** a working Q-learning agent that plays legal Ayo and improves over
training. Be honest in the report: it will underperform minimax, and that's
expected.

**Status:** implemented and tested on 2026-04-22.

- `src/agents/qlearning.py`
    - `Q: dict[tuple[StateKey, Move], float]` — lazy (missing = 0.0).
    - State key = `state.q_key()` — includes `to_move` and omits `ply`.
    - Shared table: no role-flipping and no board canonicalization; both
      players' states live in the same dict under different `to_move` keys.
    - `select_move()` is greedy for normal play/evaluation.
    - `train_self_play()` uses epsilon-greedy self-play with linear epsilon
      decay.
    - Sparse rewards: nonterminal `0.0`; terminal utility from the acting
      player's perspective.
    - Zero-sum update: terminal next state `target = reward`; otherwise
      `target = reward - gamma * max_next_q`.
    - Hyperparameters exposed as kwargs with defaults `alpha=0.1`,
      `gamma=0.99`.
    - `TrainingStats` records episodes, Q-entry count, wins/draws, total
      plies, and average plies.
    - `save()` / `load()` pickle the Q-table with `format_version`, `alpha`,
      and `gamma` metadata.
- Full Phase 5 coverage currently: 9 tests.

Recommended training budget for actual experiments:
- Start with 50k self-play episodes.
- Move to 100k or 200k only if runtime is acceptable and the early evaluation
  curve suggests more training is useful.

### Phase 6 — Evaluation harness (complete)

**Goal:** reproducible N-game tournaments between any two agents with
metrics ready to drop into the report.

**Status:** implemented and tested on 2026-04-22.

- `src/evaluate.py`
    - CLI entrypoint: `python -m src.evaluate`
    - Example args:
      `--agent-a minimax_h4 --agent-b random --n 200 --out results.csv`
    - Supported specs: `random`, `qlearning`, `minimax_h1`, `minimax_h2`,
      `minimax_h3`, `minimax_h4`.
    - Q-learning checkpoints: use `--agent-a-q-path` and/or
      `--agent-b-q-path` depending on which logical agent is `qlearning`.
    - Agents are instantiated fresh per game; random seeds derive from the
      tournament seed, game index, and seat.
    - Seat swapping is on by default; disable with `--no-seat-swap`.
    - Per-game CSV metrics: winner, logical winner, store counts,
      `store_margin_for_a`, plies, per-seat move counts, timing, minimax move
      counts, minimax nodes/cutoffs, minimax depth averages, and minimax
      depth/time settings.
    - Aggregate stdout summary: Agent A/B wins, draws, all-games and
      decisive-games Agent A win rates, Wilson 95% CI over all games, average
      plies, average Agent A store margin, average decision time, and minimax
      nodes by logical agent.
- Output: CSV that pandas can read for the notebook.
- Full Phase 6 coverage currently: 10 tests.

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

All planned code phases are complete and the first report-oriented experiment
batch has been run. Next work should be report support:

- use `results/phase6_seed20260422_depth3_final/summary.csv` and per-matchup
  CSVs for tables/figures;
- cite `results/phase6_seed20260422_depth3_final/README.md` for the concise
  interpretation notes;
- cite `artifacts/qlearning_50k_seed152_metadata.json` for Q-learning training
  provenance;
- if time allows, run larger `n` or deeper minimax experiments before making
  stronger claims about H1-H4 ordering.

Keep `progress.md` updated after each meaningful experiment checkpoint. Update
`AI_log.md` when the user asks or when agreed as part of the current phase.
let'
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
  mapping in `AyoHumanAgent` — the two are coupled.
- **Label ↔ pit mapping** (for any code that prompts the user or prints
  moves): P0 label n ∈ {1..6} → pit n−1; P1 label n ∈ {1..6} → pit 13−n.
  Reverse: P0 pit i → label i+1; P1 pit i → label 13−i.

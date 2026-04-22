AI Statement / Collaboration Log

- I used AI to collect information on how Awari works. Based on the papers I
  read, it flagged some discrepancies that were contrary to my understanding of
  the game. For example, the Awari paper describes a related but different
  ruleset, so we treated it as historical/algorithmic context rather than as
  the source of truth for Ayo rules.
- I asked AI to implement and verify the Ayo rules engine, CLI, random agent,
  and supporting tests. I reviewed the behavior at phase boundaries rather than
  treating generated code as automatically correct.
- I helped verify Phase 2 by running the terminal game myself as P0, entering
  invalid input (`banana`), trying an illegal/empty pit, and then playing a
  complete game against the random agent. I pasted the full transcript back for
  review.
- The AI replayed my full Phase 2 transcript move-by-move through the rules
  engine and confirmed that every accepted move was legal, every printed board
  state matched the implementation, seeds stayed conserved at 48, and the final
  P0 win was correctly scored.
- I directed the AI to keep `progress.md` updated as a handoff document and to
  record how I helped in this log, so future work can be audited and picked up
  cleanly by another agent.
- I reviewed the first Phase 3 design proposal and pushed back before
  implementation. I identified missing or underspecified pieces: nonterminal
  leaf evaluation, reusable pluggable heuristics, safe transposition-table
  keys and depth awareness, deterministic move ordering and tie-breaking,
  explicit Connect Four board indexing, typed search statistics, and clean
  alpha-beta-vs-minimax tests with transposition-table caching disabled.
- I reviewed the revised Phase 3 design and approved the direction with final
  clarifications: heuristic evaluation should be from the root player's
  perspective, terminal scores must dominate heuristic scores and prefer
  shorter wins/longer losses, search-node counting must be defined consistently,
  and the default Connect Four heuristic should be stated before coding.
- After those clarifications, the AI implemented the Connect Four validation
  game and reusable minimax/alpha-beta agent. The implementation followed my
  requested safeguards: pluggable root-perspective heuristics, deterministic
  center-first move ordering, typed search statistics, terminal scores that
  dominate heuristic scores, and alpha-beta comparison tests with
  transposition-table caching disabled.
- I reviewed the Phase 4 Ayo heuristic proposal before implementation and
  pushed for tighter definitions. I clarified that H3/H4 should be described
  as immediate store-gain potential rather than pure capture potential, because
  finalized Ayo moves can include terminal sweeps. I also asked for
  counterfactual mobility/gain helpers to be documented, heuristic weights to
  be exposed through factory functions, deterministic Ayo move ordering to
  acknowledge its extra `apply_move()` cost, and robust tests for helper
  computations and tactical move choice.
- After that review, the AI implemented `src/heuristics/ayo_heuristics.py`
  with Ayo H1-H4 heuristics, tuning factories, helper functions, deterministic
  immediate-gain move ordering, and a convenience Ayo minimax configuration
  that reuses the existing `MinimaxAgent` unchanged.
- The AI added `tests/test_ayo_heuristics.py` and verified Phase 4 with the
  full test suite: 67/67 tests passed. It also ran `compileall` and
  `git diff --check`; `flake8` was not available in the virtual environment.
- The AI updated `README.md` and `progress.md` to mark Phase 4 complete and to
  set the next handoff point as Phase 5 tabular Q-learning design.
- I reviewed the Phase 5 Q-learning proposal and tightened the design before
  implementation. I clarified that reward must be computed from the player who
  acted in `state`, not from `next_state.to_move`, because Ayo flips turns even
  at terminal states. I also clarified that the shared Q-table uses
  `(state.q_key(), move)` directly, with no role-flipping or board
  canonicalization.
- I asked the AI to keep normal `select_move()` greedy and isolate epsilon
  exploration to self-play training, write down the exact zero-sum Q-update,
  track average plies in training stats, persist metadata with pickled Q-tables,
  and add tests for terminal-no-bootstrap behavior and terminal-state
  `select_move()` errors.
- After those clarifications, the AI implemented `src/agents/qlearning.py`
  with `QLearningAgent`, `TrainingStats`, self-play training, sparse terminal
  rewards, zero-sum bootstrapping, and save/load support.
- The AI added `tests/test_qlearning.py` and verified Phase 5 with the full
  test suite: 76/76 tests passed. It also ran `compileall` and
  `git diff --check`.
- The AI updated `README.md` and `progress.md` to mark Phase 5 complete and to
  set the next handoff point as Phase 6 evaluation harness design.
- I reviewed the Phase 6 evaluation-harness proposal and pushed for stronger
  measurement and reproducibility details before implementation. I asked for
  fresh agent instances per game, deterministic per-game seeding, explicit
  move counts, minimax move counts, machine-consistent draw encoding,
  seat-independent Agent A store margin, a clearly labeled Wilson interval
  over all games, pure functions beneath the CLI, side-specific Q-learning
  checkpoint paths, minimax settings recorded in CSV output, and mixed
  random/minimax stat tests.
- After that review, the AI implemented `src/evaluate.py` with `make_agent`,
  `run_game`, `run_tournament`, `summarize_results`, `write_results_csv`,
  `wilson_interval`, and a thin command-line wrapper.
- The evaluator writes one CSV row per game, swaps seats by default, records
  timing and minimax search statistics, supports separate Q-learning
  checkpoints for Agent A and Agent B, and prints a concise tournament summary.
- The AI added `tests/test_evaluate.py` and verified Phase 6 with the full
  test suite: 85/85 tests passed. It also ran `compileall` and
  `git diff --check`.
- The AI updated `README.md` and `progress.md` to mark all planned code phases
  complete and identify experiment execution as the next step.
- I asked the AI to use other agents to independently verify the rules fix,
  Q-learning path, evaluator, and experiment methodology rather than relying
  only on its own self-reporting.
- During the 50k Q-learning training run, the AI found a reachable relay-sowing
  cycle. It updated the Ayo rules engine so nonterminating relay moves are
  filtered out of `legal_moves()`, added a regression test for the discovered
  state, and reran verification.
- The independent verifier agents did not find blocking issues. Their
  low-risk suggestions led the AI to make fixed-depth minimax CSV output more
  explicit, require logical-side Q-learning checkpoint selection, and record
  Q-learning checkpoint provenance.
- The AI trained a 50,000-episode Q-learning checkpoint, recorded metadata and
  a SHA-256 hash, and ran a seeded, seat-swapped experiment batch comparing
  random, minimax H1-H4, and the Q-learning checkpoint.
- The final experiment batch showed Q-learning beating random but losing to
  each depth-3 minimax heuristic, while all minimax heuristics beat random in
  the tested sample. The AI saved per-game CSVs and a summary under
  `results/phase6_seed20260422_depth3_final/`.

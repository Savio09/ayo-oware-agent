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

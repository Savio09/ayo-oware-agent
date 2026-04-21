"""Ayo (Yoruba mancala) rules engine.

Rules implemented (see README for authoritative sources and discussion):

* 12 play pits in 2 rows of 6, plus 2 stores (Kalah-style abstraction used
  here purely for accounting of captured seeds — traditional Ayoayo keeps
  captures off-board, but the abstraction makes scoring and hashing simpler).
* 48 seeds total, 4 per pit at start; stores empty.
* Sowing is counterclockwise; stores are NEVER sown into.
* Skip-origin applies per relay lap only: the pit you just emptied at the
  start of the CURRENT lap is skipped; a later relay lap may sow back into
  the original move's pit.
* Relay (multi-lap) sowing: if the last seed lands in a non-empty pit, pick
  up all seeds there and continue sowing. Sowing stops only when the last
  seed lands in an empty pit.
* Capture: when sowing stops with the last seed in an empty pit on the
  mover's own side AND the opposite pit contains seeds, the mover captures
  the opposite seeds PLUS the final seed into their store.
* Feeding: if the opponent's side is empty, the mover must play a move that
  leaves at least one seed on the opponent's side AFTER captures resolve.
  If no such move exists, the game ends and the mover keeps their own
  remaining seeds.
* Standard endgame: if the mover's side is empty at the start of their
  turn, the game ends and the opponent collects any remaining board seeds.
* Ply-limit safety valve (non-traditional): at ply 200 the game ends; seeds
  left on the board are ignored; winner decided by store counts (draw if
  tied). Documented in README.

Board layout (flat tuple, index -> pit):

::

        P1:  [12] [11] [10] [ 9] [ 8] [ 7]
    P1 store: 13                        P0 store: 6
        P0:  [ 0] [ 1] [ 2] [ 3] [ 4] [ 5]

Counterclockwise order for sowing: 0, 1, 2, 3, 4, 5, (skip 6), 7, 8, 9, 10,
11, 12, (skip 13), wrap to 0.  Opposite pit: ``12 - i`` for play pits.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, List, Optional, Tuple

from .base import Game


@dataclass(frozen=True, slots=True)
class AyoState:
    """Immutable Ayo state. Hashable for Q-learning and transposition tables."""

    pits: Tuple[int, ...]
    to_move: int
    ply: int

    def q_key(self) -> Tuple[Tuple[int, ...], int]:
        """Key used by Q-learning — omits ``ply`` so states reached via
        different move counts share a Q-value."""
        return (self.pits, self.to_move)


class Ayo(Game[AyoState, int]):
    """Ayo rules engine. Moves are int pit indices."""

    NUM_POSITIONS = 14
    P0_PITS: Tuple[int, ...] = (0, 1, 2, 3, 4, 5)
    P0_STORE = 6
    P1_PITS: Tuple[int, ...] = (7, 8, 9, 10, 11, 12)
    P1_STORE = 13
    PLY_LIMIT = 200

    # ------------------------------------------------------------------
    # Game interface
    # ------------------------------------------------------------------

    def initial_state(self) -> AyoState:
        pits = tuple([4] * 6 + [0] + [4] * 6 + [0])
        return AyoState(pits=pits, to_move=0, ply=0)

    def current_player(self, state: AyoState) -> int:
        return state.to_move

    def legal_moves(self, state: AyoState) -> List[int]:
        if state.ply >= self.PLY_LIMIT:
            return []
        player = state.to_move
        candidates = self._nonempty_pits(state, self._own_side(player))
        if not candidates:
            return []
        if not self._side_empty(state, self._opp_side(player)):
            return candidates
        # Feeding rule: opp side empty -> only moves that deliver seeds are legal.
        return self._delivering_moves(state, candidates)

    def apply_move(self, state: AyoState, move: int) -> AyoState:
        self._validate_move(state, move)
        raw = self._apply_move_raw(state, move)
        return self._finalize_if_terminal(raw)

    def winner(self, state: AyoState) -> Optional[int]:
        if not self.is_terminal(state):
            return None
        p0 = state.pits[self.P0_STORE]
        p1 = state.pits[self.P1_STORE]
        if p0 > p1:
            return 0
        if p1 > p0:
            return 1
        return None

    def render(self, state: AyoState) -> str:
        # Each player's row shows pit labels 1..6 left-to-right from THEIR
        # perspective: labels are printed above P1's row and below P0's row
        # so both players read "1 2 3 4 5 6" naturally. Internal pit indices
        # are not displayed; see README for the label<->pit mapping.
        top_indices = list(reversed(self.P1_PITS))  # 12..7 in display order
        bot_indices = list(self.P0_PITS)            # 0..5 in display order
        top = " ".join(f"[{state.pits[i]:2d}]" for i in top_indices)
        bot = " ".join(f"[{state.pits[i]:2d}]" for i in bot_indices)
        labels = " ".join(f" {n:2d} " for n in (1, 2, 3, 4, 5, 6))
        p0_store = state.pits[self.P0_STORE]
        p1_store = state.pits[self.P1_STORE]
        lines = [
            f"       {labels}",
            f"  P1:  {top}",
            f"  P1 store: {p1_store:>2}                              "
            f"P0 store: {p0_store:>2}",
            f"  P0:  {bot}",
            f"       {labels}",
            f"  to move: P{state.to_move}   ply: {state.ply}",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Side / index helpers
    # ------------------------------------------------------------------

    def _own_side(self, player: int) -> Tuple[int, ...]:
        return self.P0_PITS if player == 0 else self.P1_PITS

    def _opp_side(self, player: int) -> Tuple[int, ...]:
        return self.P1_PITS if player == 0 else self.P0_PITS

    def _own_store(self, player: int) -> int:
        return self.P0_STORE if player == 0 else self.P1_STORE

    def _opp_store(self, player: int) -> int:
        return self.P1_STORE if player == 0 else self.P0_STORE

    def _side_empty(self, state: AyoState, side: Iterable[int]) -> bool:
        return all(state.pits[i] == 0 for i in side)

    def _opposite(self, pit: int) -> int:
        # Pit i (0..5) mirrors pit 12-i (12..7). Stores are not opposites.
        return 12 - pit

    # ------------------------------------------------------------------
    # Move application
    # ------------------------------------------------------------------

    def _validate_move(self, state: AyoState, move: int) -> None:
        player = state.to_move
        own = self._own_side(player)
        if move not in own:
            raise ValueError(
                f"Move {move} is not on player {player}'s side "
                f"(valid: {list(own)})."
            )
        if state.pits[move] == 0:
            raise ValueError(f"Pit {move} is empty.")
        if state.ply >= self.PLY_LIMIT:
            raise ValueError("Ply limit reached; no moves are legal.")
        legal = self.legal_moves(state)
        if move not in legal:
            raise ValueError(
                f"Move {move} is not legal in this state; legal moves are "
                f"{legal}."
            )

    def _apply_move_raw(self, state: AyoState, move: int) -> AyoState:
        """Sow + capture + flip turn + increment ply. Does NOT finalize."""
        pits = list(state.pits)
        final_pos = self._sow(pits, move)
        self._maybe_capture(pits, final_pos, state.to_move)
        return AyoState(
            pits=tuple(pits),
            to_move=1 - state.to_move,
            ply=state.ply + 1,
        )

    # Defensive: on a legal 48-seed board sowing terminates in well under
    # this many steps. The cap only fires if a caller constructs a
    # malformed state (e.g. via a buggy feature under development) — we
    # prefer a loud failure over a hung Q-learning training run.
    _SOW_BUDGET = 10_000

    def _sow(self, pits: List[int], start: int) -> int:
        """Relay / multi-lap sowing. Mutates ``pits``; returns final pit.

        Walks counterclockwise, skipping both stores and the current lap's
        origin pit. If the last seed lands in a pit that already had seeds,
        pick them all up and begin a new lap from a new origin. Stop when
        the last seed lands in an empty pit (final pit holds exactly 1).
        """
        seeds = pits[start]
        pits[start] = 0
        relay_origin = start
        pos = start
        for _ in range(self._SOW_BUDGET):
            if seeds == 0:
                return pos
            pos = (pos + 1) % self.NUM_POSITIONS
            if pos == self.P0_STORE or pos == self.P1_STORE:
                continue
            if pos == relay_origin:
                continue
            pits[pos] += 1
            seeds -= 1
            if seeds == 0 and pits[pos] > 1:
                # Relay: the pit already held seeds before our drop.
                seeds = pits[pos]
                pits[pos] = 0
                relay_origin = pos
        raise RuntimeError(
            f"Sow did not terminate within {self._SOW_BUDGET} steps — "
            f"likely corrupt state (start={start}, pits={pits})."
        )

    def _maybe_capture(self, pits: List[int], final_pos: int, player: int) -> None:
        if final_pos not in self._own_side(player):
            return
        opp_pit = self._opposite(final_pos)
        if pits[opp_pit] == 0:
            return
        captured = pits[opp_pit] + pits[final_pos]
        pits[opp_pit] = 0
        pits[final_pos] = 0
        pits[self._own_store(player)] += captured

    def _move_delivers(self, state: AyoState, move: int) -> bool:
        """Would this move leave >= 1 seed on opp's side AFTER any capture?"""
        player = state.to_move
        raw = self._apply_move_raw(state, move)
        return not self._side_empty(raw, self._opp_side(player))

    def _nonempty_pits(
        self, state: AyoState, side: Iterable[int]
    ) -> List[int]:
        return [i for i in side if state.pits[i] > 0]

    def _delivering_moves(
        self, state: AyoState, candidates: Iterable[int]
    ) -> List[int]:
        """Subset of ``candidates`` whose sow leaves seeds on opp's side.

        Shared by ``legal_moves`` (for the feeding-rule restriction) and
        ``_finalize_if_terminal`` (to decide whether the no-delivering-move
        endgame fires). Keeping these in one place means the feeding rule
        has a single source of truth.
        """
        return [m for m in candidates if self._move_delivers(state, m)]

    def _finalize_if_terminal(self, state: AyoState) -> AyoState:
        """Sweep remaining seeds into the right store if the game just ended."""
        if state.ply >= self.PLY_LIMIT:
            # Seeds stay on board; stores alone decide winner.
            return state
        player = state.to_move
        own = self._own_side(player)
        opp = self._opp_side(player)
        if self._side_empty(state, own):
            # Current mover has no seeds -> opponent collects remaining seeds.
            return self._sweep(state, from_pits=opp, into_store=self._opp_store(player))
        if self._side_empty(state, opp):
            # Feeding required. Terminal only if no legal feeding move exists.
            candidates = self._nonempty_pits(state, own)
            if not self._delivering_moves(state, candidates):
                return self._sweep(
                    state, from_pits=own, into_store=self._own_store(player)
                )
        return state

    def _sweep(
        self, state: AyoState, from_pits: Iterable[int], into_store: int
    ) -> AyoState:
        pits = list(state.pits)
        for i in from_pits:
            pits[into_store] += pits[i]
            pits[i] = 0
        return replace(state, pits=tuple(pits))

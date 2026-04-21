"""Abstract Game interface shared by Ayo and Connect Four.

Design:
- States are immutable; ``apply_move`` returns a new state.
- Players are 0 and 1. Utility is from a specified player's perspective.
- ``Move`` is a game-specific type (int for Ayo pit index, int for C4 column).
- ``utility`` is the pure game-theoretic value at a terminal (+1 / 0 / -1).
  Non-terminal evaluation belongs in ``heuristics/``, not here.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

StateT = TypeVar("StateT")
MoveT = TypeVar("MoveT")


class Game(ABC, Generic[StateT, MoveT]):
    """Abstract two-player, zero-sum, perfect-information game."""

    @abstractmethod
    def initial_state(self) -> StateT:
        """Return the start-of-game state."""

    @abstractmethod
    def current_player(self, state: StateT) -> int:
        """Return the player to move (0 or 1)."""

    @abstractmethod
    def legal_moves(self, state: StateT) -> List[MoveT]:
        """Return all legal moves for the current player.

        Returns an empty list iff ``state`` is terminal.
        """

    @abstractmethod
    def apply_move(self, state: StateT, move: MoveT) -> StateT:
        """Return the state resulting from playing ``move`` at ``state``.

        The returned state is fully finalized: if the move ends the game,
        any remaining-seed sweeps are reflected in the new state.
        """

    def is_terminal(self, state: StateT) -> bool:
        """Whether the game is over at ``state``."""
        return len(self.legal_moves(state)) == 0

    @abstractmethod
    def winner(self, state: StateT) -> Optional[int]:
        """Return 0, 1, or None (draw, or not terminal)."""

    def utility(self, state: StateT, player: int) -> float:
        """Terminal utility from ``player``'s perspective: +1 / 0 / -1."""
        w = self.winner(state)
        if w is None:
            return 0.0
        return 1.0 if w == player else -1.0

    @abstractmethod
    def render(self, state: StateT) -> str:
        """Human-readable representation for CLI and debugging."""

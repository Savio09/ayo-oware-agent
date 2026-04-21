"""Abstract agent interface. An ``Agent`` picks a legal move for a state.

Agents are stateless with respect to the game (the ``Game`` object owns the
rules); they may carry their own internal state (RNG, Q-table, search
statistics, etc.).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic

from src.games.base import Game, MoveT, StateT


class Agent(ABC, Generic[StateT, MoveT]):
    """Abstract move-picker."""

    @abstractmethod
    def select_move(self, game: Game[StateT, MoveT], state: StateT) -> MoveT:
        """Return a legal move for ``state``. Raises if none exist."""

    @property
    def name(self) -> str:
        """Short identifier used by the evaluation harness and CLI logs."""
        return type(self).__name__

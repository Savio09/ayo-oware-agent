"""Uniform-random agent. Seedable for reproducibility."""
from __future__ import annotations

import random
from typing import Optional

from src.agents.base import Agent
from src.games.base import Game, MoveT, StateT


class RandomAgent(Agent[StateT, MoveT]):
    """Picks a legal move uniformly at random.

    Useful as a sanity-check opponent and as the lower bound in agent
    tournaments: any learned or searched policy should beat it handily.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = random.Random(seed)

    def select_move(self, game: Game[StateT, MoveT], state: StateT) -> MoveT:
        legal = game.legal_moves(state)
        if not legal:
            raise ValueError(
                "RandomAgent.select_move called on a terminal state "
                "(no legal moves)."
            )
        return self._rng.choice(legal)

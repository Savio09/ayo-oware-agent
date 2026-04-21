"""CLI human agent for Ayo.

The agent talks to the user in player-relative pit labels (1..6), not the
internal 0..13 indices. Each player reads their own row left-to-right as
"1 2 3 4 5 6":

* P0: label n ∈ {1..6} → pit n-1  (pits 0..5)
* P1: label n ∈ {1..6} → pit 13-n (pits 12..7, display-left-to-right)

``input_fn`` / ``output_fn`` are injectable so unit tests can drive the
agent without touching stdin/stdout.
"""
from __future__ import annotations

from typing import Callable

from src.agents.base import Agent
from src.games.ayo import Ayo, AyoState


class AyoHumanAgent(Agent[AyoState, int]):
    """Ayo-specific prompt-driven agent."""

    def __init__(
        self,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> None:
        self._input = input_fn
        self._output = output_fn

    def select_move(self, game: Ayo, state: AyoState) -> int:
        player = state.to_move
        legal = set(game.legal_moves(state))
        if not legal:
            raise ValueError(
                "AyoHumanAgent.select_move called on a terminal state."
            )
        legal_labels = sorted(self._pit_to_label(player, p) for p in legal)
        while True:
            raw = self._input(
                f"  P{player} move — pick a pit from {legal_labels}: "
            ).strip()
            try:
                label = int(raw)
            except ValueError:
                self._output(f"  Not an integer: {raw!r}. Try again.")
                continue
            if not 1 <= label <= 6:
                self._output("  Pit label must be between 1 and 6.")
                continue
            pit = self._label_to_pit(player, label)
            if pit not in legal:
                self._output(
                    f"  Pit {label} is empty or blocked by the feeding "
                    f"rule. Legal pits: {legal_labels}."
                )
                continue
            return pit

    # Mapping helpers. Static so the CLI can convert moves for logging
    # without instantiating an agent.

    @staticmethod
    def _label_to_pit(player: int, label: int) -> int:
        return (label - 1) if player == 0 else (13 - label)

    @staticmethod
    def _pit_to_label(player: int, pit: int) -> int:
        return (pit + 1) if player == 0 else (13 - pit)

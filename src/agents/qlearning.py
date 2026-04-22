"""Tabular Q-learning agent for Ayo self-play.

The Q-table is shared across both seats without any board canonicalization:
keys are ``(state.q_key(), move)``, and ``AyoState.q_key()`` already includes
``to_move`` while omitting ``ply``. A Q-value is always from the perspective of
the player to move in that state.

Because turns alternate in a two-player zero-sum game, nonterminal bootstrap
targets negate the next state's greedy value:

``target = reward - gamma * max_next_q``

where ``reward`` is measured from the perspective of the player who just took
the action, not from ``next_state.to_move``.
"""
from __future__ import annotations

import pickle
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

from src.agents.base import Agent
from src.games.ayo import Ayo, AyoState

StateKey = Tuple[Tuple[int, ...], int]
QKey = Tuple[StateKey, int]

FORMAT_VERSION = 1


@dataclass(slots=True)
class TrainingStats:
    """Summary of a self-play training run."""

    episodes: int
    q_entries: int
    p0_wins: int
    p1_wins: int
    draws: int
    total_plies: int
    avg_plies: float


class QLearningAgent(Agent[AyoState, int]):
    """Greedy Ayo agent backed by a tabular Q-function."""

    def __init__(
        self,
        alpha: float = 0.1,
        gamma: float = 0.99,
        q_values: Optional[Dict[QKey, float]] = None,
        seed: Optional[int] = None,
    ) -> None:
        if not (0 < alpha <= 1):
            raise ValueError("alpha must be in (0, 1].")
        if not (0 <= gamma <= 1):
            raise ValueError("gamma must be in [0, 1].")
        self.alpha = alpha
        self.gamma = gamma
        self.q_values: Dict[QKey, float] = dict(q_values or {})
        self._rng = random.Random(seed)

    def select_move(self, game: Ayo, state: AyoState) -> int:
        """Return the greedy legal move for ``state``.

        Normal play and evaluation are deterministic by default. Exploration is
        used by ``train_self_play`` through ``_choose_action`` instead.
        """
        return self._choose_action(game, state, epsilon=0.0, rng=self._rng)

    def q_value(self, state: AyoState, move: int) -> float:
        """Return Q(state, move), treating missing entries as 0.0."""
        return self.q_values.get((state.q_key(), move), 0.0)

    def update(
        self,
        game: Ayo,
        state: AyoState,
        move: int,
        next_state: AyoState,
    ) -> float:
        """Apply one sparse-reward Q-learning update and return the new value."""
        if move not in game.legal_moves(state):
            raise ValueError(
                f"Move {move} is not legal in this state; legal moves are "
                f"{game.legal_moves(state)}."
            )

        actor = game.current_player(state)
        old = self.q_value(state, move)
        reward = game.utility(next_state, actor) if game.is_terminal(next_state) else 0.0

        if game.is_terminal(next_state):
            target = reward
        else:
            next_values = [
                self.q_value(next_state, next_move)
                for next_move in game.legal_moves(next_state)
            ]
            target = reward - self.gamma * max(next_values)

        new_value = old + self.alpha * (target - old)
        self.q_values[(state.q_key(), move)] = new_value
        return new_value

    def save(self, path: Union[str, Path]) -> None:
        """Persist Q-table and core hyperparameters with pickle metadata."""
        payload = {
            "format_version": FORMAT_VERSION,
            "alpha": self.alpha,
            "gamma": self.gamma,
            "q_values": self.q_values,
        }
        with Path(path).open("wb") as f:
            pickle.dump(payload, f)

    @classmethod
    def load(cls, path: Union[str, Path], seed: Optional[int] = None) -> "QLearningAgent":
        """Load a Q-learning agent saved by ``save``."""
        with Path(path).open("rb") as f:
            payload = pickle.load(f)
        if payload.get("format_version") != FORMAT_VERSION:
            raise ValueError(
                "Unsupported Q-learning pickle format version: "
                f"{payload.get('format_version')!r}."
            )
        return cls(
            alpha=payload["alpha"],
            gamma=payload["gamma"],
            q_values=payload["q_values"],
            seed=seed,
        )

    def _choose_action(
        self,
        game: Ayo,
        state: AyoState,
        epsilon: float,
        rng: random.Random,
    ) -> int:
        if not (0 <= epsilon <= 1):
            raise ValueError("epsilon must be in [0, 1].")
        legal = game.legal_moves(state)
        if not legal:
            raise ValueError("QLearningAgent.select_move called on a terminal state.")
        if epsilon > 0 and rng.random() < epsilon:
            return rng.choice(legal)
        return self._greedy_action(state, legal)

    def _greedy_action(self, state: AyoState, legal: list[int]) -> int:
        best_move = legal[0]
        best_value = self.q_value(state, best_move)
        for move in legal[1:]:
            value = self.q_value(state, move)
            if value > best_value:
                best_move = move
                best_value = value
        return best_move


def train_self_play(
    game: Ayo,
    agent: QLearningAgent,
    episodes: int,
    epsilon_start: float = 1.0,
    epsilon_min: float = 0.05,
    seed: Optional[int] = None,
) -> TrainingStats:
    """Train ``agent`` by playing Ayo against itself.

    One shared table is used for both players. This works because
    ``state.q_key()`` includes ``to_move``, so P0-to-move and P1-to-move
    positions occupy different keys without extra role-flipping.
    """
    if episodes < 1:
        raise ValueError("episodes must be at least 1.")
    if not (0 <= epsilon_min <= epsilon_start <= 1):
        raise ValueError("expected 0 <= epsilon_min <= epsilon_start <= 1.")

    rng = random.Random(seed)
    p0_wins = 0
    p1_wins = 0
    draws = 0
    total_plies = 0

    for episode in range(episodes):
        epsilon = _linear_epsilon(
            episode=episode,
            episodes=episodes,
            epsilon_start=epsilon_start,
            epsilon_min=epsilon_min,
        )
        state = game.initial_state()
        episode_plies = 0

        while not game.is_terminal(state):
            move = agent._choose_action(game, state, epsilon=epsilon, rng=rng)
            next_state = game.apply_move(state, move)
            agent.update(game, state, move, next_state)
            state = next_state
            episode_plies += 1

        total_plies += episode_plies
        winner = game.winner(state)
        if winner == 0:
            p0_wins += 1
        elif winner == 1:
            p1_wins += 1
        else:
            draws += 1

    return TrainingStats(
        episodes=episodes,
        q_entries=len(agent.q_values),
        p0_wins=p0_wins,
        p1_wins=p1_wins,
        draws=draws,
        total_plies=total_plies,
        avg_plies=total_plies / episodes,
    )


def _linear_epsilon(
    episode: int,
    episodes: int,
    epsilon_start: float,
    epsilon_min: float,
) -> float:
    if episodes == 1:
        return epsilon_start
    fraction = episode / (episodes - 1)
    return epsilon_start + fraction * (epsilon_min - epsilon_start)

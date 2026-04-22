"""Tests for the tabular Ayo Q-learning agent."""
from __future__ import annotations

import random

import pytest

from src.agents.qlearning import QLearningAgent, train_self_play
from src.games.ayo import Ayo, AyoState


@pytest.fixture
def game() -> Ayo:
    return Ayo()


def terminal_state(p0_store: int, p1_store: int, to_move: int = 1) -> AyoState:
    return AyoState(
        pits=tuple([0] * 6 + [p0_store] + [0] * 6 + [p1_store]),
        to_move=to_move,
        ply=Ayo.PLY_LIMIT,
    )


def test_missing_q_values_default_to_zero(game):
    agent = QLearningAgent()
    state = game.initial_state()

    assert agent.q_value(state, 0) == 0.0


def test_select_move_is_greedy_and_ties_use_legal_move_order(game):
    agent = QLearningAgent()
    state = game.initial_state()

    assert game.legal_moves(state) == [0, 1, 2, 3, 4, 5]
    assert agent.select_move(game, state) == 0

    agent.q_values[(state.q_key(), 3)] = 1.25
    assert agent.select_move(game, state) == 3


def test_epsilon_action_selection_still_returns_legal_moves(game):
    agent = QLearningAgent()
    state = game.initial_state()
    rng = random.Random(0)
    legal = set(game.legal_moves(state))

    for _ in range(50):
        assert agent._choose_action(game, state, epsilon=1.0, rng=rng) in legal


def test_select_move_raises_on_terminal_state(game):
    agent = QLearningAgent()
    state = terminal_state(p0_store=24, p1_store=24)

    with pytest.raises(ValueError, match="terminal state"):
        agent.select_move(game, state)


def test_terminal_update_uses_acting_player_reward_without_bootstrap(game):
    agent = QLearningAgent(alpha=1.0, gamma=0.99)
    state = game.initial_state()
    next_state = terminal_state(p0_store=30, p1_store=18, to_move=1)

    new_value = agent.update(game, state, 0, next_state)

    assert game.current_player(state) == 0
    assert next_state.to_move == 1
    assert game.utility(next_state, 0) == 1.0
    assert game.utility(next_state, next_state.to_move) == -1.0
    assert new_value == 1.0


def test_nonterminal_update_negates_next_players_best_value(game):
    agent = QLearningAgent(alpha=1.0, gamma=0.5)
    state = game.initial_state()
    move = 0
    next_state = game.apply_move(state, move)
    best_reply = game.legal_moves(next_state)[0]
    agent.q_values[(next_state.q_key(), best_reply)] = 0.8

    new_value = agent.update(game, state, move, next_state)

    assert not game.is_terminal(next_state)
    assert new_value == pytest.approx(-0.4)


def test_update_rejects_illegal_move(game):
    agent = QLearningAgent()
    state = game.initial_state()
    next_state = game.apply_move(state, 0)

    with pytest.raises(ValueError, match="not legal"):
        agent.update(game, state, 7, next_state)


def test_self_play_training_populates_q_table_and_reports_avg_plies(game):
    agent = QLearningAgent(alpha=0.5, gamma=0.9)

    stats = train_self_play(
        game,
        agent,
        episodes=3,
        epsilon_start=0.2,
        epsilon_min=0.0,
        seed=4,
    )

    assert stats.episodes == 3
    assert stats.q_entries == len(agent.q_values)
    assert stats.q_entries > 0
    assert stats.p0_wins + stats.p1_wins + stats.draws == 3
    assert stats.total_plies > 0
    assert stats.total_plies <= 3 * Ayo.PLY_LIMIT
    assert stats.avg_plies == pytest.approx(stats.total_plies / stats.episodes)


def test_save_and_load_round_trips_q_values_and_metadata(game, tmp_path):
    state = game.initial_state()
    path = tmp_path / "q_agent.pkl"
    agent = QLearningAgent(alpha=0.2, gamma=0.7)
    agent.q_values[(state.q_key(), 2)] = 1.5

    agent.save(path)
    loaded = QLearningAgent.load(path)

    assert loaded.alpha == 0.2
    assert loaded.gamma == 0.7
    assert loaded.q_value(state, 2) == 1.5

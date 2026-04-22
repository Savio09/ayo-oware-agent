"""Tests for Ayo heuristic features and minimax integration."""
from __future__ import annotations

from typing import List

import pytest

from src.agents.minimax import MinimaxAgent
from src.games.ayo import Ayo, AyoState
from src.heuristics.ayo_heuristics import (
    ayo_h1,
    ayo_h2,
    ayo_h3,
    ayo_h4,
    ayo_immediate_gain_move_order,
    immediate_store_gain,
    immediate_store_gain_differential,
    immediate_store_gain_potential,
    legal_moves_for_player,
    make_ayo_h3,
    make_ayo_h4,
    mobility_differential,
    store_differential,
)


def make_state(pits: List[int], to_move: int = 0, ply: int = 0) -> AyoState:
    assert len(pits) == 14
    return AyoState(pits=tuple(pits), to_move=to_move, ply=ply)


@pytest.fixture
def game() -> Ayo:
    return Ayo()


def test_h1_store_differential(game):
    state = make_state([0, 0, 1, 0, 0, 0, 10] + [1, 0, 0, 0, 0, 0] + [4])

    assert store_differential(game, state, 0) == 6
    assert ayo_h1(game, state, 0) == 6.0
    assert ayo_h1(game, state, 1) == -6.0


def test_counterfactual_legal_moves_and_h2_mobility(game):
    state = make_state([1, 1, 0, 0, 0, 0, 0] + [1, 0, 0, 0, 0, 0] + [0])

    assert legal_moves_for_player(game, state, 0) == [0, 1]
    assert legal_moves_for_player(game, state, 1) == [7]
    assert mobility_differential(game, state, 0) == 1
    assert mobility_differential(game, state, 1) == -1
    assert ayo_h2(game, state, 0) == 0.25
    assert ayo_h2(game, state, 1) == -0.25


def test_immediate_store_gain_helpers_include_finalized_store_delta(game):
    state = make_state([1, 0, 1, 0, 0, 0, 0] + [2, 0, 5, 0, 0, 0] + [0])

    assert immediate_store_gain(game, state, 0, 0) == 0
    assert immediate_store_gain(game, state, 0, 2) == 6
    assert immediate_store_gain_potential(game, state, 0) == 6
    assert immediate_store_gain_potential(game, state, 1) == 0
    assert immediate_store_gain_differential(game, state, 0) == 6
    assert immediate_store_gain_differential(game, state, 1) == -6


def test_h3_uses_immediate_store_gain_potential(game):
    state = make_state([1, 0, 1, 0, 0, 0, 0] + [2, 0, 5, 0, 0, 0] + [0])

    assert ayo_h2(game, state, 0) == 0.0
    assert ayo_h3(game, state, 0) == 3.0

    heavier_h3 = make_ayo_h3(immediate_gain_weight=1.0)
    assert heavier_h3(game, state, 0) == 6.0


def test_h4_adds_extra_opponent_immediate_gain_vulnerability_penalty(game):
    state = make_state([1, 0, 1, 0, 0, 0, 0] + [2, 0, 5, 0, 0, 0] + [0])

    assert ayo_h3(game, state, 1) == -3.0
    assert ayo_h4(game, state, 1) == -6.0

    no_vulnerability_h4 = make_ayo_h4(vulnerability_weight=0.0)
    assert no_vulnerability_h4(game, state, 1) == ayo_h3(game, state, 1)


def test_ayo_move_order_uses_immediate_gain_then_pit_index(game):
    state = make_state([1, 0, 1, 0, 0, 0, 0] + [2, 0, 5, 0, 0, 0] + [0])
    legal = game.legal_moves(state)

    assert legal == [0, 2]
    assert ayo_immediate_gain_move_order(game, state, legal) == [2, 0]


def test_heuristic_rejects_non_ayo_game():
    with pytest.raises(TypeError, match="Ayo"):
        ayo_h1(object(), make_state([0] * 14), 0)


def test_minimax_with_ayo_heuristic_returns_legal_move(game):
    agent = MinimaxAgent(
        heuristic=ayo_h4,
        max_depth=1,
        move_order=ayo_immediate_gain_move_order,
    )
    state = game.initial_state()

    move = agent.select_move(game, state)

    assert move in game.legal_moves(state)


def test_minimax_prefers_clearly_superior_immediate_store_gain(game):
    state = make_state([1, 0, 1, 0, 0, 0, 0] + [2, 0, 5, 0, 0, 0] + [0])
    agent = MinimaxAgent(
        heuristic=ayo_h1,
        max_depth=1,
        move_order=ayo_immediate_gain_move_order,
    )

    assert game.legal_moves(state) == [0, 2]
    assert agent.select_move(game, state) == 2


def test_terminal_children_use_minimax_terminal_path_not_heuristic(game):
    state = make_state([0, 0, 1, 0, 0, 0, 0] + [0, 0, 3, 0, 0, 0] + [0])

    def failing_heuristic(_game, _state, _player):
        raise AssertionError("heuristic should not be called for terminal child")

    agent = MinimaxAgent(
        heuristic=failing_heuristic,
        max_depth=1,
        move_order=ayo_immediate_gain_move_order,
    )

    assert game.legal_moves(state) == [2]
    assert agent.select_move(game, state) == 2

"""Validation tests for the reusable minimax / alpha-beta agent."""
from __future__ import annotations

from typing import Iterable

import pytest

from src.agents.minimax import (
    MinimaxAgent,
    SearchStats,
    connect_four_center_first_moves,
    connect_four_heuristic,
)
from src.agents.random_agent import RandomAgent
from src.games.connect_four import ConnectFour, ConnectFourState


def play_sequence(game: ConnectFour, moves: Iterable[int]) -> ConnectFourState:
    state = game.initial_state()
    for move in moves:
        state = game.apply_move(state, move)
    return state


def zero_heuristic(_game, _state, _player):
    return 0.0


@pytest.fixture
def game() -> ConnectFour:
    return ConnectFour()


def test_minimax_takes_immediate_win(game):
    # P0 has bottom-row tokens in columns 0, 1, 2. Column 3 wins immediately.
    state = play_sequence(game, [0, 6, 1, 6, 2, 5])
    agent = MinimaxAgent(
        heuristic=connect_four_heuristic,
        max_depth=1,
        move_order=connect_four_center_first_moves,
    )

    assert agent.select_move(game, state) == 3
    assert agent.last_stats.depth_completed == 1
    assert isinstance(agent.last_stats, SearchStats)


def test_minimax_blocks_opponent_immediate_win(game):
    # P1 threatens bottom-row columns 0, 1, 2, 3. P0 must block column 3.
    state = play_sequence(game, [6, 0, 6, 1, 5, 2])
    agent = MinimaxAgent(
        heuristic=connect_four_heuristic,
        max_depth=2,
        move_order=connect_four_center_first_moves,
    )

    assert agent.select_move(game, state) == 3


def test_center_first_order_breaks_equal_score_ties(game):
    agent = MinimaxAgent(
        heuristic=zero_heuristic,
        max_depth=1,
        move_order=connect_four_center_first_moves,
    )

    assert agent.select_move(game, game.initial_state()) == 3


def test_terminal_win_dominates_large_nonterminal_heuristic(game):
    state = play_sequence(game, [0, 6, 1, 6, 2, 5])

    def large_heuristic(_game, _state, _player):
        return 500_000.0

    agent = MinimaxAgent(
        heuristic=large_heuristic,
        max_depth=1,
        move_order=connect_four_center_first_moves,
    )

    assert agent.select_move(game, state) == 3


def test_alpha_beta_matches_plain_minimax_with_same_move_order(game):
    state = play_sequence(game, [3, 2, 4, 2, 5, 2])
    plain = MinimaxAgent(
        heuristic=connect_four_heuristic,
        max_depth=4,
        use_alpha_beta=False,
        use_transposition_table=False,
        move_order=connect_four_center_first_moves,
    )
    alpha_beta = MinimaxAgent(
        heuristic=connect_four_heuristic,
        max_depth=4,
        use_alpha_beta=True,
        use_transposition_table=False,
        move_order=connect_four_center_first_moves,
    )

    assert alpha_beta.select_move(game, state) == plain.select_move(game, state)


def test_alpha_beta_visits_fewer_nodes_than_plain_minimax_with_tt_disabled(game):
    state = game.initial_state()
    plain = MinimaxAgent(
        heuristic=zero_heuristic,
        max_depth=5,
        use_alpha_beta=False,
        use_transposition_table=False,
        move_order=connect_four_center_first_moves,
    )
    alpha_beta = MinimaxAgent(
        heuristic=zero_heuristic,
        max_depth=5,
        use_alpha_beta=True,
        use_transposition_table=False,
        move_order=connect_four_center_first_moves,
    )

    assert alpha_beta.select_move(game, state) == plain.select_move(game, state)
    assert plain.last_stats.cutoffs == 0
    assert alpha_beta.last_stats.cutoffs > 0
    assert alpha_beta.last_stats.nodes < plain.last_stats.nodes


def test_minimax_select_move_raises_on_terminal_state(game):
    terminal = play_sequence(game, [0, 6, 1, 6, 2, 6, 3])
    agent = MinimaxAgent(
        heuristic=connect_four_heuristic,
        max_depth=1,
        move_order=connect_four_center_first_moves,
    )

    with pytest.raises(ValueError, match="terminal state"):
        agent.select_move(game, terminal)


def test_minimax_vs_random_smoke_game(game):
    agents = {
        0: MinimaxAgent(
            heuristic=connect_four_heuristic,
            max_depth=2,
            move_order=connect_four_center_first_moves,
        ),
        1: RandomAgent(seed=3),
    }
    final = game.initial_state()
    while not game.is_terminal(final):
        mover = game.current_player(final)
        move = agents[mover].select_move(game, final)
        final = game.apply_move(final, move)

    assert game.is_terminal(final)
    assert game.winner(final) in {0, None}

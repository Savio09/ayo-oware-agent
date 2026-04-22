"""Rule-correctness tests for the Connect Four validation game."""
from __future__ import annotations

from typing import List

import pytest

from src.games.connect_four import ConnectFour, ConnectFourState


def make_state(board: List[int], to_move: int = 0, ply: int = 0) -> ConnectFourState:
    assert len(board) == ConnectFour.NUM_CELLS
    return ConnectFourState(board=tuple(board), to_move=to_move, ply=ply)


@pytest.fixture
def game() -> ConnectFour:
    return ConnectFour()


def test_initial_state_layout_and_legal_moves(game):
    state = game.initial_state()
    assert state.board == (0,) * 42
    assert state.to_move == 0
    assert state.ply == 0
    assert game.legal_moves(state) == [0, 1, 2, 3, 4, 5, 6]
    assert not game.is_terminal(state)


def test_apply_move_uses_bottom_left_row_major_indexing(game):
    state = game.initial_state()
    s1 = game.apply_move(state, 3)
    s2 = game.apply_move(s1, 3)

    assert s1.board[3] == ConnectFour.P0_TOKEN
    assert s2.board[3] == ConnectFour.P0_TOKEN
    assert s2.board[10] == ConnectFour.P1_TOKEN  # row 1, col 3
    assert state.board[3] == ConnectFour.EMPTY
    assert s2.to_move == 0
    assert s2.ply == 2


def test_full_column_is_not_legal_and_rejected(game):
    state = game.initial_state()
    for _ in range(ConnectFour.ROWS):
        state = game.apply_move(state, 0)

    assert 0 not in game.legal_moves(state)
    with pytest.raises(ValueError, match="not legal"):
        game.apply_move(state, 0)


def test_horizontal_win(game):
    board = [0] * ConnectFour.NUM_CELLS
    for col in range(4):
        board[col] = ConnectFour.P0_TOKEN
    state = make_state(board, to_move=1, ply=7)

    assert game.winner(state) == 0
    assert game.is_terminal(state)
    assert game.legal_moves(state) == []


def test_vertical_win(game):
    board = [0] * ConnectFour.NUM_CELLS
    for row in range(4):
        board[row * ConnectFour.COLS + 2] = ConnectFour.P1_TOKEN
    state = make_state(board, to_move=0, ply=8)

    assert game.winner(state) == 1
    assert game.is_terminal(state)


def test_diagonal_up_right_win(game):
    board = [0] * ConnectFour.NUM_CELLS
    for row, col in ((0, 0), (1, 1), (2, 2), (3, 3)):
        board[row * ConnectFour.COLS + col] = ConnectFour.P0_TOKEN
    state = make_state(board, to_move=1, ply=7)

    assert game.winner(state) == 0
    assert game.is_terminal(state)


def test_diagonal_up_left_win(game):
    board = [0] * ConnectFour.NUM_CELLS
    for row, col in ((0, 6), (1, 5), (2, 4), (3, 3)):
        board[row * ConnectFour.COLS + col] = ConnectFour.P1_TOKEN
    state = make_state(board, to_move=0, ply=8)

    assert game.winner(state) == 1
    assert game.is_terminal(state)


def test_full_board_draw(game):
    board = [
        2, 1, 1, 1, 2, 2, 2,
        1, 2, 2, 2, 1, 1, 2,
        1, 1, 2, 1, 2, 2, 1,
        2, 1, 2, 1, 1, 2, 1,
        2, 2, 1, 2, 1, 1, 1,
        2, 1, 1, 2, 1, 2, 2,
    ]
    state = make_state(board, to_move=0, ply=42)

    assert game.legal_moves(state) == []
    assert game.is_terminal(state)
    assert game.winner(state) is None
    assert game.utility(state, 0) == 0.0


def test_render_prints_top_row_first_and_column_labels(game):
    board = [0] * ConnectFour.NUM_CELLS
    board[0] = ConnectFour.P0_TOKEN
    board[41] = ConnectFour.P1_TOKEN
    state = make_state(board, to_move=1, ply=2)
    out = game.render(state)
    lines = out.splitlines()

    assert lines[0] == "| . . . . . . O |"
    assert lines[5] == "| X . . . . . . |"
    assert lines[6] == "  0 1 2 3 4 5 6"
    assert lines[7] == "to move: P1   ply: 2"

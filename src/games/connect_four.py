"""Connect Four rules engine used to validate minimax.

Board representation:

* 7 columns x 6 rows = 42 cells in a flat tuple.
* Row-major indexing from the bottom-left: ``index = row * 7 + col``.
* ``row == 0`` is the bottom row; ``row == 5`` is the top row.
* ``col == 0`` is the leftmost column; ``col == 6`` is the rightmost column.
* Cell values are ``0`` for empty, ``1`` for P0, and ``2`` for P1.

Rendering prints rows top-to-bottom so the display matches the usual physical
board, while the stored tuple keeps gravity simple to reason about.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .base import Game


@dataclass(frozen=True, slots=True)
class ConnectFourState:
    """Immutable Connect Four state."""

    board: Tuple[int, ...]
    to_move: int
    ply: int


class ConnectFour(Game[ConnectFourState, int]):
    """Connect Four rules engine. Moves are column indices 0..6."""

    ROWS = 6
    COLS = 7
    NUM_CELLS = ROWS * COLS
    EMPTY = 0
    P0_TOKEN = 1
    P1_TOKEN = 2

    def initial_state(self) -> ConnectFourState:
        return ConnectFourState(board=(self.EMPTY,) * self.NUM_CELLS, to_move=0, ply=0)

    def current_player(self, state: ConnectFourState) -> int:
        return state.to_move

    def legal_moves(self, state: ConnectFourState) -> List[int]:
        if self._winning_token(state) is not None:
            return []
        return [
            col
            for col in range(self.COLS)
            if state.board[self._index(self.ROWS - 1, col)] == self.EMPTY
        ]

    def apply_move(self, state: ConnectFourState, move: int) -> ConnectFourState:
        legal = self.legal_moves(state)
        if move not in legal:
            raise ValueError(f"Move {move} is not legal; legal moves are {legal}.")

        board = list(state.board)
        token = self._token_for_player(state.to_move)
        for row in range(self.ROWS):
            idx = self._index(row, move)
            if board[idx] == self.EMPTY:
                board[idx] = token
                break

        return ConnectFourState(
            board=tuple(board),
            to_move=1 - state.to_move,
            ply=state.ply + 1,
        )

    def winner(self, state: ConnectFourState) -> Optional[int]:
        token = self._winning_token(state)
        if token == self.P0_TOKEN:
            return 0
        if token == self.P1_TOKEN:
            return 1
        return None

    def render(self, state: ConnectFourState) -> str:
        symbols = {
            self.EMPTY: ".",
            self.P0_TOKEN: "X",
            self.P1_TOKEN: "O",
        }
        lines = []
        for row in range(self.ROWS - 1, -1, -1):
            row_symbols = [
                symbols[state.board[self._index(row, col)]]
                for col in range(self.COLS)
            ]
            cells = " ".join(row_symbols)
            lines.append(f"| {cells} |")
        lines.append("  0 1 2 3 4 5 6")
        lines.append(f"to move: P{state.to_move}   ply: {state.ply}")
        return "\n".join(lines)

    def _index(self, row: int, col: int) -> int:
        return row * self.COLS + col

    def _token_for_player(self, player: int) -> int:
        return self.P0_TOKEN if player == 0 else self.P1_TOKEN

    def _winning_token(self, state: ConnectFourState) -> Optional[int]:
        directions = (
            (0, 1),   # horizontal
            (1, 0),   # vertical
            (1, 1),   # diagonal up-right
            (1, -1),  # diagonal up-left
        )
        for row in range(self.ROWS):
            for col in range(self.COLS):
                token = state.board[self._index(row, col)]
                if token == self.EMPTY:
                    continue
                for d_row, d_col in directions:
                    if self._has_four_from(state, row, col, d_row, d_col, token):
                        return token
        return None

    def _has_four_from(
        self,
        state: ConnectFourState,
        row: int,
        col: int,
        d_row: int,
        d_col: int,
        token: int,
    ) -> bool:
        for offset in range(4):
            r = row + d_row * offset
            c = col + d_col * offset
            if not (0 <= r < self.ROWS and 0 <= c < self.COLS):
                return False
            if state.board[self._index(r, c)] != token:
                return False
        return True

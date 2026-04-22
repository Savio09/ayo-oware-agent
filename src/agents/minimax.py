"""Reusable minimax / alpha-beta agent.

The search score is always from the root player's perspective. That keeps the
agent reusable: game-specific knowledge stays in the supplied heuristic, while
the search code only needs the ``Game`` interface.
"""
from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Callable, Dict, Generic, List, Optional, Tuple

from src.agents.base import Agent
from src.games.base import Game, MoveT, StateT
from src.games.connect_four import ConnectFour, ConnectFourState


WIN_SCORE = 1_000_000.0

Heuristic = Callable[[Game[StateT, MoveT], StateT, int], float]
MoveOrder = Callable[[Game[StateT, MoveT], StateT, List[MoveT]], List[MoveT]]


@dataclass(slots=True)
class SearchStats:
    """Stats from the most recent search.

    ``nodes`` means recursive search calls entered. This definition is used for
    both plain minimax and alpha-beta so node-count comparisons stay fair.
    """

    nodes: int = 0
    cutoffs: int = 0
    depth_completed: int = 0
    elapsed_s: float = 0.0
    tt_hits: int = 0


class _SearchTimeout(Exception):
    """Internal control flow for time-budgeted iterative deepening."""


class MinimaxAgent(Agent[StateT, MoveT], Generic[StateT, MoveT]):
    """Depth-limited minimax agent with optional alpha-beta pruning."""

    def __init__(
        self,
        heuristic: Heuristic[StateT, MoveT],
        max_depth: int,
        time_limit_s: Optional[float] = None,
        use_alpha_beta: bool = True,
        use_transposition_table: bool = False,
        move_order: Optional[MoveOrder[StateT, MoveT]] = None,
    ) -> None:
        if max_depth < 1:
            raise ValueError("max_depth must be at least 1.")
        if time_limit_s is not None and time_limit_s <= 0:
            raise ValueError("time_limit_s must be positive when provided.")
        self.heuristic = heuristic
        self.max_depth = max_depth
        self.time_limit_s = time_limit_s
        self.use_alpha_beta = use_alpha_beta
        self.use_transposition_table = use_transposition_table
        self.move_order = move_order
        self.last_stats = SearchStats()
        self._deadline: Optional[float] = None
        self._tt: Dict[Tuple[StateT, int, int], float] = {}

    def select_move(self, game: Game[StateT, MoveT], state: StateT) -> MoveT:
        """Return the best legal move found for ``state``."""
        legal = self._ordered_moves(game, state)
        if not legal:
            raise ValueError("MinimaxAgent.select_move called on a terminal state.")

        self.last_stats = SearchStats()
        self._tt = {}
        start = perf_counter()
        self._deadline = None

        best_move = legal[0]
        try:
            if self.time_limit_s is None:
                move, _score = self._best_move_at_depth(game, state, self.max_depth)
                best_move = move
                self.last_stats.depth_completed = self.max_depth
            else:
                self._deadline = start + self.time_limit_s
                for depth in range(1, self.max_depth + 1):
                    move, _score = self._best_move_at_depth(game, state, depth)
                    best_move = move
                    self.last_stats.depth_completed = depth
                    if perf_counter() >= self._deadline:
                        break
        except _SearchTimeout:
            # Keep the best move from the deepest fully completed iteration.
            pass
        finally:
            self.last_stats.elapsed_s = perf_counter() - start
            self._deadline = None

        return best_move

    def _best_move_at_depth(
        self,
        game: Game[StateT, MoveT],
        state: StateT,
        depth: int,
    ) -> Tuple[MoveT, float]:
        self.last_stats.nodes += 1
        root_player = game.current_player(state)
        maximizing = True
        alpha = -float("inf")
        beta = float("inf")
        best_score = -float("inf")
        best_move = self._ordered_moves(game, state)[0]

        for move in self._ordered_moves(game, state):
            self._check_timeout()
            child = game.apply_move(state, move)
            score = self._search(
                game=game,
                state=child,
                depth_remaining=depth - 1,
                root_player=root_player,
                maximizing=not maximizing,
                alpha=alpha,
                beta=beta,
                ply_from_root=1,
            )
            if score > best_score:
                best_score = score
                best_move = move
            if self.use_alpha_beta:
                alpha = max(alpha, best_score)
        return best_move, best_score

    def _search(
        self,
        game: Game[StateT, MoveT],
        state: StateT,
        depth_remaining: int,
        root_player: int,
        maximizing: bool,
        alpha: float,
        beta: float,
        ply_from_root: int,
    ) -> float:
        self._check_timeout()
        self.last_stats.nodes += 1

        if game.is_terminal(state):
            return self._terminal_score(game, state, root_player, ply_from_root)
        if depth_remaining == 0:
            return self.heuristic(game, state, root_player)

        tt_key = (state, depth_remaining, root_player)
        if self.use_transposition_table and tt_key in self._tt:
            self.last_stats.tt_hits += 1
            return self._tt[tt_key]

        moves = self._ordered_moves(game, state)
        exact = True
        if maximizing:
            value = -float("inf")
            for move in moves:
                child = game.apply_move(state, move)
                value = max(
                    value,
                    self._search(
                        game,
                        child,
                        depth_remaining - 1,
                        root_player,
                        False,
                        alpha,
                        beta,
                        ply_from_root + 1,
                    ),
                )
                if self.use_alpha_beta:
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        self.last_stats.cutoffs += 1
                        exact = False
                        break
        else:
            value = float("inf")
            for move in moves:
                child = game.apply_move(state, move)
                value = min(
                    value,
                    self._search(
                        game,
                        child,
                        depth_remaining - 1,
                        root_player,
                        True,
                        alpha,
                        beta,
                        ply_from_root + 1,
                    ),
                )
                if self.use_alpha_beta:
                    beta = min(beta, value)
                    if alpha >= beta:
                        self.last_stats.cutoffs += 1
                        exact = False
                        break

        if self.use_transposition_table and exact:
            self._tt[tt_key] = value
        return value

    def _terminal_score(
        self,
        game: Game[StateT, MoveT],
        state: StateT,
        root_player: int,
        ply_from_root: int,
    ) -> float:
        winner = game.winner(state)
        if winner is None:
            return 0.0
        if winner == root_player:
            return WIN_SCORE - ply_from_root
        return -WIN_SCORE + ply_from_root

    def _ordered_moves(
        self,
        game: Game[StateT, MoveT],
        state: StateT,
    ) -> List[MoveT]:
        moves = game.legal_moves(state)
        if self.move_order is None:
            return list(moves)
        return self.move_order(game, state, list(moves))

    def _check_timeout(self) -> None:
        if self._deadline is not None and perf_counter() >= self._deadline:
            raise _SearchTimeout


def connect_four_center_first_moves(
    _game: Game[ConnectFourState, int],
    _state: ConnectFourState,
    moves: List[int],
) -> List[int]:
    """Return legal columns in deterministic center-first order."""
    preferred = (3, 2, 4, 1, 5, 0, 6)
    legal = set(moves)
    return [move for move in preferred if move in legal]


def connect_four_heuristic(
    game: Game[ConnectFourState, int],
    state: ConnectFourState,
    player: int,
) -> float:
    """Simple Connect Four heuristic from ``player``'s perspective."""
    if not isinstance(game, ConnectFour):
        raise TypeError("connect_four_heuristic requires a ConnectFour game.")

    own = game.P0_TOKEN if player == 0 else game.P1_TOKEN
    opp = game.P1_TOKEN if player == 0 else game.P0_TOKEN
    score = 0.0

    center_col = game.COLS // 2
    center_count = sum(
        1
        for row in range(game.ROWS)
        if state.board[row * game.COLS + center_col] == own
    )
    score += center_count * 3

    for window in _connect_four_windows(game, state):
        score += _score_connect_four_window(window, own, opp)
    return score


def _connect_four_windows(
    game: ConnectFour,
    state: ConnectFourState,
) -> List[Tuple[int, int, int, int]]:
    windows: List[Tuple[int, int, int, int]] = []
    directions = ((0, 1), (1, 0), (1, 1), (1, -1))
    for row in range(game.ROWS):
        for col in range(game.COLS):
            for d_row, d_col in directions:
                cells: List[int] = []
                for offset in range(4):
                    r = row + d_row * offset
                    c = col + d_col * offset
                    if not (0 <= r < game.ROWS and 0 <= c < game.COLS):
                        break
                    cells.append(state.board[r * game.COLS + c])
                if len(cells) == 4:
                    windows.append(tuple(cells))
    return windows


def _score_connect_four_window(
    window: Tuple[int, int, int, int],
    own: int,
    opp: int,
) -> float:
    own_count = window.count(own)
    opp_count = window.count(opp)
    empty_count = window.count(ConnectFour.EMPTY)

    if own_count and opp_count:
        return 0.0
    if own_count == 4:
        return 10_000.0
    if opp_count == 4:
        return -10_000.0
    if own_count == 3 and empty_count == 1:
        return 50.0
    if own_count == 2 and empty_count == 2:
        return 10.0
    if own_count == 1 and empty_count == 3:
        return 1.0
    if opp_count == 3 and empty_count == 1:
        return -80.0
    if opp_count == 2 and empty_count == 2:
        return -10.0
    if opp_count == 1 and empty_count == 3:
        return -1.0
    return 0.0

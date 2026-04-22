"""Ayo heuristics for depth-limited minimax.

These functions are for nonterminal cutoff evaluation only. True terminal
states are scored by ``MinimaxAgent`` using the game-theoretic winner.

Several features below are counterfactual: they evaluate what each player could
do if it were their turn on the same board by replacing ``state.to_move`` before
calling the rules engine. This is a heuristic feature, not a literal claim about
the current move history.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Callable, List

from src.agents.minimax import MinimaxAgent
from src.games.ayo import Ayo, AyoState

DEFAULT_MOBILITY_WEIGHT = 0.25
DEFAULT_IMMEDIATE_GAIN_WEIGHT = 0.5
DEFAULT_VULNERABILITY_WEIGHT = 0.5

AyoHeuristic = Callable[[Ayo, AyoState, int], float]


def ayo_h1(game: Ayo, state: AyoState, player: int) -> float:
    """Store differential: captured seeds for player minus opponent."""
    _require_ayo(game)
    return float(store_differential(game, state, player))


def make_ayo_h2(mobility_weight: float = DEFAULT_MOBILITY_WEIGHT) -> AyoHeuristic:
    """Create H2: store differential plus counterfactual mobility differential."""

    def heuristic(game: Ayo, state: AyoState, player: int) -> float:
        _require_ayo(game)
        mobility = mobility_differential(game, state, player)
        return ayo_h1(game, state, player) + mobility_weight * mobility

    return heuristic


def make_ayo_h3(
    mobility_weight: float = DEFAULT_MOBILITY_WEIGHT,
    immediate_gain_weight: float = DEFAULT_IMMEDIATE_GAIN_WEIGHT,
) -> AyoHeuristic:
    """Create H3 using immediate store-gain potential differential.

    This is intentionally not called pure capture potential: because
    ``Ayo.apply_move`` finalizes terminal sweeps, store deltas can include more
    than captures.
    """

    h2 = make_ayo_h2(mobility_weight=mobility_weight)

    def heuristic(game: Ayo, state: AyoState, player: int) -> float:
        _require_ayo(game)
        gain_diff = immediate_store_gain_differential(game, state, player)
        return h2(game, state, player) + immediate_gain_weight * gain_diff

    return heuristic


def make_ayo_h4(
    mobility_weight: float = DEFAULT_MOBILITY_WEIGHT,
    immediate_gain_weight: float = DEFAULT_IMMEDIATE_GAIN_WEIGHT,
    vulnerability_weight: float = DEFAULT_VULNERABILITY_WEIGHT,
) -> AyoHeuristic:
    """Create H4 with an extra opponent immediate-gain vulnerability penalty."""

    h3 = make_ayo_h3(
        mobility_weight=mobility_weight,
        immediate_gain_weight=immediate_gain_weight,
    )

    def heuristic(game: Ayo, state: AyoState, player: int) -> float:
        _require_ayo(game)
        opp_gain = immediate_store_gain_potential(game, state, _opponent(player))
        return h3(game, state, player) - vulnerability_weight * opp_gain

    return heuristic


ayo_h2 = make_ayo_h2()
ayo_h3 = make_ayo_h3()
ayo_h4 = make_ayo_h4()


def store_differential(game: Ayo, state: AyoState, player: int) -> int:
    """Return captured-seed differential from ``player``'s perspective."""
    return state.pits[game._own_store(player)] - state.pits[game._opp_store(player)]


def legal_moves_for_player(game: Ayo, state: AyoState, player: int) -> List[int]:
    """Counterfactual legal moves for ``player`` on the same board.

    This intentionally replaces only ``to_move``. It lets a heuristic compare
    each side's options without claiming that both sides can literally move next.
    """
    return game.legal_moves(replace(state, to_move=player))


def mobility_differential(game: Ayo, state: AyoState, player: int) -> int:
    """Difference in counterfactual legal move counts."""
    own = len(legal_moves_for_player(game, state, player))
    opp = len(legal_moves_for_player(game, state, _opponent(player)))
    return own - opp


def immediate_store_gain(
    game: Ayo,
    state: AyoState,
    player: int,
    move: int,
) -> int:
    """Counterfactual store gain from applying ``move`` for ``player``.

    The returned delta may include captures and terminal sweeps because
    ``Ayo.apply_move`` returns finalized states.
    """
    perspective_state = replace(state, to_move=player)
    before = perspective_state.pits[game._own_store(player)]
    after = game.apply_move(perspective_state, move)
    return after.pits[game._own_store(player)] - before


def immediate_store_gain_potential(game: Ayo, state: AyoState, player: int) -> int:
    """Sum immediate finalized store gains over counterfactual legal moves."""
    return sum(
        immediate_store_gain(game, state, player, move)
        for move in legal_moves_for_player(game, state, player)
    )


def immediate_store_gain_differential(game: Ayo, state: AyoState, player: int) -> int:
    """Immediate store-gain potential minus opponent potential."""
    own = immediate_store_gain_potential(game, state, player)
    opp = immediate_store_gain_potential(game, state, _opponent(player))
    return own - opp


def ayo_immediate_gain_move_order(
    game: Ayo,
    state: AyoState,
    moves: List[int],
) -> List[int]:
    """Order Ayo moves by immediate store gain, then pit index.

    This costs extra ``apply_move`` calls at each searched node, but Ayo has at
    most six legal moves, so the deterministic pruning benefit is worth it for
    this project scale.
    """
    player = game.current_player(state)
    return sorted(
        moves,
        key=lambda move: (-immediate_store_gain(game, state, player, move), move),
    )


def make_ayo_minimax_agent(
    heuristic: AyoHeuristic = ayo_h4,
    max_depth: int = 4,
    time_limit_s: float = 1.0,
) -> MinimaxAgent[AyoState, int]:
    """Convenience configuration for Phase 4 Ayo minimax play."""
    return MinimaxAgent(
        heuristic=heuristic,
        max_depth=max_depth,
        time_limit_s=time_limit_s,
        use_alpha_beta=True,
        use_transposition_table=False,
        move_order=ayo_immediate_gain_move_order,
    )


def _opponent(player: int) -> int:
    return 1 - player


def _require_ayo(game: Ayo) -> None:
    if not isinstance(game, Ayo):
        raise TypeError("Ayo heuristics require an Ayo game.")

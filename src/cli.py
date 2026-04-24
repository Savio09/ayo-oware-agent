"""Play Ayo at the terminal.

Examples::

    # Human (P0) vs. random (P1)
    python -m src.cli

    # Human vs. minimax (default H4 heuristic)
    python -m src.cli --p0 human --p1 minimax --minimax-time none

    # Human vs. Q-learning checkpoint
    python -m src.cli --p0 human --p1 qlearning

    # Random vs. random, seeded for reproducibility
    python -m src.cli --p0 random --p1 random --seed 42

    # Swap sides
    python -m src.cli --p0 random --p1 human
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Optional

from src.agents.base import Agent
from src.agents.human import AyoHumanAgent
from src.agents.minimax import MinimaxAgent
from src.agents.qlearning import QLearningAgent
from src.agents.random_agent import RandomAgent
from src.games.ayo import Ayo, AyoState
from src.heuristics.ayo_heuristics import (
    ayo_h1,
    ayo_h2,
    ayo_h3,
    ayo_h4,
    ayo_immediate_gain_move_order,
)

DEFAULT_Q_PATH = (
    Path(__file__).resolve().parents[1] / "artifacts" / "qlearning_50k_seed152.pkl"
)

MINIMAX_HEURISTICS = {
    "minimax": ayo_h4,
    "minimax_h1": ayo_h1,
    "minimax_h2": ayo_h2,
    "minimax_h3": ayo_h3,
    "minimax_h4": ayo_h4,
}
AGENT_NAMES = ("human", "random", "qlearning", *MINIMAX_HEURISTICS.keys())


def build_agent(
    name: str,
    seed: Optional[int],
    q_path: Path,
    minimax_depth: int,
    minimax_time_limit_s: Optional[float],
) -> Agent:
    if name == "human":
        return AyoHumanAgent()
    if name == "random":
        return RandomAgent(seed=seed)
    if name == "qlearning":
        return QLearningAgent.load(q_path, seed=seed)
    if name in MINIMAX_HEURISTICS:
        return MinimaxAgent(
            heuristic=MINIMAX_HEURISTICS[name],
            max_depth=minimax_depth,
            time_limit_s=minimax_time_limit_s,
            use_alpha_beta=True,
            use_transposition_table=False,
            move_order=ayo_immediate_gain_move_order,
        )
    raise ValueError(f"Unknown agent {name!r}. Choices: {sorted(AGENT_NAMES)}.")


def parse_minimax_time(value: str) -> Optional[float]:
    """Parse a positive seconds budget, or ``none`` for fixed-depth search."""
    if value.lower() in {"none", "null", "off", "0"}:
        return None
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("minimax time must be positive or 'none'.")
    return parsed


def play_game(
    game: Ayo,
    agents: Dict[int, Agent],
    verbose: bool = True,
) -> AyoState:
    """Run one full game and return the terminal state."""
    state = game.initial_state()
    if verbose:
        print(game.render(state))
    while not game.is_terminal(state):
        mover = state.to_move
        move = agents[mover].select_move(game, state)
        legal = game.legal_moves(state)
        if move not in legal:
            raise ValueError(
                f"Agent for P{mover} returned illegal move {move}; "
                f"legal moves are {legal}."
            )
        if verbose:
            label = AyoHumanAgent._pit_to_label(mover, move)
            print(f"\n  -> P{mover} plays pit {label} (label)\n")
        state = game.apply_move(state, move)
        if verbose:
            print(game.render(state))
    if verbose:
        _print_result(game, state)
    return state


def _print_result(game: Ayo, state: AyoState) -> None:
    p0 = state.pits[Ayo.P0_STORE]
    p1 = state.pits[Ayo.P1_STORE]
    winner = game.winner(state)
    print(f"\n  Final score — P0 store: {p0}, P1 store: {p1}")
    if winner is None:
        print("  Result: draw.")
    else:
        print(f"  Result: P{winner} wins.")


def main(argv: Optional[list] = None) -> None:
    ap = argparse.ArgumentParser(
        prog="python -m src.cli",
        description="Play Ayo at the terminal.",
    )
    ap.add_argument("--p0", default="human", choices=sorted(AGENT_NAMES))
    ap.add_argument("--p1", default="random", choices=sorted(AGENT_NAMES))
    ap.add_argument(
        "--seed",
        type=int,
        default=None,
        help="RNG seed for random agents and deterministic tie-breaking.",
    )
    ap.add_argument(
        "--q-path",
        type=Path,
        default=DEFAULT_Q_PATH,
        help=(
            "Path to a Q-learning checkpoint pickle. Used whenever either side "
            "is qlearning."
        ),
    )
    ap.add_argument("--minimax-depth", type=int, default=4)
    ap.add_argument("--minimax-time", type=parse_minimax_time, default=1.0)
    args = ap.parse_args(argv)
    game = Ayo()
    agents = {
        0: build_agent(
            args.p0,
            args.seed,
            args.q_path,
            args.minimax_depth,
            args.minimax_time,
        ),
        1: build_agent(
            args.p1,
            args.seed,
            args.q_path,
            args.minimax_depth,
            args.minimax_time,
        ),
    }
    play_game(game, agents)


if __name__ == "__main__":
    main()

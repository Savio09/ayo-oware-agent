"""Play Ayo at the terminal.

Examples::

    # Human (P0) vs. random (P1)
    python -m src.cli

    # Random vs. random, seeded for reproducibility
    python -m src.cli --p0 random --p1 random --seed 42

    # Swap sides
    python -m src.cli --p0 random --p1 human
"""
from __future__ import annotations

import argparse
from typing import Callable, Dict, Optional

from src.agents.base import Agent
from src.agents.human import AyoHumanAgent
from src.agents.random_agent import RandomAgent
from src.games.ayo import Ayo, AyoState

AGENT_FACTORIES: Dict[str, Callable[[Optional[int]], Agent]] = {
    "human": lambda _seed: AyoHumanAgent(),
    "random": lambda seed: RandomAgent(seed=seed),
}


def build_agent(name: str, seed: Optional[int]) -> Agent:
    try:
        return AGENT_FACTORIES[name](seed)
    except KeyError as exc:
        raise ValueError(
            f"Unknown agent {name!r}. Choices: {sorted(AGENT_FACTORIES)}."
        ) from exc


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
        if verbose:
            label = AyoHumanAgent._pit_to_label(mover, move)
            print(f"\n  -> P{mover} plays pit {label}\n")
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
    ap.add_argument("--p0", default="human", choices=sorted(AGENT_FACTORIES))
    ap.add_argument("--p1", default="random", choices=sorted(AGENT_FACTORIES))
    ap.add_argument(
        "--seed",
        type=int,
        default=None,
        help="RNG seed for random agents (ignored by human).",
    )
    args = ap.parse_args(argv)
    game = Ayo()
    agents = {
        0: build_agent(args.p0, args.seed),
        1: build_agent(args.p1, args.seed),
    }
    play_game(game, agents)


if __name__ == "__main__":
    main()

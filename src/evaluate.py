"""Tournament evaluation harness for Ayo agents."""
from __future__ import annotations

import argparse
import csv
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Dict, Iterable, List, Optional, Tuple, Union

from src.agents.base import Agent
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

MINIMAX_HEURISTICS = {
    "minimax_h1": ayo_h1,
    "minimax_h2": ayo_h2,
    "minimax_h3": ayo_h3,
    "minimax_h4": ayo_h4,
}
AGENT_SPECS = ("random", "qlearning", *MINIMAX_HEURISTICS.keys())


@dataclass(frozen=True, slots=True)
class AgentSpecConfig:
    """Configuration needed to instantiate agents fresh per game."""

    agent_a: str
    agent_b: str
    agent_a_q_path: Optional[Path] = None
    agent_b_q_path: Optional[Path] = None
    minimax_depth_limit: int = 4
    minimax_time_limit_s: Optional[float] = 1.0


@dataclass(slots=True)
class SeatMetrics:
    """Per-seat counters accumulated during one game."""

    move_count: int = 0
    total_time_s: float = 0.0
    minimax_move_count: int = 0
    minimax_nodes: int = 0
    minimax_cutoffs: int = 0
    minimax_depth_completed_total: int = 0

    @property
    def avg_time_s(self) -> float:
        if self.move_count == 0:
            return 0.0
        return self.total_time_s / self.move_count

    @property
    def minimax_depth_completed_avg(self) -> float:
        if self.minimax_move_count == 0:
            return 0.0
        return self.minimax_depth_completed_total / self.minimax_move_count


@dataclass(frozen=True, slots=True)
class GameResult:
    """One CSV-ready row for a completed game."""

    game_index: int
    agent_a: str
    agent_b: str
    p0_agent: str
    p1_agent: str
    winner_player: int
    winner_agent: str
    p0_store: int
    p1_store: int
    store_margin_for_a: int
    plies: int
    p0_move_count: int
    p1_move_count: int
    p0_total_time_s: float
    p1_total_time_s: float
    p0_avg_time_s: float
    p1_avg_time_s: float
    p0_minimax_move_count: int
    p1_minimax_move_count: int
    p0_minimax_nodes: int
    p1_minimax_nodes: int
    p0_minimax_cutoffs: int
    p1_minimax_cutoffs: int
    p0_minimax_depth_completed_avg: float
    p1_minimax_depth_completed_avg: float
    minimax_depth_limit: int
    minimax_time_limit_s: Optional[float]


@dataclass(frozen=True, slots=True)
class TournamentSummary:
    """Aggregate metrics printed after a tournament."""

    games: int
    agent_a: str
    agent_b: str
    agent_a_wins: int
    agent_b_wins: int
    draws: int
    agent_a_win_rate_all_games: float
    agent_a_win_rate_decisive_games: float
    agent_a_wilson_low_all_games: float
    agent_a_wilson_high_all_games: float
    avg_plies: float
    avg_store_margin_for_a: float
    agent_a_avg_time_s: float
    agent_b_avg_time_s: float
    agent_a_minimax_nodes: int
    agent_b_minimax_nodes: int


def make_agent(
    spec: str,
    config: AgentSpecConfig,
    seed: Optional[int],
    logical_agent: Optional[str] = None,
) -> Agent[AyoState, int]:
    """Build a fresh agent for one game from a stable spec string."""
    if spec == "random":
        return RandomAgent(seed=seed)
    if spec == "qlearning":
        if logical_agent not in ("A", "B"):
            raise ValueError("qlearning agent construction requires logical_agent A or B.")
        q_path = _q_path_for_logical_agent(logical_agent, config)
        agent = QLearningAgent.load(q_path, seed=seed)
        return agent
    if spec in MINIMAX_HEURISTICS:
        return MinimaxAgent(
            heuristic=MINIMAX_HEURISTICS[spec],
            max_depth=config.minimax_depth_limit,
            time_limit_s=config.minimax_time_limit_s,
            use_alpha_beta=True,
            use_transposition_table=False,
            move_order=ayo_immediate_gain_move_order,
        )
    raise ValueError(f"Unknown agent spec {spec!r}. Choices: {list(AGENT_SPECS)}.")


def run_game(
    game: Ayo,
    config: AgentSpecConfig,
    game_index: int,
    p0_logical: str,
    p1_logical: str,
    seed: Optional[int] = None,
) -> GameResult:
    """Run one game with fresh per-seat agent instances."""
    p0_spec = config.agent_a if p0_logical == "A" else config.agent_b
    p1_spec = config.agent_a if p1_logical == "A" else config.agent_b
    p0_seed = _per_game_seed(seed, game_index, "p0")
    p1_seed = _per_game_seed(seed, game_index, "p1")
    agents = {
        0: make_agent(p0_spec, config, p0_seed, p0_logical),
        1: make_agent(p1_spec, config, p1_seed, p1_logical),
    }
    metrics = {0: SeatMetrics(), 1: SeatMetrics()}

    state = game.initial_state()
    while not game.is_terminal(state):
        player = game.current_player(state)
        agent = agents[player]
        started = perf_counter()
        move = agent.select_move(game, state)
        elapsed = perf_counter() - started
        legal = game.legal_moves(state)
        if move not in legal:
            raise ValueError(
                f"{type(agent).__name__} returned illegal move {move}; "
                f"legal moves are {legal}."
            )

        seat = metrics[player]
        seat.move_count += 1
        seat.total_time_s += elapsed
        if isinstance(agent, MinimaxAgent):
            seat.minimax_move_count += 1
            seat.minimax_nodes += agent.last_stats.nodes
            seat.minimax_cutoffs += agent.last_stats.cutoffs
            seat.minimax_depth_completed_total += agent.last_stats.depth_completed

        state = game.apply_move(state, move)

    return _build_result(
        game=game,
        state=state,
        config=config,
        game_index=game_index,
        p0_logical=p0_logical,
        p1_logical=p1_logical,
        metrics=metrics,
    )


def run_tournament(
    config: AgentSpecConfig,
    n_games: int,
    seed: Optional[int] = None,
    seat_swap: bool = True,
) -> List[GameResult]:
    """Run a tournament, building fresh agents for every game."""
    if n_games < 1:
        raise ValueError("n_games must be at least 1.")
    game = Ayo()
    results: List[GameResult] = []
    split = (n_games + 1) // 2 if seat_swap else n_games
    for game_index in range(n_games):
        if seat_swap and game_index >= split:
            p0_logical, p1_logical = "B", "A"
        else:
            p0_logical, p1_logical = "A", "B"
        results.append(
            run_game(
                game=game,
                config=config,
                game_index=game_index,
                p0_logical=p0_logical,
                p1_logical=p1_logical,
                seed=seed,
            )
        )
    return results


def summarize_results(results: Iterable[GameResult]) -> TournamentSummary:
    """Aggregate per-game rows into report-friendly summary metrics."""
    rows = list(results)
    if not rows:
        raise ValueError("cannot summarize an empty tournament.")
    agent_a = rows[0].agent_a
    agent_b = rows[0].agent_b
    a_wins = sum(row.winner_agent == "A" for row in rows)
    b_wins = sum(row.winner_agent == "B" for row in rows)
    draws = sum(row.winner_agent == "draw" for row in rows)
    decisive = a_wins + b_wins
    ci_low, ci_high = wilson_interval(successes=a_wins, trials=len(rows))

    a_time, a_moves = _logical_time_and_moves(rows, "A")
    b_time, b_moves = _logical_time_and_moves(rows, "B")

    return TournamentSummary(
        games=len(rows),
        agent_a=agent_a,
        agent_b=agent_b,
        agent_a_wins=a_wins,
        agent_b_wins=b_wins,
        draws=draws,
        agent_a_win_rate_all_games=a_wins / len(rows),
        agent_a_win_rate_decisive_games=(a_wins / decisive if decisive else 0.0),
        agent_a_wilson_low_all_games=ci_low,
        agent_a_wilson_high_all_games=ci_high,
        avg_plies=sum(row.plies for row in rows) / len(rows),
        avg_store_margin_for_a=sum(row.store_margin_for_a for row in rows) / len(rows),
        agent_a_avg_time_s=(a_time / a_moves if a_moves else 0.0),
        agent_b_avg_time_s=(b_time / b_moves if b_moves else 0.0),
        agent_a_minimax_nodes=_logical_minimax_nodes(rows, "A"),
        agent_b_minimax_nodes=_logical_minimax_nodes(rows, "B"),
    )


def write_results_csv(path: Union[str, Path], results: Iterable[GameResult]) -> None:
    """Write one CSV row per game."""
    rows = [asdict(result) for result in results]
    if not rows:
        raise ValueError("cannot write an empty tournament.")
    with Path(path).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def wilson_interval(
    successes: int,
    trials: int,
    confidence: float = 0.95,
) -> Tuple[float, float]:
    """Wilson interval for Agent A win vs. not-Agent-A-win over all games."""
    if trials < 1:
        raise ValueError("trials must be at least 1.")
    if not (0 <= successes <= trials):
        raise ValueError("successes must be between 0 and trials.")
    if confidence != 0.95:
        raise ValueError("only 95% Wilson intervals are currently supported.")

    z = 1.959963984540054
    p_hat = successes / trials
    denom = 1 + z * z / trials
    center = (p_hat + z * z / (2 * trials)) / denom
    half_width = (
        z
        * math.sqrt((p_hat * (1 - p_hat) + z * z / (4 * trials)) / trials)
        / denom
    )
    return max(0.0, center - half_width), min(1.0, center + half_width)


def format_summary(summary: TournamentSummary) -> str:
    """Return a concise human-readable tournament summary."""
    return "\n".join(
        [
            f"Games: {summary.games}",
            (
                f"Agent A ({summary.agent_a}) wins: {summary.agent_a_wins}; "
                f"Agent B ({summary.agent_b}) wins: {summary.agent_b_wins}; "
                f"draws: {summary.draws}"
            ),
            (
                "Agent A win rate, all games: "
                f"{summary.agent_a_win_rate_all_games:.3f} "
                f"(95% Wilson CI "
                f"{summary.agent_a_wilson_low_all_games:.3f}-"
                f"{summary.agent_a_wilson_high_all_games:.3f})"
            ),
            (
                "Agent A win rate, decisive games only: "
                f"{summary.agent_a_win_rate_decisive_games:.3f}"
            ),
            f"Average plies: {summary.avg_plies:.2f}",
            f"Average store margin for Agent A: {summary.avg_store_margin_for_a:.2f}",
            f"Agent A average decision time: {summary.agent_a_avg_time_s:.6f}s",
            f"Agent B average decision time: {summary.agent_b_avg_time_s:.6f}s",
            f"Agent A minimax nodes: {summary.agent_a_minimax_nodes}",
            f"Agent B minimax nodes: {summary.agent_b_minimax_nodes}",
        ]
    )


def _build_result(
    game: Ayo,
    state: AyoState,
    config: AgentSpecConfig,
    game_index: int,
    p0_logical: str,
    p1_logical: str,
    metrics: Dict[int, SeatMetrics],
) -> GameResult:
    winner = game.winner(state)
    winner_player = -1 if winner is None else winner
    winner_agent = "draw" if winner is None else (p0_logical if winner == 0 else p1_logical)
    p0_store = state.pits[Ayo.P0_STORE]
    p1_store = state.pits[Ayo.P1_STORE]
    a_store = p0_store if p0_logical == "A" else p1_store
    b_store = p1_store if p0_logical == "A" else p0_store
    p0_metrics = metrics[0]
    p1_metrics = metrics[1]
    return GameResult(
        game_index=game_index,
        agent_a=config.agent_a,
        agent_b=config.agent_b,
        p0_agent=p0_logical,
        p1_agent=p1_logical,
        winner_player=winner_player,
        winner_agent=winner_agent,
        p0_store=p0_store,
        p1_store=p1_store,
        store_margin_for_a=a_store - b_store,
        plies=state.ply,
        p0_move_count=p0_metrics.move_count,
        p1_move_count=p1_metrics.move_count,
        p0_total_time_s=p0_metrics.total_time_s,
        p1_total_time_s=p1_metrics.total_time_s,
        p0_avg_time_s=p0_metrics.avg_time_s,
        p1_avg_time_s=p1_metrics.avg_time_s,
        p0_minimax_move_count=p0_metrics.minimax_move_count,
        p1_minimax_move_count=p1_metrics.minimax_move_count,
        p0_minimax_nodes=p0_metrics.minimax_nodes,
        p1_minimax_nodes=p1_metrics.minimax_nodes,
        p0_minimax_cutoffs=p0_metrics.minimax_cutoffs,
        p1_minimax_cutoffs=p1_metrics.minimax_cutoffs,
        p0_minimax_depth_completed_avg=p0_metrics.minimax_depth_completed_avg,
        p1_minimax_depth_completed_avg=p1_metrics.minimax_depth_completed_avg,
        minimax_depth_limit=config.minimax_depth_limit,
        minimax_time_limit_s=config.minimax_time_limit_s,
    )


def _q_path_for_logical_agent(
    logical_agent: Optional[str],
    config: AgentSpecConfig,
) -> Path:
    if logical_agent == "A":
        q_path = config.agent_a_q_path
    elif logical_agent == "B":
        q_path = config.agent_b_q_path
    else:
        q_path = config.agent_a_q_path or config.agent_b_q_path
    if q_path is None:
        raise ValueError("qlearning agent requires a matching q-path.")
    return q_path


def _per_game_seed(seed: Optional[int], game_index: int, seat: str) -> Optional[int]:
    if seed is None:
        return None
    seat_offset = 0 if seat == "p0" else 1
    return seed + game_index * 2 + seat_offset


def _logical_time_and_moves(rows: List[GameResult], logical: str) -> Tuple[float, int]:
    total_time = 0.0
    moves = 0
    for row in rows:
        if row.p0_agent == logical:
            total_time += row.p0_total_time_s
            moves += row.p0_move_count
        else:
            total_time += row.p1_total_time_s
            moves += row.p1_move_count
    return total_time, moves


def _logical_minimax_nodes(rows: List[GameResult], logical: str) -> int:
    nodes = 0
    for row in rows:
        nodes += row.p0_minimax_nodes if row.p0_agent == logical else row.p1_minimax_nodes
    return nodes


def parse_minimax_time(value: str) -> Optional[float]:
    """Parse a positive seconds budget, or ``none`` for fixed-depth search."""
    if value.lower() in {"none", "null", "off", "0"}:
        return None
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("minimax time must be positive or 'none'.")
    return parsed


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m src.evaluate",
        description="Run reproducible Ayo tournaments.",
    )
    parser.add_argument("--agent-a", required=True, choices=AGENT_SPECS)
    parser.add_argument("--agent-b", required=True, choices=AGENT_SPECS)
    parser.add_argument("--agent-a-q-path", type=Path, default=None)
    parser.add_argument("--agent-b-q-path", type=Path, default=None)
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--no-seat-swap", action="store_true")
    parser.add_argument("--minimax-depth", type=int, default=4)
    parser.add_argument("--minimax-time", type=parse_minimax_time, default=1.0)
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    config = AgentSpecConfig(
        agent_a=args.agent_a,
        agent_b=args.agent_b,
        agent_a_q_path=args.agent_a_q_path,
        agent_b_q_path=args.agent_b_q_path,
        minimax_depth_limit=args.minimax_depth,
        minimax_time_limit_s=args.minimax_time,
    )
    results = run_tournament(
        config=config,
        n_games=args.n,
        seed=args.seed,
        seat_swap=not args.no_seat_swap,
    )
    write_results_csv(args.out, results)
    print(format_summary(summarize_results(results)))


if __name__ == "__main__":
    main()

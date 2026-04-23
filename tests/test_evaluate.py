"""Tests for the Ayo tournament evaluation harness."""
from __future__ import annotations

import csv

import pytest

from src.agents.qlearning import QLearningAgent
from src.evaluate import (
    AgentSpecConfig,
    make_agent,
    parse_args,
    run_tournament,
    summarize_results,
    wilson_interval,
    write_results_csv,
)
from src.games.ayo import Ayo


def comparable_rows(results):
    return [
        (
            row.p0_agent,
            row.p1_agent,
            row.winner_player,
            row.winner_agent,
            row.p0_store,
            row.p1_store,
            row.store_margin_for_a,
            row.plies,
        )
        for row in results
    ]


def test_random_tournament_writes_csv_rows(tmp_path):
    config = AgentSpecConfig(
        agent_a="random",
        agent_b="random",
        minimax_time_limit_s=None,
    )
    results = run_tournament(config, n_games=2, seed=10)
    out = tmp_path / "results.csv"

    write_results_csv(out, results)

    with out.open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert rows[0]["agent_a"] == "random"
    assert rows[0]["agent_b"] == "random"
    assert "p0_move_count" in rows[0]
    assert "minimax_depth_limit" in rows[0]
    assert rows[0]["minimax_time_limit_s"] == ""


def test_tournament_seat_swapping_assigns_both_agents_to_both_seats():
    config = AgentSpecConfig(agent_a="random", agent_b="random")

    results = run_tournament(config, n_games=4, seed=7, seat_swap=True)

    assert [row.p0_agent for row in results] == ["A", "A", "B", "B"]
    assert [row.p1_agent for row in results] == ["B", "B", "A", "A"]


def test_winner_mapping_and_agent_a_store_margin_follow_seat_assignment():
    config = AgentSpecConfig(agent_a="random", agent_b="random")

    results = run_tournament(config, n_games=4, seed=12, seat_swap=True)

    for row in results:
        if row.winner_player == -1:
            assert row.winner_agent == "draw"
        elif row.winner_player == 0:
            assert row.winner_agent == row.p0_agent
        else:
            assert row.winner_agent == row.p1_agent

        expected_margin = (
            row.p0_store - row.p1_store
            if row.p0_agent == "A"
            else row.p1_store - row.p0_store
        )
        assert row.store_margin_for_a == expected_margin


def test_mixed_agent_stats_populate_only_for_minimax_seat():
    config = AgentSpecConfig(
        agent_a="random",
        agent_b="minimax_h1",
        minimax_depth_limit=1,
        minimax_time_limit_s=None,
    )

    results = run_tournament(config, n_games=2, seed=2, seat_swap=True)

    first, second = results
    assert first.p0_agent == "A"
    assert first.p0_minimax_move_count == 0
    assert first.p0_minimax_nodes == 0
    assert first.p0_move_count > 0
    assert first.p0_total_time_s >= 0.0
    assert first.p1_agent == "B"
    assert first.p1_minimax_move_count == first.p1_move_count
    assert first.p1_minimax_nodes > 0
    assert first.p1_minimax_depth_completed_avg == 1.0

    assert second.p0_agent == "B"
    assert second.p0_minimax_move_count == second.p0_move_count
    assert second.p0_minimax_nodes > 0
    assert second.p1_agent == "A"
    assert second.p1_minimax_move_count == 0
    assert second.p1_minimax_nodes == 0
    assert second.p1_total_time_s >= 0.0


def test_wilson_interval_returns_sane_bounds():
    low, high = wilson_interval(successes=3, trials=10)

    assert 0.0 <= low <= 0.3 <= high <= 1.0


def test_summary_uses_all_games_for_agent_a_wilson_interval():
    results = run_tournament(
        AgentSpecConfig(agent_a="random", agent_b="random"),
        n_games=3,
        seed=5,
    )

    summary = summarize_results(results)
    low, high = wilson_interval(summary.agent_a_wins, summary.games)

    assert summary.agent_a_wilson_low_all_games == low
    assert summary.agent_a_wilson_high_all_games == high
    assert summary.agent_a_wins + summary.agent_b_wins + summary.draws == 3


def test_tournament_seed_reproduces_game_outcomes():
    config = AgentSpecConfig(agent_a="random", agent_b="random")

    first = run_tournament(config, n_games=3, seed=123)
    second = run_tournament(config, n_games=3, seed=123)

    assert comparable_rows(first) == comparable_rows(second)


def test_qlearning_paths_are_tied_to_logical_agent(tmp_path):
    game = Ayo()
    state = game.initial_state()
    a_path = tmp_path / "a.pkl"
    b_path = tmp_path / "b.pkl"
    agent_a = QLearningAgent(alpha=0.2, gamma=0.8)
    agent_b = QLearningAgent(alpha=0.3, gamma=0.7)
    agent_a.q_values[(state.q_key(), 0)] = 1.0
    agent_b.q_values[(state.q_key(), 0)] = -1.0
    agent_a.save(a_path)
    agent_b.save(b_path)
    config = AgentSpecConfig(
        agent_a="qlearning",
        agent_b="qlearning",
        agent_a_q_path=a_path,
        agent_b_q_path=b_path,
    )

    loaded_a = make_agent("qlearning", config, seed=1, logical_agent="A")
    loaded_b = make_agent("qlearning", config, seed=1, logical_agent="B")

    assert isinstance(loaded_a, QLearningAgent)
    assert isinstance(loaded_b, QLearningAgent)
    assert loaded_a.alpha == 0.2
    assert loaded_b.alpha == 0.3
    assert loaded_a.q_value(state, 0) == 1.0
    assert loaded_b.q_value(state, 0) == -1.0


def test_invalid_agent_name_and_missing_q_path_fail_clearly():
    config = AgentSpecConfig(agent_a="random", agent_b="random")

    with pytest.raises(ValueError, match="Unknown agent"):
        make_agent("bad", config, seed=0)

    with pytest.raises(ValueError, match="q-path"):
        make_agent(
            "qlearning",
            AgentSpecConfig(agent_a="qlearning", agent_b="random"),
            seed=0,
            logical_agent="A",
        )

    with pytest.raises(ValueError, match="logical_agent"):
        make_agent(
            "qlearning",
            AgentSpecConfig(
                agent_a="qlearning",
                agent_b="random",
                agent_a_q_path=__file__,
            ),
            seed=0,
        )


def test_cli_accepts_none_for_fixed_depth_minimax_time(tmp_path):
    args = parse_args(
        [
            "--agent-a",
            "random",
            "--agent-b",
            "minimax_h1",
            "--out",
            str(tmp_path / "results.csv"),
            "--minimax-time",
            "none",
        ]
    )

    assert args.minimax_time is None

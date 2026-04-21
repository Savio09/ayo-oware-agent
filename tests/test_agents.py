"""Tests for agents and the CLI play-loop.

Covers:
* RandomAgent picks only legal moves, is deterministic under a seed, and
  raises on a terminal state.
* AyoHumanAgent round-trips labels<->pits, accepts valid input, and
  re-prompts on integer-parse errors, out-of-range numbers, and illegal
  moves.
* ``play_game`` runs two random agents to a terminal state without
  throwing, with total seeds conserved at 48.
"""
from __future__ import annotations

from typing import Iterator, List

import pytest

import src.cli as cli
from src.agents.human import AyoHumanAgent
from src.agents.random_agent import RandomAgent
from src.cli import play_game
from src.games.ayo import Ayo, AyoState


@pytest.fixture
def game() -> Ayo:
    return Ayo()


# ---------------------------------------------------------------------------
# RandomAgent
# ---------------------------------------------------------------------------


def test_random_agent_only_picks_legal_moves(game):
    agent = RandomAgent(seed=0)
    state = game.initial_state()
    for _ in range(500):
        if game.is_terminal(state):
            break
        move = agent.select_move(game, state)
        assert move in game.legal_moves(state)
        state = game.apply_move(state, move)


def test_random_agent_is_deterministic_under_seed(game):
    def play_with(seed: int) -> List[int]:
        agent = RandomAgent(seed=seed)
        state = game.initial_state()
        moves: List[int] = []
        for _ in range(30):
            if game.is_terminal(state):
                break
            m = agent.select_move(game, state)
            moves.append(m)
            state = game.apply_move(state, m)
        return moves

    assert play_with(123) == play_with(123)
    # Different seeds should (almost certainly) diverge within 30 moves.
    assert play_with(123) != play_with(456)


def test_random_agent_raises_on_terminal_state(game):
    # Ply-limit terminal: no legal moves.
    pits = tuple([1] * 6 + [10] + [1] * 6 + [5])
    s = AyoState(pits=pits, to_move=0, ply=Ayo.PLY_LIMIT)
    assert game.is_terminal(s)
    with pytest.raises(ValueError):
        RandomAgent(seed=0).select_move(game, s)


# ---------------------------------------------------------------------------
# AyoHumanAgent
# ---------------------------------------------------------------------------


def test_human_label_pit_mapping_is_a_bijection():
    # P0: labels 1..6 <-> pits 0..5
    for label in range(1, 7):
        pit = AyoHumanAgent._label_to_pit(0, label)
        assert AyoHumanAgent._pit_to_label(0, pit) == label
    assert AyoHumanAgent._label_to_pit(0, 1) == 0
    assert AyoHumanAgent._label_to_pit(0, 6) == 5
    # P1: labels 1..6 <-> pits 12..7 (display-left-to-right)
    for label in range(1, 7):
        pit = AyoHumanAgent._label_to_pit(1, label)
        assert AyoHumanAgent._pit_to_label(1, pit) == label
    assert AyoHumanAgent._label_to_pit(1, 1) == 12
    assert AyoHumanAgent._label_to_pit(1, 6) == 7


def _scripted(responses: List[str]) -> Iterator[str]:
    return iter(responses)


def test_human_agent_accepts_valid_label(game):
    inputs = _scripted(["3"])
    outputs: List[str] = []
    agent = AyoHumanAgent(
        input_fn=lambda _: next(inputs),
        output_fn=outputs.append,
    )
    # Label 3 -> pit 2 for P0 from the initial state.
    assert agent.select_move(game, game.initial_state()) == 2
    assert outputs == []  # no error messages on a clean first try


def test_human_agent_reprompts_on_non_integer_input(game):
    inputs = _scripted(["banana", "4"])
    outputs: List[str] = []
    agent = AyoHumanAgent(
        input_fn=lambda _: next(inputs),
        output_fn=outputs.append,
    )
    assert agent.select_move(game, game.initial_state()) == 3  # label 4
    assert any("Not an integer" in msg for msg in outputs)


def test_human_agent_reprompts_on_out_of_range(game):
    inputs = _scripted(["0", "7", "2"])
    outputs: List[str] = []
    agent = AyoHumanAgent(
        input_fn=lambda _: next(inputs),
        output_fn=outputs.append,
    )
    assert agent.select_move(game, game.initial_state()) == 1  # label 2
    assert sum("between 1 and 6" in msg for msg in outputs) == 2


def test_human_agent_reprompts_on_illegal_pit(game):
    # Only pit 2 has seeds on P0's side; all other labels are empty pits.
    pits = tuple([0, 0, 3, 0, 0, 0] + [0] + [4] * 6 + [0])
    s = AyoState(pits=pits, to_move=0, ply=0)
    inputs = _scripted(["1", "3"])  # label 1 empty, label 3 legal
    outputs: List[str] = []
    agent = AyoHumanAgent(
        input_fn=lambda _: next(inputs),
        output_fn=outputs.append,
    )
    assert agent.select_move(game, s) == 2
    assert any("empty or blocked" in msg for msg in outputs)


def test_human_agent_translates_for_p1(game):
    # P1 to move from the initial state. Label 1 should map to pit 12.
    s = AyoState(pits=game.initial_state().pits, to_move=1, ply=0)
    inputs = _scripted(["1"])
    agent = AyoHumanAgent(
        input_fn=lambda _: next(inputs),
        output_fn=lambda _: None,
    )
    assert agent.select_move(game, s) == 12


def test_human_agent_raises_on_terminal_state(game):
    pits = tuple([1] * 6 + [10] + [1] * 6 + [5])
    s = AyoState(pits=pits, to_move=0, ply=Ayo.PLY_LIMIT)
    with pytest.raises(ValueError, match="terminal state"):
        AyoHumanAgent(input_fn=lambda _: "1").select_move(game, s)


# ---------------------------------------------------------------------------
# play_game smoke test
# ---------------------------------------------------------------------------


def test_play_game_runs_two_random_agents_to_terminal(game, capsys):
    agents = {0: RandomAgent(seed=7), 1: RandomAgent(seed=8)}
    final = play_game(game, agents, verbose=False)
    assert game.is_terminal(final)
    assert sum(final.pits) == 48  # seed conservation end-to-end
    # capsys ensures no stray prints with verbose=False.
    captured = capsys.readouterr()
    assert captured.out == ""


def test_play_game_verbose_prints_board_and_result(game, capsys):
    agents = {0: RandomAgent(seed=0), 1: RandomAgent(seed=1)}
    play_game(game, agents, verbose=True)
    out = capsys.readouterr().out
    assert "P0 store" in out and "P1 store" in out
    assert "-> P" in out and "(label)" in out
    assert "Final score" in out
    assert "Result:" in out


def test_play_game_rejects_illegal_agent_move(game):
    class BadAgent:
        def select_move(self, _game, _state):
            return 7

    agents = {0: BadAgent(), 1: RandomAgent(seed=0)}
    with pytest.raises(ValueError, match="illegal move"):
        play_game(game, agents, verbose=False)


def test_main_wires_argparse_agent_factories_and_seed(monkeypatch):
    captured = {}

    def fake_play_game(game, agents):
        captured["game"] = game
        captured["agents"] = agents
        return game.initial_state()

    monkeypatch.setattr(cli, "play_game", fake_play_game)
    cli.main(["--p0", "human", "--p1", "random", "--seed", "123"])

    assert isinstance(captured["game"], Ayo)
    assert isinstance(captured["agents"][0], AyoHumanAgent)
    assert isinstance(captured["agents"][1], RandomAgent)

    state = captured["game"].initial_state()
    expected = RandomAgent(seed=123).select_move(captured["game"], state)
    observed = captured["agents"][1].select_move(captured["game"], state)
    assert observed == expected

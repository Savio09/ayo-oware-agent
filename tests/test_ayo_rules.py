"""Rule-correctness tests for Ayo.

These tests are the foundation for every AI layer built on top, so edge
cases are covered aggressively:

* seed-conservation invariant
* basic sowing without relay / without capture
* capture mechanics (trigger conditions, final seed included)
* skip-store rule during sowing
* skip-origin rule for the current lap only (relay laps may sow into the
  original move's pit)
* multi-lap relay sowing (single relay and compound relay ending in capture)
* feeding rule (delivering moves; terminal when no delivering move exists)
* standard endgame (mover's side empty -> opp collects)
* ply-limit safety valve
* immutability and validation
"""
from __future__ import annotations

from typing import List

import pytest

from src.games.ayo import Ayo, AyoState


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def make_state(pits: List[int], to_move: int = 0, ply: int = 0) -> AyoState:
    assert len(pits) == 14
    return AyoState(pits=tuple(pits), to_move=to_move, ply=ply)


@pytest.fixture
def game() -> Ayo:
    return Ayo()


# ---------------------------------------------------------------------------
# Initial state & invariants
# ---------------------------------------------------------------------------


def test_initial_state_has_48_seeds_and_correct_layout(game):
    s = game.initial_state()
    assert s.pits == (4, 4, 4, 4, 4, 4, 0, 4, 4, 4, 4, 4, 4, 0)
    assert s.to_move == 0
    assert s.ply == 0
    assert sum(s.pits) == 48


def test_initial_state_has_six_legal_moves(game):
    s = game.initial_state()
    assert game.legal_moves(s) == [0, 1, 2, 3, 4, 5]
    assert not game.is_terminal(s)


def test_seed_conservation_over_a_playout(game):
    """Total seeds on the board (including stores) must stay at 48."""
    s = game.initial_state()
    for _ in range(300):  # long enough to hit the ply limit
        moves = game.legal_moves(s)
        if not moves:
            break
        s = game.apply_move(s, moves[0])
        assert sum(s.pits) == 48, f"seed count drift at ply {s.ply}"


def test_state_is_immutable(game):
    s = game.initial_state()
    s2 = game.apply_move(s, 2)
    assert s.pits != s2.pits
    assert s.ply == 0 and s2.ply == 1
    with pytest.raises((AttributeError, TypeError)):
        s.pits = (0,) * 14  # frozen dataclass should forbid assignment


def test_state_is_hashable_and_q_key_omits_ply(game):
    s1 = AyoState(pits=(4,) * 6 + (0,) + (4,) * 6 + (0,), to_move=0, ply=3)
    s2 = AyoState(pits=(4,) * 6 + (0,) + (4,) * 6 + (0,), to_move=0, ply=7)
    assert s1 != s2  # different ply makes the full state unequal
    assert s1.q_key() == s2.q_key()
    assert hash(s1) != hash(s2)  # hash reflects ply
    assert hash(s1.q_key()) == hash(s2.q_key())


# ---------------------------------------------------------------------------
# Legal moves / validation
# ---------------------------------------------------------------------------


def test_legal_moves_player_one(game):
    pits = [0] * 6 + [0] + [4] * 6 + [0]
    s = make_state(pits, to_move=1)
    # P0 side empty -> but it's P1 to move; opp side empty triggers feeding.
    # All of P1's candidate moves will cross into P0's row, so all deliver.
    assert game.legal_moves(s) == [7, 8, 9, 10, 11, 12]


def test_legal_moves_skip_empty_pits(game):
    pits = [0, 0, 3, 0, 0, 0] + [0] + [4] * 6 + [0]
    s = make_state(pits, to_move=0)
    assert game.legal_moves(s) == [2]


def test_apply_move_rejects_opponent_pit(game):
    s = game.initial_state()
    with pytest.raises(ValueError):
        game.apply_move(s, 7)


def test_apply_move_rejects_empty_pit(game):
    pits = [0, 4, 4, 4, 4, 4] + [0] + [4] * 6 + [0]
    s = make_state(pits, to_move=0)
    with pytest.raises(ValueError):
        game.apply_move(s, 0)


# ---------------------------------------------------------------------------
# Basic sowing (no relay, no capture)
# ---------------------------------------------------------------------------


def test_simple_sow_lands_in_empty_pit_with_empty_opposite_no_capture(game):
    # P0 pit 0 has 3 seeds. Opposite of last pit (3) is pit 9 = empty.
    # Pit 7 non-zero so P1 side isn't empty (no feeding rule and no terminal).
    pits = [3, 0, 0, 0, 0, 0] + [0] + [1, 0, 0, 0, 0, 0] + [0]
    s = make_state(pits, to_move=0)
    s2 = game.apply_move(s, 0)
    assert list(s2.pits) == [0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
    assert s2.to_move == 1
    assert s2.ply == 1


def test_sow_crosses_own_store_without_depositing(game):
    # P0 has 3 seeds in pit 4; they sow across pits 5 and the store (skipped)
    # into pits 7 and 8. Neither store should gain a seed.
    pits = [0, 0, 0, 0, 3, 0] + [0] + [0, 0, 0, 0, 0, 1] + [0]
    s = make_state(pits, to_move=0)
    s2 = game.apply_move(s, 4)
    assert s2.pits[Ayo.P0_STORE] == 0
    assert s2.pits[Ayo.P1_STORE] == 0
    # Seeds fell in 5, 7, 8:
    assert s2.pits[5] == 1
    assert s2.pits[7] == 1
    assert s2.pits[8] == 1


# ---------------------------------------------------------------------------
# Capture rule
# ---------------------------------------------------------------------------

# TODO: add a test where final_pos equals the original move's start index
# after a relay chain — confirms the emptied origin can be the final
# landing pit and capture math still holds. (Suggested by test-trace
# verifier agent, 2026-04-21.)


def test_capture_includes_final_seed(game):
    # P0 plays pit 2 (1 seed) -> drops into empty pit 3. Opposite pit 9 has 5.
    # Capture 5 + 1 = 6 into P0 store.  P1 side kept non-empty elsewhere.
    pits = [0, 0, 1, 0, 0, 0] + [0] + [2, 0, 5, 0, 2, 0] + [0]
    s = make_state(pits, to_move=0)
    s2 = game.apply_move(s, 2)
    assert s2.pits[Ayo.P0_STORE] == 6
    assert s2.pits[3] == 0
    assert s2.pits[9] == 0
    assert s2.pits[2] == 0


def test_no_capture_when_opposite_empty(game):
    pits = [0, 0, 1, 0, 0, 0] + [0] + [0, 0, 0, 1, 0, 0] + [0]
    s = make_state(pits, to_move=0)
    s2 = game.apply_move(s, 2)
    assert s2.pits[Ayo.P0_STORE] == 0
    assert s2.pits[3] == 1


def test_no_capture_when_final_pit_on_opponent_side(game):
    # P0 plays pit 4 (3 seeds). Lands in pit 5, 7, 8. Final pit (8) is on opp
    # side so no capture regardless of pit 8's opposite (= pit 4 on own side).
    pits = [0, 0, 0, 0, 3, 0] + [0] + [0, 0, 0, 0, 0, 1] + [0]
    s = make_state(pits, to_move=0)
    s2 = game.apply_move(s, 4)
    assert s2.pits[Ayo.P0_STORE] == 0
    assert s2.pits[8] == 1


# ---------------------------------------------------------------------------
# Skip-origin rule
# ---------------------------------------------------------------------------


def test_twelve_seed_sow_skips_origin_in_first_lap(game):
    # 12 seeds in pit 0, rest empty. Without skip-origin the 12th seed would
    # drop back into pit 0. With skip-origin the 12th drop goes into pit 1,
    # which triggers a compound relay chain (hand-traced):
    #   - first lap fills pits 1..5, 7..12 with 1 seed each (11 drops),
    #   - skip store, skip origin, 12th drop -> pit 1 (now 2 -> relay),
    #   - relay cascades through pits 1, 3, 5, 8, 10, 12,
    #   - last seed lands in pit 1 after wrapping past pit 0 (which gets 1),
    #   - final pit 1 has opposite pit 11 with 2 seeds -> capture 2 + 1 = 3.
    pits = [12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    s = make_state(pits, to_move=0)
    s2 = game.apply_move(s, 0)
    expected = [1, 0, 2, 0, 2, 0, 3, 2, 0, 2, 0, 0, 0, 0]
    assert list(s2.pits) == expected
    # Pit 0 = 1 confirms skip-origin is per-lap (later relay lap sowed into it).


# ---------------------------------------------------------------------------
# Relay sowing
# ---------------------------------------------------------------------------

# TODO: add a test where a relay chain's final seed lands on the opponent's
# side — confirms the "final on opp side -> no capture" branch works after
# relay, not just after a single-lap sow. (Suggested by test-trace
# verifier agent, 2026-04-21.)


def test_single_relay(game):
    # Pit 0 has 1 seed; pit 1 has 1 seed; sowing pit 0 drops into pit 1
    # (already non-empty) -> relay picks up 2 and sows into pits 2 and 3.
    pits = [1, 1, 0, 0, 0, 0] + [0] + [1, 0, 0, 0, 0, 0] + [0]
    s = make_state(pits, to_move=0)
    s2 = game.apply_move(s, 0)
    # Final landing pit = 3 (own side). Opposite = 9 empty -> no capture.
    assert list(s2.pits) == [0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]


def test_relay_chain_with_capture(game):
    # Compound relay that ends back on P0's side with capture.
    # Trace (done by hand):
    #   pit 3 (1 seed) -> drop pit 4 (2 -> 3, relay) -> sow pits 5, (skip
    #   store), 7, 8 (4 -> 5, relay) -> sow 9, 10, 11, 12, (skip store),
    #   0 (empty -> 1). Stop. Capture opp pit 12 (=1) + final seed (=1) = 2.
    pits = [0, 0, 0, 1, 2, 0] + [0] + [0, 4, 0, 0, 0, 0] + [0]
    s = make_state(pits, to_move=0)
    s2 = game.apply_move(s, 3)
    expected = [0, 0, 0, 0, 0, 1, 2, 1, 0, 1, 1, 1, 0, 0]
    assert list(s2.pits) == expected


# ---------------------------------------------------------------------------
# Feeding rule
# ---------------------------------------------------------------------------


def test_feeding_rule_restricts_legal_moves_to_delivering_moves(game):
    # P1 side empty. P0 has seeds in pits 0 (2 seeds) and 5 (2 seeds).
    # Pit 0 sows to pits 1, 2 -> does NOT reach opp side.
    # Pit 5 sows to pits 7, 8 -> DOES reach opp side.
    # So only pit 5 is a legal move under the feeding rule.
    pits = [2, 0, 0, 0, 0, 2] + [0] + [0] * 6 + [0]
    s = make_state(pits, to_move=0)
    assert game.legal_moves(s) == [5]


def test_apply_move_rejects_feeding_illegal_move(game):
    # `apply_move` must enforce the same legality contract as `legal_moves`,
    # because search agents will generate moves from one API and apply via the other.
    pits = [2, 0, 0, 0, 0, 2] + [0] + [0] * 6 + [0]
    s = make_state(pits, to_move=0)
    assert game.legal_moves(s) == [5]
    with pytest.raises(ValueError, match="not legal"):
        game.apply_move(s, 0)


def test_no_delivering_move_makes_constructed_state_terminal(game):
    # P1 side empty. P0 has 2 seeds in pit 0; sowing stays on P0 side so
    # no move delivers to P1 -> legal_moves is empty -> terminal.
    pits = [2, 0, 0, 0, 0, 0] + [0] + [0] * 6 + [0]
    s = make_state(pits, to_move=0)
    assert game.legal_moves(s) == []
    assert game.is_terminal(s)


def test_apply_move_finalizes_when_feeding_becomes_impossible(game):
    # Setup: P1 has a single seed in pit 12, P0 has 2 seeds in pit 1.
    # P1 plays pit 12 -> sows 1 seed into pit 0 (P0 side). P1 side empties.
    # New state: P0 to move; P0 side has pits 0=1, 1=2; P1 side empty.
    # Feeding check: neither pit 0 (sow stays on P0) nor pit 1 (sow stays on
    # P0) delivers to P1 -> game ends and P0's 3 own-side seeds sweep into
    # P0 store.
    predecessor = make_state(
        [0, 2, 0, 0, 0, 0] + [0] + [0, 0, 0, 0, 0, 1] + [0], to_move=1
    )
    s_after = game.apply_move(predecessor, 12)
    assert game.is_terminal(s_after)
    assert s_after.pits[Ayo.P0_STORE] == 3
    assert all(s_after.pits[i] == 0 for i in Ayo.P0_PITS)
    assert all(s_after.pits[i] == 0 for i in Ayo.P1_PITS)


# ---------------------------------------------------------------------------
# Standard endgame
# ---------------------------------------------------------------------------


def test_mover_with_empty_side_opponent_collects_remaining_seeds(game):
    # Exercises the "own-side empty after apply_move" branch of finalize.
    # A capture that takes the opponent's last seeds leaves the opponent with
    # an empty side on their turn. Any seeds still on the previous mover's
    # side are swept into the previous mover's store.
    predecessor = make_state(
        [0, 0, 1, 0, 2, 0] + [0] + [0, 0, 3, 0, 0, 0] + [0], to_move=0
    )
    # P0 plays pit 2 (1 seed -> pit 3 which is empty). Opposite pit 9 has 3.
    # Capture: 3 + 1 = 4 into P0 store. After capture P1 side is all zero.
    # Finalize fires own_empty branch: pit 4's 2 seeds sweep into P0 store.
    s_after = game.apply_move(predecessor, 2)
    assert game.is_terminal(s_after)
    assert s_after.pits[Ayo.P0_STORE] == 6  # 4 from capture + 2 from sweep
    assert s_after.pits[Ayo.P1_STORE] == 0
    assert all(s_after.pits[i] == 0 for i in Ayo.P0_PITS)
    assert all(s_after.pits[i] == 0 for i in Ayo.P1_PITS)
    assert game.winner(s_after) == 0


# ---------------------------------------------------------------------------
# Ply-limit safety valve
# ---------------------------------------------------------------------------


def test_ply_limit_terminates_game_and_scores_by_stores_only(game):
    # Construct a state already at the ply limit. Seeds on the board are
    # ignored; winner decided by stores.
    pits = [1, 1, 1, 1, 1, 1] + [10] + [1, 1, 1, 1, 1, 1] + [5]
    s = make_state(pits, to_move=0, ply=Ayo.PLY_LIMIT)
    assert game.legal_moves(s) == []
    assert game.is_terminal(s)
    assert game.winner(s) == 0
    assert game.utility(s, 0) == 1.0
    assert game.utility(s, 1) == -1.0


def test_ply_limit_draw_when_stores_tie(game):
    pits = [1, 1, 1, 1, 1, 1] + [5] + [1, 1, 1, 1, 1, 1] + [5]
    s = make_state(pits, to_move=0, ply=Ayo.PLY_LIMIT)
    assert game.is_terminal(s)
    assert game.winner(s) is None
    assert game.utility(s, 0) == 0.0


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def test_render_produces_nonempty_multiline_string(game):
    s = game.initial_state()
    out = game.render(s)
    assert isinstance(out, str)
    assert "P0" in out and "P1" in out
    assert out.count("\n") >= 4


def test_render_shows_player_relative_labels_and_display_order(game):
    s = make_state(list(range(14)), to_move=1, ply=12)
    out = game.render(s)
    assert "       1    2    3    4    5    6 " in out
    assert "  P1:  [12] [11] [10] [ 9] [ 8] [ 7]" in out
    assert "  P0:  [ 0] [ 1] [ 2] [ 3] [ 4] [ 5]" in out

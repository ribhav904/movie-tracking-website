import pytest

from app.services.arena import battle_score, expected_score, updated_elo


def test_equal_players_have_equal_expected_score() -> None:
    assert expected_score(1500, 1500) == pytest.approx(0.5)


def test_elo_win_transfers_equal_points() -> None:
    winner = updated_elo(1500, 1500, 1.0, 40)
    loser = updated_elo(1500, 1500, 0.0, 40)
    assert winner == pytest.approx(1520)
    assert loser == pytest.approx(1480)
    assert winner + loser == pytest.approx(3000)


def test_tie_between_equal_players_does_not_change_rating() -> None:
    assert updated_elo(1500, 1500, 0.5, 40) == pytest.approx(1500)


def test_battle_score_is_bounded_and_centered() -> None:
    assert battle_score(1500) == 5.0
    assert 0 < battle_score(500) < 5
    assert 5 < battle_score(2500) < 10

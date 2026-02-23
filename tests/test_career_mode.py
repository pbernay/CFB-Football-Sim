from pathlib import Path

from cfbSimulation.logic.career import CareerManager


def test_create_career_generates_schedule_and_save(tmp_path: Path):
    manager = CareerManager(save_path=tmp_path / "career.json", seed=13)
    career = manager.create_new_career("Alex Stone", "Balanced", "tID1", weeks=4)

    assert career.coach_name == "Alex Stone"
    assert career.team_id == "tID1"
    assert len(career.schedule) == 4
    assert (tmp_path / "career.json").exists()


def test_play_next_game_updates_record_and_marks_played(tmp_path: Path):
    manager = CareerManager(save_path=tmp_path / "career.json", seed=7)
    career = manager.create_new_career("Jordan", "Run Heavy", "tID1", weeks=2)

    career, result, game = manager.play_next_game(career)

    assert game.played is True
    assert result.home_team.score >= 0
    assert result.away_team.score >= 0
    assert career.wins + career.losses == 1
    assert career.current_week == 2

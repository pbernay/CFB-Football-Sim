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


def test_decisions_update_career_progression(tmp_path: Path):
    manager = CareerManager(save_path=tmp_path / "career.json", seed=4)
    career = manager.create_new_career("Taylor", "Defensive Minded", "tID1", weeks=2)

    scenario = manager.get_weekly_scenario(career)
    option = scenario.options[0]
    career = manager.apply_decision(career, scenario.key, option.key)

    assert len(career.decision_history) == 1
    assert career.morale != 50 or career.defense_modifier != 0 or career.offense_modifier != 0


def test_career_resets_between_seasons(tmp_path: Path):
    manager = CareerManager(save_path=tmp_path / "career.json", seed=9)
    career = manager.create_new_career("Casey", "Balanced", "tID1", weeks=1)

    career, *_ = manager.play_next_game(career)
    prior_level = career.coach_level
    career = manager.reset_for_new_season(career, weeks=3)

    assert career.season == 2
    assert career.wins == 0
    assert career.losses == 0
    assert career.current_week == 1
    assert len(career.schedule) == 3
    assert career.coach_level == prior_level

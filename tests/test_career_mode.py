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



def test_strategy_and_starter_plan_saved(tmp_path: Path):
    manager = CareerManager(save_path=tmp_path / "career.json", seed=21)
    career = manager.create_new_career("Morgan", "Balanced", "tID1", weeks=3)

    career = manager.set_week_strategy(career, week=1, strategy_name="Air Raid")
    team_players = manager.repository.get_players_for_team("tID1")
    starters = {}
    for player in team_players:
        if player.position in {"QB", "RB", "WR"} and player.position not in starters:
            starters[player.position] = player.player_id
    career = manager.set_week_starters(career, week=1, starters=starters)

    loaded = manager.load()
    assert loaded is not None
    assert loaded.strategy_plan[1] == "Air Raid"
    assert loaded.starter_plan[1]["QB"]


def test_auto_starters_cover_all_core_positions(tmp_path: Path):
    manager = CareerManager(save_path=tmp_path / "career.json", seed=11)
    career = manager.create_new_career("Auto", "Balanced", "tID1", weeks=1)

    starters = manager.auto_set_best_starters(career)

    for pos in {"QB", "RB", "WR", "TE", "OT", "OG", "C", "DE", "DT", "LB", "CB", "S", "K", "P"}:
        assert pos in starters


def test_decision_can_increase_recruiting_modifier(tmp_path: Path):
    manager = CareerManager(save_path=tmp_path / "career.json", seed=5)
    career = manager.create_new_career("Recruit", "Balanced", "tID1", weeks=2)

    recruiting = next(s for s in manager.list_decision_scenarios() if s.key == "recruiting")
    host = next(o for o in recruiting.options if o.key == "host")
    manager.apply_decision(career, recruiting.key, host.key)

    assert career.recruiting_modifier > 0


def test_staff_auto_starters_reflect_coordinator_quality(tmp_path: Path):
    manager = CareerManager(save_path=tmp_path / "career.json", seed=3)
    career = manager.create_new_career("Staff", "Balanced", "tID1", weeks=1)

    career.coaching_staff["Offensive Coordinator"]["overall"] = 95
    strong = manager.auto_set_best_starters(career)

    career.coaching_staff["Offensive Coordinator"]["overall"] = 40
    weak = manager.auto_set_best_starters(career)

    roster = {str(p.get("player_id")): int(p.get("overall", 0)) for p in career.roster if str(p.get("position")) == "QB"}
    assert roster[strong["QB"]] >= roster[weak["QB"]]


def test_head_scout_restricts_promotion_and_regens_points(tmp_path: Path):
    manager = CareerManager(save_path=tmp_path / "career.json", seed=6)
    career = manager.create_new_career("Scout", "Balanced", "tID1", weeks=1)

    try:
        manager.promote_staff_member(career, "Head Scout", "QB Coach")
        assert False, "Expected ValueError when promoting Head Scout"
    except ValueError:
        pass

    career.coaching_staff["Head Scout"]["overall"] = 90
    regen_high = manager.scouting_points_regen(career)
    career.coaching_staff["Head Scout"]["overall"] = 50
    regen_low = manager.scouting_points_regen(career)

    assert regen_high > regen_low

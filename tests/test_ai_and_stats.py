from pathlib import Path

from cfbSimulation.logic.career import CareerManager
from cfbSimulation.logic.player_stats import PlayerStatsManager


def test_ai_difficulty_profiles_and_counter_scaling(tmp_path: Path):
    manager = CareerManager(save_path=tmp_path / "career.json", seed=31)
    profiles = manager.ai_difficulty_profiles()

    assert profiles["Heisman"]["rating_bonus"] > profiles["Easy"]["rating_bonus"]

    career = manager.create_new_career("A", "Balanced", "tID1", weeks=2, ai_difficulty="Heisman")
    base = manager.simulator.predefined_strategies()["Air Raid"]
    counter_one = manager._counter_strategy(base, career)
    career.ai_adaptation["Air Raid"] = 4
    counter_two = manager._counter_strategy(base, career)

    assert counter_two.defensive_focus >= counter_one.defensive_focus


def test_ai_adaptation_tracks_repeated_strategy(tmp_path: Path):
    manager = CareerManager(save_path=tmp_path / "career.json", seed=10)
    career = manager.create_new_career("Coach", "Balanced", "tID1", weeks=3, ai_difficulty="Hard")

    career = manager.set_week_strategy(career, 1, "Air Raid")
    career, _, _ = manager.play_next_game(career)
    career = manager.set_week_strategy(career, 2, "Air Raid")
    career, _, _ = manager.play_next_game(career)

    assert career.ai_adaptation.get("Air Raid", 0) >= 2


def test_player_stats_record_and_compare(tmp_path: Path):
    manager = CareerManager(save_path=tmp_path / "career.json", seed=5)
    stats_manager = PlayerStatsManager(save_path=tmp_path / "stats.json", seed=5)
    manager.stats_manager = stats_manager

    career = manager.create_new_career("Stats", "Balanced", "tID1", weeks=1)
    career, result, _ = manager.play_next_game(career)

    leaders = stats_manager.top_players(limit=5)
    assert leaders
    compared = stats_manager.compare_players([leaders[0].player_id])
    assert compared
    assert compared[0].games_played >= 1
    assert result.home_team.score >= 0

from cfbSimulation.logic.season import SeasonManager


def test_start_season_creates_schedule():
    manager = SeasonManager(seed=11)
    season = manager.start_season("tID1", weeks=4)

    assert season.team_id == "tID1"
    assert season.team_name
    assert len(season.schedule) == 4


def test_play_week_updates_state():
    manager = SeasonManager(seed=5)
    season = manager.start_season("tID1", weeks=2)

    season, result, played = manager.play_next_game(season)

    assert played.played is True
    assert season.wins + season.losses == 1
    assert season.current_week == 2
    assert result.home_team.score >= 0
    assert result.away_team.score >= 0

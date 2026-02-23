from cfbSimulation.data.repository import DatabaseRepository
from cfbSimulation.logic.simulator import GameSimulator


def test_database_has_teams():
    repo = DatabaseRepository()
    teams = repo.list_teams(limit=5)
    assert len(teams) == 5


def test_simulate_game_generates_scores():
    sim = GameSimulator(seed=123)
    result = sim.simulate_single_game("tID1", "tID2")
    assert result.home_team.score >= 0
    assert result.away_team.score >= 0
    assert result.home_team.name
    assert result.away_team.name


def test_strategies_influence_scoring_profile():
    sim = GameSimulator(seed=42)
    profiles = sim.predefined_strategies()

    aggressive_points = 0
    conservative_points = 0
    games = 60
    for _ in range(games):
        result = sim.simulate_single_game(
            "tID1",
            "tID2",
            home_strategy=profiles["Air Raid"],
            away_strategy=profiles["Ball Control"],
        )
        aggressive_points += result.home_team.score
        conservative_points += result.away_team.score

    assert aggressive_points / games > conservative_points / games

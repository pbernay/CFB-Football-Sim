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

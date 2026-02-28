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


def test_snapshot_includes_potential_and_position_ratings():
    sim = GameSimulator(seed=11)
    snapshot = sim.build_team_snapshot("tID1")

    assert 0 <= snapshot.potential_rating <= 100
    assert 0 <= snapshot.offense_position_rating <= 100
    assert 0 <= snapshot.defense_position_rating <= 100
    assert 0 <= snapshot.special_position_rating <= 100


def test_high_potential_team_reports_higher_potential_rating(tmp_path):
    from cfbSimulation.data.repository import PlayerRecord, TeamRecord

    db = tmp_path / "ratings.db"
    repo = DatabaseRepository(db_path=db)
    repo.initialize_schema()

    repo.create_team(TeamRecord(team_id="tIDH", name="High Pot", location="City"))
    repo.create_team(TeamRecord(team_id="tIDL", name="Low Pot", location="City"))

    positions = ["QB", "RB", "WR", "TE", "OT", "OG", "C", "DE", "DT", "LB", "CB", "S", "K", "P"]
    for idx, pos in enumerate(positions):
        repo.create_player(
            PlayerRecord(
                player_id=f"h{idx}",
                team_id="tIDH",
                first_name="A",
                last_name="B",
                position=pos,
                overall=70,
                potential=95,
            )
        )
        repo.create_player(
            PlayerRecord(
                player_id=f"l{idx}",
                team_id="tIDL",
                first_name="C",
                last_name="D",
                position=pos,
                overall=70,
                potential=72,
            )
        )

    sim = GameSimulator(repository=repo, seed=3)
    high = sim.build_team_snapshot("tIDH")
    low = sim.build_team_snapshot("tIDL")

    assert high.potential_rating > low.potential_rating

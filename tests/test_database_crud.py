from __future__ import annotations

import time
from pathlib import Path

from cfbSimulation.data.repository import DatabaseRepository, PlayerRecord, TeamRecord


def _build_repository(tmp_path: Path) -> DatabaseRepository:
    repo = DatabaseRepository(db_path=tmp_path / "crud_test.db")
    repo.initialize_schema()
    return repo


def test_team_crud_roundtrip(tmp_path: Path):
    repo = _build_repository(tmp_path)

    created = repo.create_team(
        TeamRecord(
            team_id="tID9000",
            name="Coastal Coders",
            location="Remote",
            conference_id="cID1",
            coach_id="coID1",
            wins=1,
            losses=2,
            ties=0,
        )
    )
    assert created.name == "Coastal Coders"

    updated = repo.update_team(
        TeamRecord(
            team_id="tID9000",
            name="Coastal Coders United",
            location="Remote",
            conference_id="cID1",
            coach_id="coID2",
            wins=4,
            losses=2,
            ties=0,
        )
    )
    assert updated is not None
    assert updated.name == "Coastal Coders United"
    assert updated.wins == 4

    assert repo.delete_team("tID9000") is True
    assert repo.get_team("tID9000") is None


def test_player_crud_roundtrip(tmp_path: Path):
    repo = _build_repository(tmp_path)
    repo.create_team(TeamRecord(team_id="tID9001", name="Schema State", location="Austin"))

    created = repo.create_player(
        PlayerRecord(
            player_id="pID8001",
            team_id="tID9001",
            first_name="Ada",
            last_name="Lovelace",
            position="QB",
            overall=88,
            age=21,
            year="Junior",
            potential=92,
            player_status="Current",
        )
    )
    assert created.first_name == "Ada"

    updated = repo.update_player(
        PlayerRecord(
            player_id="pID8001",
            team_id="tID9001",
            first_name="Ada",
            last_name="Lovelace",
            position="QB",
            overall=91,
            age=22,
            year="Senior",
            potential=94,
            player_status="Current",
        )
    )
    assert updated is not None
    assert updated.overall == 91
    assert updated.year == "Senior"

    players = repo.get_players_for_team("tID9001")
    assert len(players) == 1
    assert players[0].player_id == "pID8001"

    assert repo.delete_player("pID8001") is True
    assert repo.get_player("pID8001") is None


def test_bulk_mock_data_query_performance(tmp_path: Path):
    repo = _build_repository(tmp_path)
    team_count = 120
    players_per_team = 85

    for i in range(team_count):
        repo.create_team(
            TeamRecord(
                team_id=f"tID{i:04}",
                name=f"Team {i}",
                location=f"City {i}",
                conference_id=f"cID{i % 10}",
                coach_id=f"coID{i}",
            )
        )

    total_players = team_count * players_per_team
    for i in range(total_players):
        team_idx = i % team_count
        repo.create_player(
            PlayerRecord(
                player_id=f"pID{i:06}",
                team_id=f"tID{team_idx:04}",
                first_name="Test",
                last_name=f"Player{i}",
                position=("QB" if i % 20 == 0 else "WR"),
                overall=60 + (i % 40),
                age=18 + (i % 5),
                year=("Freshman" if i % 4 == 0 else "Sophomore"),
                potential=65 + (i % 30),
                player_status="Current",
            )
        )

    start = time.perf_counter()
    teams = repo.list_teams()
    for team in teams:
        _ = repo.get_players_for_team(team.team_id)
    elapsed = time.perf_counter() - start

    assert len(teams) == team_count
    assert elapsed < 2.5

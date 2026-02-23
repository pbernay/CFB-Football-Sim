"""Database access helpers for the CFB simulation."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "datafiles" / "saveData" / "theDatabase.db"


@dataclass(frozen=True)
class TeamRecord:
    team_id: str
    name: str
    location: str


@dataclass(frozen=True)
class PlayerRecord:
    player_id: str
    team_id: str
    first_name: str
    last_name: str
    position: str
    overall: int
    age: int = 20
    year: str = "Freshman"
    potential: int = 60
    player_status: str = "Current"


class DatabaseRepository:
    """Read-only wrapper around the simulation SQLite database."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def health_check(self) -> None:
        with self._connect() as conn:
            conn.execute("SELECT 1")

    def list_teams(self, limit: int | None = None) -> list[TeamRecord]:
        query = 'SELECT TeamID, "Team Name", Location FROM Teams ORDER BY TeamID'
        params: tuple[object, ...] = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            TeamRecord(team_id=row["TeamID"], name=row["Team Name"], location=row["Location"])
            for row in rows
        ]

    def get_team(self, team_id: str) -> TeamRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                'SELECT TeamID, "Team Name", Location FROM Teams WHERE TeamID = ?',
                (team_id,),
            ).fetchone()

        if row is None:
            return None

        return TeamRecord(team_id=row["TeamID"], name=row["Team Name"], location=row["Location"])

    def get_players_for_team(self, team_id: str) -> list[PlayerRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT PlayerID, TeamID, Fname, Lname, Position, Overall
                    , Age, Year, Potential, PlayerStatus
                FROM Players
                WHERE TeamID = ?
                ORDER BY Overall DESC
                """,
                (team_id,),
            ).fetchall()

        return [
            PlayerRecord(
                player_id=row["PlayerID"],
                team_id=row["TeamID"],
                first_name=row["Fname"],
                last_name=row["Lname"],
                position=row["Position"],
                overall=int(row["Overall"]),
                age=int(row["Age"]),
                year=row["Year"],
                potential=int(row["Potential"]),
                player_status=row["PlayerStatus"],
            )
            for row in rows
        ]

    def get_two_random_team_ids(self) -> tuple[str, str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT TeamID FROM Teams ORDER BY RANDOM() LIMIT 2").fetchall()
        return rows[0]["TeamID"], rows[1]["TeamID"]

    def iter_team_ids(self) -> Iterable[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT TeamID FROM Teams ORDER BY TeamID").fetchall()
        for row in rows:
            yield row["TeamID"]

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
    conference_id: str | None = None
    coach_id: str | None = None
    wins: int = 0
    losses: int = 0
    ties: int = 0


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
    """Wrapper around the simulation SQLite database."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize_schema(self) -> None:
        """Create core tables/indexes for Teams and Players if missing."""
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS Teams (
                    TeamID TEXT PRIMARY KEY,
                    "Team Name" TEXT NOT NULL,
                    Wins INTEGER NOT NULL DEFAULT 0,
                    Losses INTEGER NOT NULL DEFAULT 0,
                    Ties INTEGER NOT NULL DEFAULT 0,
                    ConfrenceID TEXT,
                    CoachID TEXT,
                    Location TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS Players (
                    PlayerID TEXT PRIMARY KEY,
                    Fname TEXT NOT NULL,
                    Lname TEXT NOT NULL,
                    Position TEXT NOT NULL,
                    Overall INTEGER NOT NULL,
                    TeamID TEXT,
                    Age INTEGER NOT NULL,
                    Year TEXT NOT NULL,
                    InjuryType TEXT,
                    InjuryDuration INTEGER,
                    Potential INTEGER NOT NULL,
                    PlayerStatus TEXT NOT NULL,
                    Hometown TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (TeamID) REFERENCES Teams (TeamID) ON DELETE SET NULL
                );

                CREATE INDEX IF NOT EXISTS idx_players_team ON Players (TeamID);
                CREATE INDEX IF NOT EXISTS idx_players_position ON Players (Position);
                CREATE INDEX IF NOT EXISTS idx_teams_name ON Teams ("Team Name");
                """
            )

    def health_check(self) -> None:
        with self._connect() as conn:
            conn.execute("SELECT 1")

    def list_teams(self, limit: int | None = None) -> list[TeamRecord]:
        query = (
            'SELECT TeamID, "Team Name", Location, ConfrenceID, CoachID, '
            'COALESCE(Wins, 0) as Wins, COALESCE(Losses, 0) as Losses, COALESCE(Ties, 0) as Ties '
            "FROM Teams ORDER BY TeamID"
        )
        params: tuple[object, ...] = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            TeamRecord(
                team_id=row["TeamID"],
                name=row["Team Name"],
                location=row["Location"],
                conference_id=row["ConfrenceID"],
                coach_id=row["CoachID"],
                wins=int(row["Wins"]),
                losses=int(row["Losses"]),
                ties=int(row["Ties"]),
            )
            for row in rows
        ]

    def get_team(self, team_id: str) -> TeamRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                'SELECT TeamID, "Team Name", Location, ConfrenceID, CoachID, '
                'COALESCE(Wins, 0) as Wins, COALESCE(Losses, 0) as Losses, COALESCE(Ties, 0) as Ties '
                "FROM Teams WHERE TeamID = ?",
                (team_id,),
            ).fetchone()

        if row is None:
            return None

        return TeamRecord(
            team_id=row["TeamID"],
            name=row["Team Name"],
            location=row["Location"],
            conference_id=row["ConfrenceID"],
            coach_id=row["CoachID"],
            wins=int(row["Wins"]),
            losses=int(row["Losses"]),
            ties=int(row["Ties"]),
        )

    def create_team(self, team: TeamRecord) -> TeamRecord:
        with self._connect() as conn:
            conn.execute(
                '''
                INSERT INTO Teams (TeamID, "Team Name", Location, ConfrenceID, CoachID, Wins, Losses, Ties)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    team.team_id,
                    team.name,
                    team.location,
                    team.conference_id,
                    team.coach_id,
                    team.wins,
                    team.losses,
                    team.ties,
                ),
            )
        created = self.get_team(team.team_id)
        if created is None:
            raise RuntimeError(f"Unable to create team {team.team_id}")
        return created

    def update_team(self, team: TeamRecord) -> TeamRecord | None:
        with self._connect() as conn:
            cursor = conn.execute(
                '''
                UPDATE Teams
                SET "Team Name" = ?, Location = ?, ConfrenceID = ?, CoachID = ?, Wins = ?, Losses = ?, Ties = ?
                WHERE TeamID = ?
                ''',
                (
                    team.name,
                    team.location,
                    team.conference_id,
                    team.coach_id,
                    team.wins,
                    team.losses,
                    team.ties,
                    team.team_id,
                ),
            )
        if cursor.rowcount == 0:
            return None
        return self.get_team(team.team_id)

    def delete_team(self, team_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM Teams WHERE TeamID = ?", (team_id,))
        return cursor.rowcount > 0

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

    def get_player(self, player_id: str) -> PlayerRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT PlayerID, TeamID, Fname, Lname, Position, Overall
                    , Age, Year, Potential, PlayerStatus
                FROM Players
                WHERE PlayerID = ?
                """,
                (player_id,),
            ).fetchone()
        if row is None:
            return None
        return PlayerRecord(
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

    def create_player(self, player: PlayerRecord) -> PlayerRecord:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO Players (PlayerID, TeamID, Fname, Lname, Position, Overall, Age, Year, Potential, PlayerStatus)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    player.player_id,
                    player.team_id,
                    player.first_name,
                    player.last_name,
                    player.position,
                    player.overall,
                    player.age,
                    player.year,
                    player.potential,
                    player.player_status,
                ),
            )
        created = self.get_player(player.player_id)
        if created is None:
            raise RuntimeError(f"Unable to create player {player.player_id}")
        return created

    def update_player(self, player: PlayerRecord) -> PlayerRecord | None:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE Players
                SET TeamID = ?, Fname = ?, Lname = ?, Position = ?, Overall = ?, Age = ?,
                    Year = ?, Potential = ?, PlayerStatus = ?
                WHERE PlayerID = ?
                """,
                (
                    player.team_id,
                    player.first_name,
                    player.last_name,
                    player.position,
                    player.overall,
                    player.age,
                    player.year,
                    player.potential,
                    player.player_status,
                    player.player_id,
                ),
            )
        if cursor.rowcount == 0:
            return None
        return self.get_player(player.player_id)

    def delete_player(self, player_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM Players WHERE PlayerID = ?", (player_id,))
        return cursor.rowcount > 0

    def get_two_random_team_ids(self) -> tuple[str, str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT TeamID FROM Teams ORDER BY RANDOM() LIMIT 2").fetchall()
        return rows[0]["TeamID"], rows[1]["TeamID"]

    def iter_team_ids(self) -> Iterable[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT TeamID FROM Teams ORDER BY TeamID").fetchall()
        for row in rows:
            yield row["TeamID"]

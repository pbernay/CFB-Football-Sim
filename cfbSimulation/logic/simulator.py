"""Core single-game simulation engine."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from cfbSimulation.data.repository import DatabaseRepository, PlayerRecord, TeamRecord


OFFENSE_POSITIONS = {"QB", "RB", "WR", "TE", "OT", "OG", "C"}
DEFENSE_POSITIONS = {"DE", "DT", "LB", "CB", "S"}


@dataclass
class TeamSnapshot:
    team_id: str
    name: str
    location: str
    offensive_rating: float
    defensive_rating: float
    special_teams_rating: float
    overall_rating: float
    score: int = 0
    players: list[PlayerRecord] = field(default_factory=list)


@dataclass
class GameResult:
    home_team: TeamSnapshot
    away_team: TeamSnapshot
    drives_log: list[str]


class GameSimulator:
    def __init__(self, repository: DatabaseRepository | None = None, seed: int | None = None):
        self.repository = repository or DatabaseRepository()
        self.random = random.Random(seed)

    def build_team_snapshot(self, team_id: str) -> TeamSnapshot:
        team: TeamRecord | None = self.repository.get_team(team_id)
        if team is None:
            raise ValueError(f"Unknown team ID: {team_id}")

        players = self.repository.get_players_for_team(team_id)
        if not players:
            raise ValueError(f"No players found for team ID: {team_id}")

        offense = self._average_by_positions(players, OFFENSE_POSITIONS)
        defense = self._average_by_positions(players, DEFENSE_POSITIONS)
        special = self._average_by_positions(players, {"K", "P"})
        overall = round((offense + defense + special) / 3, 2)

        return TeamSnapshot(
            team_id=team.team_id,
            name=team.name,
            location=team.location,
            offensive_rating=offense,
            defensive_rating=defense,
            special_teams_rating=special,
            overall_rating=overall,
            players=players,
        )

    @staticmethod
    def _average_by_positions(players: list[PlayerRecord], positions: set[str]) -> float:
        selected = [p.overall for p in players if p.position in positions]
        if not selected:
            return 50.0
        return round(sum(selected) / len(selected), 2)

    def simulate_single_game(self, home_team_id: str, away_team_id: str) -> GameResult:
        home = self.build_team_snapshot(home_team_id)
        away = self.build_team_snapshot(away_team_id)
        drives_log: list[str] = []

        offense, defense = home, away
        for drive in range(1, 21):
            points = self._simulate_drive(offense, defense)
            offense.score += points
            if points:
                drives_log.append(f"Drive {drive}: {offense.name} scored {points}")
            offense, defense = defense, offense

        if home.score == away.score:
            for ot_drive in range(1, 5):
                points = self._simulate_drive(offense, defense)
                offense.score += points
                if points:
                    drives_log.append(f"OT {ot_drive}: {offense.name} scored {points}")
                offense, defense = defense, offense
                if home.score != away.score and ot_drive % 2 == 0:
                    break

        return GameResult(home_team=home, away_team=away, drives_log=drives_log)

    def _simulate_drive(self, offense: TeamSnapshot, defense: TeamSnapshot) -> int:
        attack_edge = offense.offensive_rating / max(offense.offensive_rating + defense.defensive_rating, 1)
        special_modifier = (offense.special_teams_rating - 70) / 200
        scoring_chance = max(0.15, min(0.75, attack_edge + special_modifier))

        if self.random.random() > scoring_chance:
            return 0

        play = self.random.choices(["td", "fg", "empty"], weights=[0.45, 0.35, 0.2], k=1)[0]
        if play == "td":
            pat_good = self.random.random() < offense.special_teams_rating / 100
            return 7 if pat_good else 6
        if play == "fg":
            return 3 if self.random.random() < offense.special_teams_rating / 100 else 0
        return 0


def format_scoreboard(result: GameResult) -> str:
    winner = result.home_team if result.home_team.score >= result.away_team.score else result.away_team
    return (
        "\n".join(
            [
                "=" * 60,
                "               CFB Football Sim - Final",
                "=" * 60,
                f"Home: {result.home_team.name:25} {result.home_team.score:>3}",
                f"Away: {result.away_team.name:25} {result.away_team.score:>3}",
                "-" * 60,
                f"Winner: {winner.name}",
                "=" * 60,
            ]
        )
    )

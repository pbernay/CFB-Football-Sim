"""Core single-game simulation engine."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from cfbSimulation.data.repository import DatabaseRepository, PlayerRecord, TeamRecord
from cfbSimulation.logic.advanced_ratings import team_potential_rating, unit_position_rating
from cfbSimulation.logic.boom_bust import BoomBustContext, BoomBustEngine


OFFENSE_POSITIONS = {"QB", "RB", "WR", "TE", "OT", "OG", "C"}
DEFENSE_POSITIONS = {"DE", "DT", "LB", "CB", "S"}


@dataclass(frozen=True)
class StrategyProfile:
    name: str
    aggressiveness: float = 0.5
    tempo: float = 0.5
    defensive_focus: float = 0.5
    risk_tolerance: float = 0.5


@dataclass
class TeamSnapshot:
    team_id: str
    name: str
    location: str
    offensive_rating: float
    defensive_rating: float
    special_teams_rating: float
    overall_rating: float
    potential_rating: float
    offense_position_rating: float
    defense_position_rating: float
    special_position_rating: float
    strategy: StrategyProfile = field(default_factory=lambda: StrategyProfile(name="Balanced"))
    lineup_modifier: float = 0.0
    offense_gpm: float = 1.0
    defense_gpm: float = 1.0
    special_gpm: float = 1.0
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

    @staticmethod
    def predefined_strategies() -> dict[str, StrategyProfile]:
        return {
            "Balanced": StrategyProfile(name="Balanced", aggressiveness=0.5, tempo=0.5, defensive_focus=0.5, risk_tolerance=0.5),
            "Air Raid": StrategyProfile(name="Air Raid", aggressiveness=0.75, tempo=0.8, defensive_focus=0.35, risk_tolerance=0.8),
            "Ground Control": StrategyProfile(name="Ground Control", aggressiveness=0.45, tempo=0.35, defensive_focus=0.55, risk_tolerance=0.3),
            "Blitz Pressure": StrategyProfile(name="Blitz Pressure", aggressiveness=0.65, tempo=0.6, defensive_focus=0.8, risk_tolerance=0.65),
            "Ball Control": StrategyProfile(name="Ball Control", aggressiveness=0.35, tempo=0.3, defensive_focus=0.7, risk_tolerance=0.25),
        }

    def build_team_snapshot(
        self,
        team_id: str,
        strategy: StrategyProfile | None = None,
        starters: dict[str, str] | None = None,
        boom_bust_context: BoomBustContext | None = None,
    ) -> TeamSnapshot:
        team: TeamRecord | None = self.repository.get_team(team_id)
        if team is None:
            raise ValueError(f"Unknown team ID: {team_id}")

        players = self.repository.get_players_for_team(team_id)
        if not players:
            raise ValueError(f"No players found for team ID: {team_id}")

        offense_base = self._average_by_positions(players, OFFENSE_POSITIONS)
        defense_base = self._average_by_positions(players, DEFENSE_POSITIONS)
        special_base = self._average_by_positions(players, {"K", "P"})

        offense_position_rating = unit_position_rating(players, OFFENSE_POSITIONS, starters=8)
        defense_position_rating = unit_position_rating(players, DEFENSE_POSITIONS, starters=8)
        special_position_rating = unit_position_rating(players, {"K", "P"}, starters=2)

        lineup_modifier = self._lineup_modifier(players, starters or {})
        boom_bust_effect = BoomBustEngine(self.random).build_team_effect(players, boom_bust_context or BoomBustContext())
        offense = round(((offense_base * 0.55) + (offense_position_rating * 0.45)) + lineup_modifier, 2)
        defense = round(((defense_base * 0.55) + (defense_position_rating * 0.45)) + lineup_modifier, 2)
        special = round(((special_base * 0.7) + (special_position_rating * 0.3)), 2)
        offense = round(max(0.0, min(100.0, offense * boom_bust_effect.offense_gpm)), 2)
        defense = round(max(0.0, min(100.0, defense * boom_bust_effect.defense_gpm)), 2)
        special = round(max(0.0, min(100.0, special * boom_bust_effect.special_gpm)), 2)
        overall = round((offense + defense + special) / 3, 2)
        potential_rating = team_potential_rating(players)

        return TeamSnapshot(
            team_id=team.team_id,
            name=team.name,
            location=team.location,
            offensive_rating=offense,
            defensive_rating=defense,
            special_teams_rating=special,
            overall_rating=overall,
            potential_rating=potential_rating,
            offense_position_rating=offense_position_rating,
            defense_position_rating=defense_position_rating,
            special_position_rating=special_position_rating,
            strategy=strategy or self.predefined_strategies()["Balanced"],
            lineup_modifier=lineup_modifier,
            offense_gpm=boom_bust_effect.offense_gpm,
            defense_gpm=boom_bust_effect.defense_gpm,
            special_gpm=boom_bust_effect.special_gpm,
            players=players,
        )

    def _lineup_modifier(self, players: list[PlayerRecord], starters: dict[str, str]) -> float:
        if not starters:
            return 0.0

        by_id = {player.player_id: player for player in players}
        starter_ratings: list[int] = []
        for player_id in starters.values():
            if player_id in by_id:
                starter_ratings.append(by_id[player_id].overall)

        if not starter_ratings:
            return 0.0

        team_average = sum(player.overall for player in players) / len(players)
        starter_average = sum(starter_ratings) / len(starter_ratings)
        return max(-3.0, min(4.0, round((starter_average - team_average) / 8, 2)))

    @staticmethod
    def _average_by_positions(players: list[PlayerRecord], positions: set[str]) -> float:
        selected = [p.overall for p in players if p.position in positions]
        if not selected:
            return 50.0
        return round(sum(selected) / len(selected), 2)

    def simulate_single_game(
        self,
        home_team_id: str,
        away_team_id: str,
        home_strategy: StrategyProfile | None = None,
        away_strategy: StrategyProfile | None = None,
        home_starters: dict[str, str] | None = None,
        away_starters: dict[str, str] | None = None,
        home_rating_adjustment: float = 0.0,
        away_rating_adjustment: float = 0.0,
        home_boom_bust_context: BoomBustContext | None = None,
        away_boom_bust_context: BoomBustContext | None = None,
    ) -> GameResult:
        home = self.build_team_snapshot(
            home_team_id,
            strategy=home_strategy,
            starters=home_starters,
            boom_bust_context=home_boom_bust_context or BoomBustContext(home=True),
        )
        away = self.build_team_snapshot(
            away_team_id,
            strategy=away_strategy,
            starters=away_starters,
            boom_bust_context=away_boom_bust_context or BoomBustContext(road=True),
        )

        self._apply_rating_adjustment(home, home_rating_adjustment)
        self._apply_rating_adjustment(away, away_rating_adjustment)
        drives_log: list[str] = []

        offense, defense = home, away
        for drive in range(1, 21):
            points = self._simulate_drive(offense, defense)
            offense.score += points
            if points:
                drives_log.append(f"Drive {drive}: {offense.name} scored {points} ({offense.strategy.name})")
            offense, defense = defense, offense

        if home.score == away.score:
            for ot_drive in range(1, 5):
                points = self._simulate_drive(offense, defense)
                offense.score += points
                if points:
                    drives_log.append(f"OT {ot_drive}: {offense.name} scored {points} ({offense.strategy.name})")
                offense, defense = defense, offense
                if home.score != away.score and ot_drive % 2 == 0:
                    break

        return GameResult(home_team=home, away_team=away, drives_log=drives_log)

    @staticmethod
    def _apply_rating_adjustment(team: TeamSnapshot, adjustment: float) -> None:
        if adjustment == 0:
            return
        team.offensive_rating = round(max(40.0, min(99.0, team.offensive_rating + adjustment)), 2)
        team.defensive_rating = round(max(40.0, min(99.0, team.defensive_rating + adjustment)), 2)
        team.overall_rating = round((team.offensive_rating + team.defensive_rating + team.special_teams_rating) / 3, 2)

    def _simulate_drive(self, offense: TeamSnapshot, defense: TeamSnapshot) -> int:
        attack_edge = offense.offensive_rating / max(offense.offensive_rating + defense.defensive_rating, 1)
        special_modifier = (offense.special_teams_rating - 70) / 200
        strategy_push = (offense.strategy.aggressiveness - 0.5) * 0.16
        tempo_push = (offense.strategy.tempo - 0.5) * 0.10
        defense_drag = (defense.strategy.defensive_focus - 0.5) * 0.12
        scoring_chance = max(0.10, min(0.82, attack_edge + special_modifier + strategy_push + tempo_push - defense_drag))

        if self.random.random() > scoring_chance:
            return 0

        risk = offense.strategy.risk_tolerance
        play = self.random.choices(
            ["td", "fg", "empty", "turnover"],
            weights=[0.35 + (risk * 0.25), 0.35 - (risk * 0.1), 0.18, 0.12 + (risk * 0.08)],
            k=1,
        )[0]
        if play == "td":
            pat_good = self.random.random() < offense.special_teams_rating / 100
            return 7 if pat_good else 6
        if play == "fg":
            return 3 if self.random.random() < offense.special_teams_rating / 100 else 0
        if play == "turnover":
            return 0
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

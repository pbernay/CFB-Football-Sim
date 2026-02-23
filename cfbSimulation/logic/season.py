"""Season mode logic for week-by-week play without coach career state."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from cfbSimulation.data.repository import DatabaseRepository
from cfbSimulation.logic.career import ScheduledGame
from cfbSimulation.logic.simulator import GameResult, GameSimulator


@dataclass
class SeasonState:
    team_id: str
    team_name: str
    season: int = 1
    wins: int = 0
    losses: int = 0
    current_week: int = 1
    schedule: list[ScheduledGame] = field(default_factory=list)


class SeasonManager:
    def __init__(
        self,
        repository: DatabaseRepository | None = None,
        simulator: GameSimulator | None = None,
        seed: int | None = None,
    ) -> None:
        self.repository = repository or DatabaseRepository()
        self.simulator = simulator or GameSimulator(repository=self.repository, seed=seed)
        self.random = random.Random(seed)

    def start_season(self, team_id: str, weeks: int = 12, season_number: int = 1) -> SeasonState:
        team = self.repository.get_team(team_id)
        if team is None:
            raise ValueError(f"Unknown team ID: {team_id}")

        schedule = self._generate_schedule(team_id=team_id, weeks=weeks)
        return SeasonState(team_id=team_id, team_name=team.name, season=season_number, schedule=schedule)

    def _generate_schedule(self, team_id: str, weeks: int = 12) -> list[ScheduledGame]:
        team_ids = [tid for tid in self.repository.iter_team_ids() if tid != team_id]
        if not team_ids:
            raise ValueError("No opponent teams found in database.")

        opponents = self.random.sample(team_ids, k=min(weeks, len(team_ids)))
        while len(opponents) < weeks:
            opponents.append(self.random.choice(team_ids))

        schedule: list[ScheduledGame] = []
        for week, opponent_id in enumerate(opponents, start=1):
            opponent = self.repository.get_team(opponent_id)
            schedule.append(
                ScheduledGame(
                    week=week,
                    opponent_team_id=opponent_id,
                    opponent_name=opponent.name if opponent else opponent_id,
                    is_home=(week % 2 == 1),
                )
            )
        return schedule

    @staticmethod
    def get_next_game(state: SeasonState) -> ScheduledGame | None:
        for game in state.schedule:
            if not game.played:
                return game
        return None

    def play_next_game(self, state: SeasonState) -> tuple[SeasonState, GameResult, ScheduledGame]:
        next_game = self.get_next_game(state)
        if next_game is None:
            raise ValueError("Season complete. No remaining games.")

        home_id = state.team_id if next_game.is_home else next_game.opponent_team_id
        away_id = next_game.opponent_team_id if next_game.is_home else state.team_id
        result = self.simulator.simulate_single_game(home_id, away_id)

        if next_game.is_home:
            my_score, opp_score = result.home_team.score, result.away_team.score
        else:
            my_score, opp_score = result.away_team.score, result.home_team.score

        next_game.played = True
        next_game.my_score = my_score
        next_game.opp_score = opp_score
        outcome = "W" if my_score > opp_score else "L"
        next_game.result_summary = f"Week {next_game.week}: {outcome} {my_score}-{opp_score} vs {next_game.opponent_name}"

        if my_score > opp_score:
            state.wins += 1
        else:
            state.losses += 1

        state.current_week = next_game.week + 1
        return state, result, next_game

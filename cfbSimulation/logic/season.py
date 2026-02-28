"""Season mode logic for week-by-week play without coach career state."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum

from cfbSimulation.data.repository import DatabaseRepository
from cfbSimulation.logic.career import ScheduledGame
from cfbSimulation.logic.player_stats import PlayerStatsManager
from cfbSimulation.logic.program_structure import (
    Division,
    PollRanking,
    ProgramStructureEngine,
)
from cfbSimulation.logic.simulator import GameResult, GameSimulator


class SeasonPhase(str, Enum):
    REGULAR = "regular"
    SEMIFINAL = "semifinal"
    CHAMPIONSHIP = "championship"
    COMPLETE = "complete"


@dataclass
class SeasonState:
    team_id: str
    team_name: str
    season: int = 1
    wins: int = 0
    losses: int = 0
    current_week: int = 1
    schedule: list[ScheduledGame] = field(default_factory=list)
    playoff_schedule: list[ScheduledGame] = field(default_factory=list)
    playoff_wins: int = 0
    playoff_losses: int = 0
    phase: SeasonPhase = SeasonPhase.REGULAR
    champion: bool = False
    team_division: str = Division.FBS.value
    ap_poll: list[PollRanking] = field(default_factory=list)
    fcs_poll: list[PollRanking] = field(default_factory=list)


class SeasonManager:
    def __init__(
        self,
        repository: DatabaseRepository | None = None,
        simulator: GameSimulator | None = None,
        stats_manager: PlayerStatsManager | None = None,
        seed: int | None = None,
    ) -> None:
        self.repository = repository or DatabaseRepository()
        self.simulator = simulator or GameSimulator(
            repository=self.repository, seed=seed
        )
        self.stats_manager = stats_manager or PlayerStatsManager(
            repository=self.repository, seed=seed
        )
        self.random = random.Random(seed)
        self.program_engine = ProgramStructureEngine(
            self.repository, self.simulator, seed=seed
        )

    def start_season(
        self, team_id: str, weeks: int = 12, season_number: int = 1
    ) -> SeasonState:
        team = self.repository.get_team(team_id)
        if team is None:
            raise ValueError(f"Unknown team ID: {team_id}")

        schedule = self._generate_schedule(team_id=team_id, weeks=weeks)
        contexts = self.program_engine.build_contexts()
        ap_poll = self.program_engine.preseason_rankings(Division.FBS)
        fcs_poll = self.program_engine.preseason_rankings(Division.FCS)
        division = (
            contexts.get(team_id).division.value
            if team_id in contexts
            else Division.FBS.value
        )
        return SeasonState(
            team_id=team_id,
            team_name=team.name,
            season=season_number,
            schedule=schedule,
            team_division=division,
            ap_poll=ap_poll,
            fcs_poll=fcs_poll,
        )

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
        if state.phase == SeasonPhase.REGULAR:
            for game in state.schedule:
                if not game.played:
                    return game
            return None

        if state.phase in (SeasonPhase.SEMIFINAL, SeasonPhase.CHAMPIONSHIP):
            for game in state.playoff_schedule:
                if not game.played:
                    return game
        return None

    def play_next_game(
        self, state: SeasonState
    ) -> tuple[SeasonState, GameResult, ScheduledGame]:
        next_game = self.get_next_game(state)
        if next_game is None:
            if state.phase == SeasonPhase.REGULAR:
                self._begin_playoffs(state)
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

        self.stats_manager.record_game(result.home_team, result.away_team)
        self.program_engine.record_game(
            home_id,
            away_id,
            result.home_team.score,
            result.away_team.score,
            state.current_week,
        )
        state.ap_poll = self.program_engine.weekly_rankings(Division.FBS)
        state.fcs_poll = self.program_engine.weekly_rankings(Division.FCS)

        next_game.played = True
        next_game.my_score = my_score
        next_game.opp_score = opp_score
        outcome = "W" if my_score > opp_score else "L"
        next_game.result_summary = f"Week {next_game.week}: {outcome} {my_score}-{opp_score} vs {next_game.opponent_name}"

        if state.phase == SeasonPhase.REGULAR:
            if my_score > opp_score:
                state.wins += 1
            else:
                state.losses += 1
            state.current_week = next_game.week + 1
            if self.get_next_game(state) is None:
                self._begin_playoffs(state)
            return state, result, next_game

        if my_score > opp_score:
            state.playoff_wins += 1
            if state.phase == SeasonPhase.SEMIFINAL:
                self._setup_championship(state)
            else:
                state.phase = SeasonPhase.COMPLETE
                state.champion = True
        else:
            state.playoff_losses += 1
            state.phase = SeasonPhase.COMPLETE
            state.champion = False

        return state, result, next_game

    def _begin_playoffs(self, state: SeasonState) -> None:
        state.phase = SeasonPhase.SEMIFINAL
        opponent_id = self._pick_playoff_opponent(state.team_id, excluded=set())
        opponent = self.repository.get_team(opponent_id)
        state.playoff_schedule = [
            ScheduledGame(
                week=len(state.schedule) + 1,
                opponent_team_id=opponent_id,
                opponent_name=(opponent.name if opponent else opponent_id),
                is_home=False,
            )
        ]

    def _setup_championship(self, state: SeasonState) -> None:
        state.phase = SeasonPhase.CHAMPIONSHIP
        excluded = {game.opponent_team_id for game in state.playoff_schedule}
        opponent_id = self._pick_playoff_opponent(state.team_id, excluded=excluded)
        opponent = self.repository.get_team(opponent_id)
        state.playoff_schedule.append(
            ScheduledGame(
                week=len(state.schedule) + 2,
                opponent_team_id=opponent_id,
                opponent_name=(opponent.name if opponent else opponent_id),
                is_home=False,
            )
        )

    def _pick_playoff_opponent(self, team_id: str, excluded: set[str]) -> str:
        candidates = [
            tid
            for tid in self.repository.iter_team_ids()
            if tid != team_id and tid not in excluded
        ]
        if not candidates:
            raise ValueError("No eligible playoff opponents found.")
        return self.random.choice(candidates)

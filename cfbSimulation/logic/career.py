"""Career mode management for coach creation and week-by-week play."""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path

from cfbSimulation.data.repository import DatabaseRepository, TeamRecord
from cfbSimulation.logic.simulator import GameResult, GameSimulator


DEFAULT_SAVE_PATH = Path(__file__).resolve().parents[2] / "datafiles" / "saveData" / "career_save.json"


@dataclass
class ScheduledGame:
    week: int
    opponent_team_id: str
    opponent_name: str
    is_home: bool
    played: bool = False
    result_summary: str = ""
    my_score: int = 0
    opp_score: int = 0


@dataclass
class CoachCareer:
    coach_name: str
    coach_style: str
    team_id: str
    team_name: str
    wins: int = 0
    losses: int = 0
    current_week: int = 1
    season: int = 1
    schedule: list[ScheduledGame] = field(default_factory=list)


class CareerManager:
    def __init__(
        self,
        repository: DatabaseRepository | None = None,
        simulator: GameSimulator | None = None,
        save_path: Path | str = DEFAULT_SAVE_PATH,
        seed: int | None = None,
    ) -> None:
        self.repository = repository or DatabaseRepository()
        self.simulator = simulator or GameSimulator(repository=self.repository, seed=seed)
        self.save_path = Path(save_path)
        self.random = random.Random(seed)

    def create_new_career(self, coach_name: str, coach_style: str, team_id: str, weeks: int = 12) -> CoachCareer:
        if not coach_name.strip():
            raise ValueError("Coach name cannot be empty.")

        team: TeamRecord | None = self.repository.get_team(team_id)
        if team is None:
            raise ValueError(f"Unknown team ID: {team_id}")

        schedule = self._generate_schedule(team_id=team_id, weeks=weeks)
        career = CoachCareer(
            coach_name=coach_name.strip(),
            coach_style=coach_style.strip() or "Balanced",
            team_id=team.team_id,
            team_name=team.name,
            schedule=schedule,
        )
        self.save(career)
        return career

    def _generate_schedule(self, team_id: str, weeks: int = 12) -> list[ScheduledGame]:
        team_ids = [tid for tid in self.repository.iter_team_ids() if tid != team_id]
        if not team_ids:
            raise ValueError("No opponent teams found in database.")

        sample_size = min(weeks, len(team_ids))
        opponents = self.random.sample(team_ids, k=sample_size)
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

    def play_next_game(self, career: CoachCareer) -> tuple[CoachCareer, GameResult, ScheduledGame]:
        next_game = self.get_next_game(career)
        if next_game is None:
            raise ValueError("Season complete. No remaining games.")

        home_id = career.team_id if next_game.is_home else next_game.opponent_team_id
        away_id = next_game.opponent_team_id if next_game.is_home else career.team_id
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
            career.wins += 1
        else:
            career.losses += 1

        career.current_week = next_game.week + 1
        self.save(career)
        return career, result, next_game

    @staticmethod
    def get_next_game(career: CoachCareer) -> ScheduledGame | None:
        for game in career.schedule:
            if not game.played:
                return game
        return None

    def reset_for_new_season(self, career: CoachCareer, weeks: int = 12) -> CoachCareer:
        career.schedule = self._generate_schedule(career.team_id, weeks=weeks)
        career.current_week = 1
        career.season += 1
        career.wins = 0
        career.losses = 0
        self.save(career)
        return career

    def save(self, career: CoachCareer) -> None:
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        serializable = asdict(career)
        with self.save_path.open("w", encoding="utf-8") as save_file:
            json.dump(serializable, save_file, indent=2)

    def load(self) -> CoachCareer | None:
        if not self.save_path.exists():
            return None

        with self.save_path.open("r", encoding="utf-8") as save_file:
            data = json.load(save_file)

        schedule = [ScheduledGame(**game) for game in data.get("schedule", [])]
        return CoachCareer(
            coach_name=data["coach_name"],
            coach_style=data.get("coach_style", "Balanced"),
            team_id=data["team_id"],
            team_name=data["team_name"],
            wins=data.get("wins", 0),
            losses=data.get("losses", 0),
            current_week=data.get("current_week", 1),
            season=data.get("season", 1),
            schedule=schedule,
        )

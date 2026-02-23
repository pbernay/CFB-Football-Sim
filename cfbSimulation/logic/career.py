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
    coach_level: int = 1
    prestige: int = 0
    morale: int = 50
    offense_modifier: int = 0
    defense_modifier: int = 0
    schedule: list[ScheduledGame] = field(default_factory=list)
    decision_history: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DecisionOption:
    key: str
    label: str
    morale_delta: int = 0
    offense_delta: int = 0
    defense_delta: int = 0
    prestige_delta: int = 0


@dataclass(frozen=True)
class DecisionScenario:
    key: str
    title: str
    description: str
    options: tuple[DecisionOption, ...]


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
        self._decision_scenarios = self._build_decision_scenarios()

    @staticmethod
    def _build_decision_scenarios() -> tuple[DecisionScenario, ...]:
        return (
            DecisionScenario(
                key="practice_focus",
                title="Weekly Practice Focus",
                description="Staff asks where to spend most reps this week.",
                options=(
                    DecisionOption("film_room", "Film Room (Defense Focus)", defense_delta=2, morale_delta=-1),
                    DecisionOption("tempo", "Tempo Offense Drills", offense_delta=2, morale_delta=1),
                    DecisionOption("recovery", "Recovery + Fundamentals", morale_delta=3, prestige_delta=1),
                ),
            ),
            DecisionScenario(
                key="discipline",
                title="Locker Room Discipline",
                description="A star player missed curfew before game week.",
                options=(
                    DecisionOption("suspend", "Suspend for a half", defense_delta=1, prestige_delta=2, morale_delta=-2),
                    DecisionOption("warning", "Private warning", morale_delta=1, prestige_delta=0),
                    DecisionOption("team_vote", "Let captains decide", morale_delta=2, prestige_delta=1),
                ),
            ),
            DecisionScenario(
                key="recruiting",
                title="Recruiting Weekend",
                description="A key recruit can visit during a game week.",
                options=(
                    DecisionOption("host", "Host full visit", prestige_delta=3, morale_delta=-1),
                    DecisionOption("assistant", "Delegate to assistants", prestige_delta=1, offense_delta=1),
                    DecisionOption("postpone", "Postpone until offseason", morale_delta=1),
                ),
            ),
        )

    def list_decision_scenarios(self) -> tuple[DecisionScenario, ...]:
        return self._decision_scenarios


    def get_weekly_scenario(self, career: CoachCareer) -> DecisionScenario:
        scenarios = self.list_decision_scenarios()
        return scenarios[(career.current_week - 1) % len(scenarios)]

    def apply_decision(self, career: CoachCareer, scenario_key: str, option_key: str) -> CoachCareer:
        scenario = next((item for item in self._decision_scenarios if item.key == scenario_key), None)
        if scenario is None:
            raise ValueError(f"Unknown decision scenario: {scenario_key}")

        option = next((item for item in scenario.options if item.key == option_key), None)
        if option is None:
            raise ValueError(f"Unknown decision option '{option_key}' for scenario '{scenario_key}'")

        career.morale = max(0, min(100, career.morale + option.morale_delta))
        career.offense_modifier = max(-5, min(10, career.offense_modifier + option.offense_delta))
        career.defense_modifier = max(-5, min(10, career.defense_modifier + option.defense_delta))
        career.prestige = max(0, career.prestige + option.prestige_delta)
        if career.prestige >= career.coach_level * 10:
            career.coach_level += 1

        career.decision_history.append(f"S{career.season}W{career.current_week}: {scenario.title} -> {option.label}")
        self.save(career)
        return career

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

        score_swing = self._decision_score_swing(career)
        my_score = max(0, my_score + score_swing)

        next_game.played = True
        next_game.my_score = my_score
        next_game.opp_score = opp_score
        outcome = "W" if my_score > opp_score else "L"
        next_game.result_summary = f"Week {next_game.week}: {outcome} {my_score}-{opp_score} vs {next_game.opponent_name}"

        if my_score > opp_score:
            career.wins += 1
            career.prestige += 2
        else:
            career.losses += 1
            career.prestige = max(0, career.prestige - 1)

        if career.prestige >= career.coach_level * 10:
            career.coach_level += 1

        career.offense_modifier = int(career.offense_modifier * 0.75)
        career.defense_modifier = int(career.defense_modifier * 0.75)
        career.morale = max(20, min(100, career.morale + (1 if outcome == "W" else -1)))

        career.current_week = next_game.week + 1
        self.save(career)
        return career, result, next_game

    def _decision_score_swing(self, career: CoachCareer) -> int:
        morale_bonus = (career.morale - 50) // 15
        style_bonus = 0
        style = career.coach_style.lower()
        if "run" in style:
            style_bonus += 1
        if "defens" in style:
            style_bonus += 1
        coach_bonus = career.coach_level // 2
        total = morale_bonus + career.offense_modifier + career.defense_modifier + style_bonus + coach_bonus
        return max(-7, min(10, total))

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
            coach_level=data.get("coach_level", 1),
            prestige=data.get("prestige", 0),
            morale=data.get("morale", 50),
            offense_modifier=data.get("offense_modifier", 0),
            defense_modifier=data.get("defense_modifier", 0),
            schedule=schedule,
            decision_history=data.get("decision_history", []),
        )

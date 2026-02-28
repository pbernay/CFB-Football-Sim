"""Career mode management for coach creation and week-by-week play."""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path

from cfbSimulation.data.repository import DatabaseRepository, TeamRecord
from cfbSimulation.logic.player_stats import PlayerStatsManager
from cfbSimulation.logic.program_structure import Division, ProgramStructureEngine
from cfbSimulation.logic.roster_dynamics import RosterDynamicsManager
from cfbSimulation.logic.simulator import GameResult, GameSimulator, StrategyProfile


DEFAULT_SAVE_PATH = (
    Path(__file__).resolve().parents[2] / "datafiles" / "saveData" / "career_save.json"
)


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
    recruiting_modifier: int = 0
    player_development_bonus: int = 0
    schedule: list[ScheduledGame] = field(default_factory=list)
    decision_history: list[str] = field(default_factory=list)
    strategy_plan: dict[int, str] = field(default_factory=dict)
    starter_plan: dict[int, dict[str, str]] = field(default_factory=dict)
    ai_difficulty: str = "Normal"
    ai_adaptation: dict[str, int] = field(default_factory=dict)
    scouting_points: int = 100
    recruiting_budget: int = 1800
    recruiting_budget_remaining: int = 1800
    last_season_wins: int = 0
    last_season_losses: int = 0
    scouting_reports: list[dict[str, str | int]] = field(default_factory=list)
    recruiting_board: dict[str, dict[str, str | int]] = field(default_factory=dict)
    signed_recruits: list[dict[str, str | int]] = field(default_factory=list)
    roster: list[dict[str, str | int]] = field(default_factory=list)
    weekly_progress_notes: list[str] = field(default_factory=list)
    offseason_summary: list[str] = field(default_factory=list)
    coaching_staff: dict[str, dict[str, str | int]] = field(default_factory=dict)
    staff_hiring_pool: list[dict[str, str | int]] = field(default_factory=list)


@dataclass(frozen=True)
class DecisionOption:
    key: str
    label: str
    morale_delta: int = 0
    offense_delta: int = 0
    defense_delta: int = 0
    prestige_delta: int = 0
    recruiting_delta: int = 0
    development_delta: int = 0
    potential_delta: int = 0


@dataclass(frozen=True)
class DecisionScenario:
    key: str
    title: str
    description: str
    options: tuple[DecisionOption, ...]


class CareerManager:
    STAFF_ROLES: tuple[str, ...] = (
        "Head Coach",
        "Offensive Coordinator",
        "Defensive Coordinator",
        "Special Teams Coordinator",
        "QB Coach",
        "RB Coach",
        "OL Coach",
        "WR Coach",
        "TE Coach",
        "LB Coach",
        "DL Coach",
        "DB Coach",
        "ST Coach",
        "Head Scout",
    )

    def __init__(
        self,
        repository: DatabaseRepository | None = None,
        simulator: GameSimulator | None = None,
        stats_manager: PlayerStatsManager | None = None,
        save_path: Path | str = DEFAULT_SAVE_PATH,
        seed: int | None = None,
    ) -> None:
        self.repository = repository or DatabaseRepository()
        self.simulator = simulator or GameSimulator(
            repository=self.repository, seed=seed
        )
        self.save_path = Path(save_path)
        self.stats_manager = stats_manager or PlayerStatsManager(
            repository=self.repository, seed=seed
        )
        self.random = random.Random(seed)
        self.roster_manager = RosterDynamicsManager(seed=seed)
        self.program_engine = ProgramStructureEngine(
            self.repository, self.simulator, seed=seed
        )
        self._decision_scenarios = self._build_decision_scenarios()

    def _build_default_staff(self, coach_name: str) -> dict[str, dict[str, str | int]]:
        staff: dict[str, dict[str, str | int]] = {
            "Head Coach": {
                "staff_id": "staff-hc-user",
                "name": coach_name,
                "role": "Head Coach",
                "overall": 70,
                "potential": 85,
            }
        }
        for role in self.STAFF_ROLES:
            if role == "Head Coach":
                continue
            staff[role] = self._generate_staff_candidate(role)
        return staff

    def _generate_staff_candidate(self, role: str) -> dict[str, str | int]:
        first = self.random.choice(
            (
                "Avery",
                "Jordan",
                "Taylor",
                "Parker",
                "Drew",
                "Devon",
                "Reese",
                "Quinn",
                "Riley",
                "Blake",
            )
        )
        last = self.random.choice(
            (
                "Hayes",
                "Manning",
                "Franklin",
                "Waller",
                "Dixon",
                "Brock",
                "Hughes",
                "Holland",
                "Reed",
                "Nolan",
            )
        )
        return {
            "staff_id": f"staff-{self.random.randint(10000, 99999)}",
            "name": f"{first} {last}",
            "role": role,
            "overall": self.random.randint(52, 86),
            "potential": self.random.randint(65, 95),
            "specialty": self.random.choice(
                ("QB", "RB", "WR", "TE", "OL", "DL", "LB", "DB", "ST")
            )
            if role == "Head Scout"
            else "",
        }

    def _staff_overall(self, career: CoachCareer, role: str, default: int = 60) -> int:
        return int(career.coaching_staff.get(role, {}).get("overall", default))

    @staticmethod
    def _build_decision_scenarios() -> tuple[DecisionScenario, ...]:
        return (
            DecisionScenario(
                key="practice_focus",
                title="Weekly Practice Focus",
                description="Staff asks where to spend most reps this week.",
                options=(
                    DecisionOption(
                        "film_room",
                        "Film Room (Defense Focus)",
                        defense_delta=2,
                        morale_delta=-1,
                    ),
                    DecisionOption(
                        "tempo", "Tempo Offense Drills", offense_delta=2, morale_delta=1
                    ),
                    DecisionOption(
                        "recovery",
                        "Recovery + Fundamentals",
                        morale_delta=3,
                        prestige_delta=1,
                        development_delta=1,
                    ),
                ),
            ),
            DecisionScenario(
                key="discipline",
                title="Locker Room Discipline",
                description="A star player missed curfew before game week.",
                options=(
                    DecisionOption(
                        "suspend",
                        "Suspend for a half",
                        defense_delta=1,
                        prestige_delta=2,
                        morale_delta=-2,
                    ),
                    DecisionOption(
                        "warning", "Private warning", morale_delta=1, prestige_delta=0
                    ),
                    DecisionOption(
                        "team_vote",
                        "Let captains decide",
                        morale_delta=2,
                        prestige_delta=1,
                        development_delta=1,
                    ),
                ),
            ),
            DecisionScenario(
                key="recruiting",
                title="Recruiting Weekend",
                description="A key recruit can visit during a game week.",
                options=(
                    DecisionOption(
                        "host",
                        "Host full visit",
                        prestige_delta=3,
                        morale_delta=-1,
                        recruiting_delta=3,
                    ),
                    DecisionOption(
                        "assistant",
                        "Delegate to assistants",
                        prestige_delta=1,
                        offense_delta=1,
                        recruiting_delta=2,
                    ),
                    DecisionOption(
                        "postpone", "Postpone until offseason", morale_delta=1
                    ),
                ),
            ),
            DecisionScenario(
                key="player_support",
                title="Player Development Opportunity",
                description="Alumni offer to sponsor extra skill coaching for veterans or freshmen.",
                options=(
                    DecisionOption(
                        "veterans",
                        "Focus on current starters",
                        development_delta=2,
                        morale_delta=1,
                    ),
                    DecisionOption(
                        "young_core",
                        "Invest in youth pipeline",
                        potential_delta=2,
                        recruiting_delta=1,
                    ),
                    DecisionOption(
                        "split",
                        "Split resources",
                        development_delta=1,
                        potential_delta=1,
                    ),
                ),
            ),
        )

    def list_decision_scenarios(self) -> tuple[DecisionScenario, ...]:
        return self._decision_scenarios

    @staticmethod
    def ai_difficulty_profiles() -> dict[str, dict[str, float]]:
        return {
            "Easy": {"rating_bonus": -4.0, "adaptation_rate": 0.65},
            "Normal": {"rating_bonus": 0.0, "adaptation_rate": 1.0},
            "Hard": {"rating_bonus": 3.0, "adaptation_rate": 1.35},
            "Heisman": {"rating_bonus": 6.0, "adaptation_rate": 1.65},
        }

    def get_weekly_scenario(self, career: CoachCareer) -> DecisionScenario:
        scenarios = self.list_decision_scenarios()
        return scenarios[(career.current_week - 1) % len(scenarios)]

    def should_trigger_random_decision(self, career: CoachCareer) -> bool:
        if self.get_next_game(career) is None:
            return False
        weekly_chance = 0.34 if career.current_week > 1 else 0.0
        morale_impact = (50 - career.morale) / 250.0
        return self.random.random() < max(
            0.18, min(0.55, weekly_chance + morale_impact)
        )

    def apply_decision(
        self, career: CoachCareer, scenario_key: str, option_key: str
    ) -> CoachCareer:
        scenario = next(
            (item for item in self._decision_scenarios if item.key == scenario_key),
            None,
        )
        if scenario is None:
            raise ValueError(f"Unknown decision scenario: {scenario_key}")

        option = next(
            (item for item in scenario.options if item.key == option_key), None
        )
        if option is None:
            raise ValueError(
                f"Unknown decision option '{option_key}' for scenario '{scenario_key}'"
            )

        career.morale = max(0, min(100, career.morale + option.morale_delta))
        career.offense_modifier = max(
            -5, min(10, career.offense_modifier + option.offense_delta)
        )
        career.defense_modifier = max(
            -5, min(10, career.defense_modifier + option.defense_delta)
        )
        career.recruiting_modifier = max(
            -4, min(8, career.recruiting_modifier + option.recruiting_delta)
        )
        career.player_development_bonus = max(
            0, min(6, career.player_development_bonus + option.development_delta)
        )
        career.prestige = max(0, career.prestige + option.prestige_delta)
        self._apply_potential_boost(career, option.potential_delta)
        if career.prestige >= career.coach_level * 10:
            career.coach_level += 1

        career.decision_history.append(
            f"S{career.season}W{career.current_week}: {scenario.title} -> {option.label}"
        )
        self.save(career)
        return career

    def _apply_potential_boost(self, career: CoachCareer, potential_delta: int) -> None:
        if potential_delta <= 0 or not career.roster:
            return
        boost_count = min(5, len(career.roster))
        for player in self.random.sample(career.roster, k=boost_count):
            current = int(player.get("potential", player.get("overall", 60)))
            player["potential"] = min(99, current + potential_delta)

    def create_new_career(
        self,
        coach_name: str,
        coach_style: str,
        team_id: str,
        weeks: int = 12,
        ai_difficulty: str = "Normal",
    ) -> CoachCareer:
        if not coach_name.strip():
            raise ValueError("Coach name cannot be empty.")

        team: TeamRecord | None = self.repository.get_team(team_id)
        if ai_difficulty not in self.ai_difficulty_profiles():
            raise ValueError(f"Unknown AI difficulty: {ai_difficulty}")
        if team is None:
            raise ValueError(f"Unknown team ID: {team_id}")

        schedule = self._generate_schedule(team_id=team_id, weeks=weeks)
        roster = self._build_initial_roster(team.team_id)
        career = CoachCareer(
            coach_name=coach_name.strip(),
            coach_style=coach_style.strip() or "Balanced",
            team_id=team.team_id,
            team_name=team.name,
            schedule=schedule,
            ai_difficulty=ai_difficulty,
            roster=roster,
            coaching_staff=self._build_default_staff(coach_name.strip()),
        )
        career.staff_hiring_pool = self.generate_staff_hiring_pool(career)
        self.save(career)
        return career

    def _build_initial_roster(self, team_id: str) -> list[dict[str, str | int]]:
        players = self.repository.get_players_for_team(team_id)
        return [
            {
                "player_id": p.player_id,
                "first_name": p.first_name,
                "last_name": p.last_name,
                "position": p.position,
                "overall": p.overall,
                "potential": p.potential,
                "age": p.age,
                "year": p.year,
                "player_status": p.player_status,
            }
            for p in players
        ]

    @staticmethod
    def calculate_recruiting_budget(last_wins: int, last_losses: int) -> int:
        weighted_total = 1800 + (last_wins * 180) - (last_losses * 60)
        return max(1200, min(5000, weighted_total))

    @staticmethod
    def recruiting_progress_from_score(score: float) -> int:
        return max(0, min(100, int(round((score / 16.0) * 100))))

    def generate_staff_hiring_pool(
        self, career: CoachCareer, candidates_per_role: int = 2
    ) -> list[dict[str, str | int]]:
        pool: list[dict[str, str | int]] = []
        for role in self.STAFF_ROLES:
            if role == "Head Coach":
                continue
            for _ in range(candidates_per_role):
                candidate = self._generate_staff_candidate(role)
                candidate["available_for"] = role
                pool.append(candidate)
        return pool

    def promote_staff_member(
        self, career: CoachCareer, from_role: str, to_role: str
    ) -> CoachCareer:
        if from_role == "Head Scout" or to_role == "Head Scout":
            raise ValueError("Head Scout cannot be promoted or reassigned.")
        if from_role == "Head Coach" or to_role == "Head Coach":
            raise ValueError("Head Coach role is reserved for the user profile.")
        if (
            from_role not in career.coaching_staff
            or to_role not in career.coaching_staff
        ):
            raise ValueError("Invalid staff roles for promotion.")
        career.coaching_staff[from_role], career.coaching_staff[to_role] = (
            career.coaching_staff[to_role],
            career.coaching_staff[from_role],
        )
        career.coaching_staff[from_role]["role"] = from_role
        career.coaching_staff[to_role]["role"] = to_role
        self.save(career)
        return career

    def hire_staff_candidate(
        self, career: CoachCareer, staff_id: str, role: str
    ) -> CoachCareer:
        if role == "Head Coach":
            raise ValueError("Head Coach cannot be replaced.")
        candidate = next(
            (c for c in career.staff_hiring_pool if str(c.get("staff_id")) == staff_id),
            None,
        )
        if candidate is None:
            raise ValueError("Staff candidate not found in hiring pool.")
        if str(candidate.get("available_for")) != role:
            raise ValueError(f"Candidate is not available for {role}.")
        payload = dict(candidate)
        payload["role"] = role
        payload.pop("available_for", None)
        career.coaching_staff[role] = payload
        career.staff_hiring_pool = [
            c for c in career.staff_hiring_pool if str(c.get("staff_id")) != staff_id
        ]
        self.save(career)
        return career

    def scout_accuracy(self, career: CoachCareer, true_potential: int) -> int:
        scout_ovr = self._staff_overall(career, "Head Scout", default=58)
        error_band = max(1, 16 - scout_ovr // 6)
        return max(
            55, min(99, true_potential + self.random.randint(-error_band, error_band))
        )

    def scouting_points_regen(self, career: CoachCareer) -> int:
        scout_ovr = self._staff_overall(career, "Head Scout", default=58)
        return max(12, min(42, 8 + scout_ovr // 3))

    def invest_in_scouting(self, career: CoachCareer, investment: int) -> CoachCareer:
        spend = max(0, min(career.scouting_points, investment))
        if spend <= 0:
            raise ValueError("Not enough scouting points to invest.")
        known_ids = set(career.recruiting_board)
        reports = self.roster_manager.generate_scouting_reports(spend, known_ids)
        career.scouting_points -= spend
        career.scouting_reports = reports
        for recruit in reports:
            recruit_payload = dict(recruit)
            true_potential = int(
                recruit_payload.get("overall", 60)
            ) + self.random.randint(5, 16)
            recruit_payload["potential"] = max(60, min(99, true_potential))
            recruit_payload["scouted_potential"] = self.scout_accuracy(
                career, recruit_payload["potential"]
            )
            career.recruiting_board[str(recruit["recruit_id"])] = recruit_payload
        self.save(career)
        return career

    def offer_recruit(
        self, career: CoachCareer, recruit_id: str, salary_offer: int
    ) -> tuple[CoachCareer, bool, str]:
        recruit = career.recruiting_board.get(recruit_id)
        if recruit is None:
            raise ValueError("Recruit not found on your board.")
        if salary_offer > career.recruiting_budget_remaining:
            raise ValueError(
                f"Offer exceeds remaining recruiting budget ({career.recruiting_budget_remaining})."
            )
        contexts = self.program_engine.build_contexts()
        context = contexts.get(career.team_id)
        division_bonus = (
            1.0 if context is None or context.division == Division.FBS else 0.75
        )
        tier_mult = context.profile.recruiting_interest_multiplier if context else 1.0
        reputation = min(
            95.0,
            (
                50.0
                + career.prestige * 1.5
                + career.wins * 0.9
                + career.recruiting_modifier * 1.75
            )
            * division_bonus
            * tier_mult,
        )
        role_score = (
            6.0
            if str(recruit.get("position")) in {"QB", "RB", "WR", "CB", "LB"}
            else 3.0
        )
        result = self.roster_manager.evaluate_offer(
            recruit, salary_offer, reputation, role_score
        )
        progress = self.recruiting_progress_from_score(result.score)
        recruit["last_offer"] = salary_offer
        recruit["last_offer_score"] = result.score
        recruit["last_offer_progress"] = progress
        recruit["target_score"] = 16.0
        career.recruiting_budget_remaining = max(
            0, career.recruiting_budget_remaining - salary_offer
        )
        if result.accepted:
            recruit["player_id"] = recruit["recruit_id"]
            recruit["first_name"], recruit["last_name"] = str(recruit["name"]).split(
                " ", 1
            )
            recruit["year"] = "Freshman"
            recruit["player_status"] = "Current"
            recruit["age"] = 18
            career.signed_recruits.append(dict(recruit))
            career.recruiting_board.pop(recruit_id, None)
        self.save(career)
        gap = round(16.0 - result.score, 2)
        msg = (
            f"{result.reason} (score {result.score}, progress {progress}%, gap {gap:+})"
        )
        return career, result.accepted, msg

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

    def play_next_game(
        self, career: CoachCareer
    ) -> tuple[CoachCareer, GameResult, ScheduledGame]:
        next_game = self.get_next_game(career)
        if next_game is None:
            raise ValueError("Season complete. No remaining games.")

        home_id = career.team_id if next_game.is_home else next_game.opponent_team_id
        away_id = next_game.opponent_team_id if next_game.is_home else career.team_id
        strategy_name = career.strategy_plan.get(next_game.week, "Balanced")
        strategy_map = self.simulator.predefined_strategies()
        my_strategy = strategy_map.get(strategy_name, strategy_map["Balanced"])
        opponent_strategy = self._counter_strategy(my_strategy, career)
        difficulty = self.ai_difficulty_profiles().get(
            career.ai_difficulty, self.ai_difficulty_profiles()["Normal"]
        )
        opp_rating_bonus = difficulty["rating_bonus"]

        if next_game.week not in career.starter_plan:
            career.starter_plan[next_game.week] = self.auto_set_best_starters(career)
        my_starters = career.starter_plan.get(next_game.week, {})
        result = self.simulator.simulate_single_game(
            home_id,
            away_id,
            home_strategy=my_strategy if next_game.is_home else opponent_strategy,
            away_strategy=opponent_strategy if next_game.is_home else my_strategy,
            home_starters=my_starters if next_game.is_home else None,
            away_starters=my_starters if not next_game.is_home else None,
            home_rating_adjustment=0.0 if next_game.is_home else opp_rating_bonus,
            away_rating_adjustment=opp_rating_bonus if next_game.is_home else 0.0,
        )

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

        team_success = (career.wins - career.losses) / max(1, next_game.week)
        development_bonus = self.position_coach_development_bonus(career)
        progress_updates = self.roster_manager.weekly_progression(
            career.roster, team_success + development_bonus
        )
        if career.player_development_bonus > 0:
            for _ in range(career.player_development_bonus):
                progress_updates.extend(
                    self.roster_manager.weekly_progression(
                        career.roster, team_success + development_bonus + 0.08
                    )
                )
            career.player_development_bonus = max(
                0, career.player_development_bonus - 1
            )
        self.apply_position_coach_performance_boost(career)
        if progress_updates:
            career.weekly_progress_notes = progress_updates[-10:]

        career.scouting_points = min(
            220, career.scouting_points + self.scouting_points_regen(career)
        )
        career.current_week = next_game.week + 1
        self._update_ai_memory(career, my_strategy)
        self.stats_manager.record_game(result.home_team, result.away_team)
        self.save(career)
        return career, result, next_game

    def auto_set_best_starters(self, career: CoachCareer) -> dict[str, str]:
        required_positions = (
            "QB",
            "RB",
            "WR",
            "TE",
            "OT",
            "OG",
            "C",
            "DE",
            "DT",
            "LB",
            "CB",
            "S",
            "K",
            "P",
        )
        starters: dict[str, str] = {}
        roster = career.roster or self._build_initial_roster(career.team_id)
        oc_rating = self._staff_overall(career, "Offensive Coordinator", default=60)
        dc_rating = self._staff_overall(career, "Defensive Coordinator", default=60)
        stc_rating = self._staff_overall(
            career, "Special Teams Coordinator", default=60
        )
        for position in required_positions:
            candidates = [p for p in roster if str(p.get("position", "")) == position]
            if not candidates:
                continue
            if position in {"QB", "RB", "WR", "TE", "OT", "OG", "C"}:
                competency = oc_rating
            elif position in {"K", "P"}:
                competency = stc_rating
            else:
                competency = dc_rating
            slip = max(0, (70 - competency) // 7)
            ranked = sorted(
                candidates, key=lambda p: int(p.get("overall", 0)), reverse=True
            )
            pick_index = min(len(ranked) - 1, slip)
            pick = ranked[pick_index]
            starters[position] = str(pick.get("player_id", pick.get("recruit_id", "")))
        return starters

    def position_coach_development_bonus(self, career: CoachCareer) -> float:
        coach_roles = (
            "QB Coach",
            "RB Coach",
            "OL Coach",
            "WR Coach",
            "TE Coach",
            "LB Coach",
            "DL Coach",
            "DB Coach",
            "ST Coach",
        )
        avg = sum(
            self._staff_overall(career, role, default=60) for role in coach_roles
        ) / len(coach_roles)
        return (avg - 60.0) / 220.0

    def apply_position_coach_performance_boost(self, career: CoachCareer) -> None:
        role_for_position = {
            "QB": "QB Coach",
            "RB": "RB Coach",
            "WR": "WR Coach",
            "TE": "TE Coach",
            "OT": "OL Coach",
            "OG": "OL Coach",
            "C": "OL Coach",
            "LB": "LB Coach",
            "DE": "DL Coach",
            "DT": "DL Coach",
            "CB": "DB Coach",
            "S": "DB Coach",
            "K": "ST Coach",
            "P": "ST Coach",
        }
        for player in career.roster:
            role = role_for_position.get(str(player.get("position", "")))
            if role is None:
                continue
            coach_ovr = self._staff_overall(career, role, default=60)
            if coach_ovr >= 82 and self.random.random() < 0.20:
                player["overall"] = min(99, int(player.get("overall", 60)) + 1)
            elif coach_ovr <= 55 and self.random.random() < 0.08:
                player["overall"] = max(45, int(player.get("overall", 60)) - 1)

    def _counter_strategy(
        self, strategy: StrategyProfile, career: CoachCareer
    ) -> StrategyProfile:
        adaptation = career.ai_adaptation.get(strategy.name, 0)
        difficulty = self.ai_difficulty_profiles().get(
            career.ai_difficulty, self.ai_difficulty_profiles()["Normal"]
        )
        adaptation_factor = min(0.22, adaptation * 0.02 * difficulty["adaptation_rate"])
        return StrategyProfile(
            name=f"Counter {strategy.name} ({career.ai_difficulty})",
            aggressiveness=max(
                0.2, min(0.9, 1 - strategy.aggressiveness + adaptation_factor)
            ),
            tempo=max(0.2, min(0.9, 1 - strategy.tempo + adaptation_factor)),
            defensive_focus=max(
                0.3, min(0.95, strategy.aggressiveness + 0.2 + adaptation_factor)
            ),
            risk_tolerance=max(
                0.2, min(0.85, strategy.risk_tolerance + adaptation_factor / 2)
            ),
        )

    def _update_ai_memory(
        self, career: CoachCareer, user_strategy: StrategyProfile
    ) -> None:
        history = dict(career.ai_adaptation)
        history[user_strategy.name] = history.get(user_strategy.name, 0) + 1
        for key in list(history):
            if key != user_strategy.name:
                history[key] = max(0, history[key] - 1)
                if history[key] == 0:
                    history.pop(key)
        career.ai_adaptation = history

    def set_week_strategy(
        self, career: CoachCareer, week: int, strategy_name: str
    ) -> CoachCareer:
        if week < career.current_week or week > len(career.schedule):
            raise ValueError("Strategy week is out of range for remaining schedule.")
        if strategy_name not in self.simulator.predefined_strategies():
            raise ValueError(f"Unknown strategy: {strategy_name}")
        career.strategy_plan[week] = strategy_name
        self.save(career)
        return career

    def set_week_starters(
        self, career: CoachCareer, week: int, starters: dict[str, str]
    ) -> CoachCareer:
        if week < career.current_week or week > len(career.schedule):
            raise ValueError("Starter week is out of range for remaining schedule.")
        career.starter_plan[week] = starters
        self.save(career)
        return career

    def _decision_score_swing(self, career: CoachCareer) -> int:
        morale_bonus = (career.morale - 50) // 15
        style_bonus = 0
        style = career.coach_style.lower()
        if "run" in style:
            style_bonus += 1
        if "defens" in style:
            style_bonus += 1
        coach_bonus = career.coach_level // 2
        total = (
            morale_bonus
            + career.offense_modifier
            + career.defense_modifier
            + style_bonus
            + coach_bonus
        )
        return max(-7, min(10, total))

    @staticmethod
    def get_next_game(career: CoachCareer) -> ScheduledGame | None:
        for game in career.schedule:
            if not game.played:
                return game
        return None

    def reset_for_new_season(self, career: CoachCareer, weeks: int = 12) -> CoachCareer:
        career.last_season_wins = career.wins
        career.last_season_losses = career.losses
        updated_roster, summary = self.roster_manager.run_offseason(career.roster)
        if career.signed_recruits:
            for recruit in career.signed_recruits:
                updated_roster.append(dict(recruit))
                summary.append(
                    f"Signed recruit {recruit['name']} ({recruit['position']}) OVR {recruit['overall']}"
                )
        career.roster = updated_roster
        career.signed_recruits = []
        career.offseason_summary = summary[-20:]
        career.scouting_points = min(
            220, career.scouting_points + self.scouting_points_regen(career) + 30
        )
        career.scouting_reports = []
        career.staff_hiring_pool = self.generate_staff_hiring_pool(career)
        career.schedule = self._generate_schedule(career.team_id, weeks=weeks)
        career.current_week = 1
        career.season += 1
        career.recruiting_budget = self.calculate_recruiting_budget(
            career.last_season_wins, career.last_season_losses
        )
        career.recruiting_budget_remaining = career.recruiting_budget
        career.wins = 0
        career.losses = 0
        career.recruiting_modifier = max(0, career.recruiting_modifier - 1)
        career.player_development_bonus = 0
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
        career = CoachCareer(
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
            recruiting_modifier=data.get("recruiting_modifier", 0),
            player_development_bonus=data.get("player_development_bonus", 0),
            schedule=schedule,
            decision_history=data.get("decision_history", []),
            strategy_plan={int(k): v for k, v in data.get("strategy_plan", {}).items()},
            starter_plan={int(k): v for k, v in data.get("starter_plan", {}).items()},
            ai_difficulty=data.get("ai_difficulty", "Normal"),
            ai_adaptation={k: int(v) for k, v in data.get("ai_adaptation", {}).items()},
            scouting_points=int(data.get("scouting_points", 100)),
            recruiting_budget=int(data.get("recruiting_budget", 1800)),
            recruiting_budget_remaining=int(
                data.get(
                    "recruiting_budget_remaining", data.get("recruiting_budget", 1800)
                )
            ),
            last_season_wins=int(data.get("last_season_wins", 0)),
            last_season_losses=int(data.get("last_season_losses", 0)),
            scouting_reports=data.get("scouting_reports", []),
            recruiting_board=data.get("recruiting_board", {}),
            signed_recruits=data.get("signed_recruits", []),
            roster=data.get("roster", self._build_initial_roster(data["team_id"])),
            weekly_progress_notes=data.get("weekly_progress_notes", []),
            offseason_summary=data.get("offseason_summary", []),
            coaching_staff=data.get(
                "coaching_staff",
                self._build_default_staff(data.get("coach_name", "Coach")),
            ),
            staff_hiring_pool=data.get("staff_hiring_pool", []),
        )
        if not career.staff_hiring_pool:
            career.staff_hiring_pool = self.generate_staff_hiring_pool(career)
        return career

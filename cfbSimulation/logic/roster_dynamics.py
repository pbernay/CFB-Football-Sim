"""Recruiting, scouting, and roster progression helpers for career mode."""

from __future__ import annotations

import random
from dataclasses import dataclass

POSITIONS = ("QB", "RB", "WR", "TE", "OL", "DL", "LB", "CB", "S", "K")
ASPIRATIONS = (
    "championship contender",
    "early playing time",
    "player development",
    "big stage exposure",
    "stability",
)


@dataclass(frozen=True)
class RecruitProfile:
    recruit_id: str
    first_name: str
    last_name: str
    position: str
    overall: int
    potential: int
    aspiration: str


@dataclass(frozen=True)
class ScoutingReport:
    recruit_id: str
    name: str
    position: str
    overall: int
    scout_note: str
    aspiration: str


@dataclass(frozen=True)
class RecruitingOfferResult:
    accepted: bool
    reason: str
    score: float


class RosterDynamicsManager:
    """Handles randomized scouting pools, offer decisions, and offseason roster churn."""

    def __init__(self, seed: int | None = None) -> None:
        self.random = random.Random(seed)

    def generate_scouting_reports(self, investment: int, existing_ids: set[str], limit: int = 8) -> list[dict[str, str | int]]:
        quality_bonus = max(0, min(16, investment // 8))
        count = max(3, min(limit, 3 + investment // 10 + self.random.randint(0, 2)))
        reports: list[dict[str, str | int]] = []
        for _ in range(count):
            recruit = self._build_recruit(existing_ids, quality_bonus)
            report = ScoutingReport(
                recruit_id=recruit.recruit_id,
                name=f"{recruit.first_name} {recruit.last_name}",
                position=recruit.position,
                overall=recruit.overall,
                scout_note=self._potential_to_note(recruit.potential),
                aspiration=recruit.aspiration,
            )
            reports.append(report.__dict__)
        reports.sort(key=lambda item: int(item["overall"]), reverse=True)
        return reports

    def evaluate_offer(
        self,
        recruit: dict[str, str | int],
        salary_offer: int,
        team_reputation: float,
        expected_role_score: float,
    ) -> RecruitingOfferResult:
        aspiration = str(recruit["aspiration"])
        desired_salary = 220 + int(recruit["overall"]) * 3 + int(recruit["potential"]) * 2
        salary_score = max(-14.0, min(30.0, (salary_offer - desired_salary) / 26.0))
        reputation_score = (team_reputation - 50.0) / 2.4
        role_score = expected_role_score

        aspiration_mod = 0.0
        if aspiration == "championship contender":
            aspiration_mod += (team_reputation - 58) / 3.5
        elif aspiration == "early playing time":
            aspiration_mod += role_score / 1.6
        elif aspiration == "player development":
            aspiration_mod += int(recruit["potential"]) / 14.0
        elif aspiration == "big stage exposure":
            aspiration_mod += (team_reputation - 50) / 4.0
        else:
            aspiration_mod += 1.5

        score = salary_score + reputation_score + role_score + aspiration_mod + self.random.uniform(-4.5, 5.5)
        accepted = score >= 13
        reason = "Accepted offer" if accepted else "Rejected offer"
        return RecruitingOfferResult(accepted=accepted, reason=reason, score=round(score, 2))

    def weekly_progression(self, roster: list[dict[str, str | int]], team_success: float) -> list[str]:
        updates: list[str] = []
        for player in roster:
            potential = int(player.get("potential", 60))
            overall = int(player.get("overall", 60))
            trend = (potential - overall) / 24.0 + team_success / 10.0 + self.random.uniform(-0.7, 0.7)
            if trend > 0.45:
                delta = 1
            elif trend < -0.5:
                delta = -1
            else:
                delta = 0
            if delta != 0:
                player["overall"] = max(45, min(99, overall + delta))
                updates.append(f"{player['first_name']} {player['last_name']} ({player['position']}) {'+' if delta > 0 else ''}{delta} OVR")
        return updates

    def run_offseason(self, roster: list[dict[str, str | int]]) -> tuple[list[dict[str, str | int]], list[str]]:
        next_roster: list[dict[str, str | int]] = []
        notes: list[str] = []
        draft_threshold = 82
        for player in roster:
            age = int(player.get("age", 20)) + 1
            overall = int(player.get("overall", 60))
            potential = int(player.get("potential", 60))
            left_reason = ""
            if age >= 23:
                left_reason = "Graduated"
            elif overall >= draft_threshold and self.random.random() < 0.35 + max(0, overall - 82) / 45:
                left_reason = "Entered draft"

            if left_reason:
                notes.append(f"{player['first_name']} {player['last_name']} ({player['position']}) - {left_reason}")
                continue

            growth = int(round((potential - overall) / 16.0 + self.random.uniform(-1.2, 1.2)))
            player["overall"] = max(45, min(99, overall + growth))
            player["age"] = age
            next_roster.append(player)
            if growth != 0:
                notes.append(f"{player['first_name']} {player['last_name']} offseason {'+' if growth > 0 else ''}{growth} OVR")

        return next_roster, notes

    def _build_recruit(self, existing_ids: set[str], quality_bonus: int) -> RecruitProfile:
        while True:
            recruit_id = f"rID{self.random.randint(10000, 99999)}"
            if recruit_id not in existing_ids:
                existing_ids.add(recruit_id)
                break
        first = self.random.choice(("Jay", "Noah", "Cam", "Ty", "Liam", "Ezra", "Malik", "Dante", "Brady", "Xavier"))
        last = self.random.choice(("Parker", "Mills", "Douglas", "Harper", "Stone", "Bennett", "Cross", "Turner", "Shaw", "Brooks"))
        overall = self.random.randint(58, 80) + quality_bonus // 4
        potential = max(overall + 1, min(97, overall + self.random.randint(3, 18) + quality_bonus // 2))
        return RecruitProfile(
            recruit_id=recruit_id,
            first_name=first,
            last_name=last,
            position=self.random.choice(POSITIONS),
            overall=max(55, min(88, overall)),
            potential=potential,
            aspiration=self.random.choice(ASPIRATIONS),
        )

    @staticmethod
    def _potential_to_note(potential: int) -> str:
        if potential >= 91:
            return "Generational ceiling"
        if potential >= 84:
            return "Future all-conference impact"
        if potential >= 76:
            return "High-upside project"
        if potential >= 68:
            return "Solid long-term contributor"
        return "Depth piece with limited upside"

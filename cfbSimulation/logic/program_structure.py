"""Program tiering, division assignment, and poll systems."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import random

from cfbSimulation.data.repository import DatabaseRepository
from cfbSimulation.logic.simulator import GameSimulator


class Division(str, Enum):
    FBS = "FBS"
    FCS = "FCS"


class ProgramTier(str, Enum):
    ELITE = "ELITE"
    STRONG = "STRONG"
    MID = "MID"
    WEAK = "WEAK"
    BOTTOM = "BOTTOM"


@dataclass(frozen=True)
class ProgramProfile:
    team_id: str
    team_name: str
    base_program_rating: float
    prestige: float
    facilities: float
    coach_reputation: float
    historical_success: float
    current_roster_strength: float
    nil_resources: float

    @property
    def computed_program_power(self) -> float:
        return round(
            (self.prestige * 0.25)
            + (self.facilities * 0.15)
            + (self.coach_reputation * 0.15)
            + (self.historical_success * 0.15)
            + (self.current_roster_strength * 0.20)
            + (self.nil_resources * 0.10),
            2,
        )

    @property
    def tier(self) -> ProgramTier:
        rating = self.base_program_rating
        if rating >= 85:
            return ProgramTier.ELITE
        if rating >= 70:
            return ProgramTier.STRONG
        if rating >= 50:
            return ProgramTier.MID
        if rating >= 30:
            return ProgramTier.WEAK
        return ProgramTier.BOTTOM

    @property
    def recruiting_interest_multiplier(self) -> float:
        return {
            ProgramTier.ELITE: 1.20,
            ProgramTier.STRONG: 1.10,
            ProgramTier.MID: 1.00,
            ProgramTier.WEAK: 0.90,
            ProgramTier.BOTTOM: 0.80,
        }[self.tier]

    @property
    def preseason_poll_bias(self) -> float:
        return {
            ProgramTier.ELITE: 8.0,
            ProgramTier.STRONG: 4.0,
            ProgramTier.MID: 0.0,
            ProgramTier.WEAK: -4.0,
            ProgramTier.BOTTOM: -8.0,
        }[self.tier]


@dataclass(frozen=True)
class TeamProgramContext:
    team_id: str
    team_name: str
    division: Division
    profile: ProgramProfile


@dataclass
class PollRanking:
    rank: int
    team_id: str
    team_name: str
    record: str
    movement_from_last_week: int
    points: int
    first_place_votes: int


class ProgramStructureEngine:
    """Builds division assignments, program profiles, and AP/FCS polls."""

    def __init__(
        self,
        repository: DatabaseRepository,
        simulator: GameSimulator,
        seed: int | None = None,
        top_x_fbs: int | None = None,
    ) -> None:
        self.repository = repository
        self.simulator = simulator
        self.random = random.Random(seed)
        self.top_x_fbs = top_x_fbs
        self._contexts_cache: dict[str, TeamProgramContext] | None = None
        self._poll_scores: dict[str, float] = {}
        self._poll_records: dict[str, tuple[int, int]] = {}
        self._last_rankings: dict[Division, list[str]] = {
            Division.FBS: [],
            Division.FCS: [],
        }

    def build_contexts(
        self, manual_assignments: dict[str, Division] | None = None
    ) -> dict[str, TeamProgramContext]:
        if self._contexts_cache is not None:
            return self._contexts_cache

        snapshots: list[tuple[str, str, float]] = []
        for team in self.repository.list_teams():
            snap = self.simulator.build_team_snapshot(team.team_id)
            snapshots.append((team.team_id, team.name, snap.overall_rating))

        fbs_count = self.top_x_fbs or max(1, round(len(snapshots) * 0.55))
        ordered = sorted(snapshots, key=lambda item: item[2], reverse=True)
        contexts: dict[str, TeamProgramContext] = {}

        for idx, (team_id, team_name, overall) in enumerate(ordered):
            base = max(0.0, min(100.0, overall))
            noise = self._stable_noise(team_id)
            profile = ProgramProfile(
                team_id=team_id,
                team_name=team_name,
                base_program_rating=base,
                prestige=self._clamp(base + 8 + noise),
                facilities=self._clamp(base + 2 + (noise * 0.5)),
                coach_reputation=self._clamp(base + (noise * 0.7)),
                historical_success=self._clamp(base + 5 + (noise * 0.8)),
                current_roster_strength=self._clamp(base + (noise * 0.4)),
                nil_resources=self._clamp(base - 1 + (noise * 0.6)),
            )
            division = Division.FBS if idx < fbs_count else Division.FCS
            if manual_assignments and team_id in manual_assignments:
                division = manual_assignments[team_id]
            contexts[team_id] = TeamProgramContext(
                team_id=team_id, team_name=team_name, division=division, profile=profile
            )
            self._poll_records[team_id] = (0, 0)

        self._contexts_cache = contexts
        self._init_preseason_scores()
        return contexts

    def _init_preseason_scores(self) -> None:
        contexts = self._contexts_cache or {}
        for team_id, context in contexts.items():
            profile = context.profile
            preseason_score = (
                profile.computed_program_power * 0.60
                + profile.historical_success * 0.20
                + (profile.prestige + profile.preseason_poll_bias) * 0.20
            )
            self._poll_scores[team_id] = preseason_score

    def preseason_rankings(self, division: Division) -> list[PollRanking]:
        return self._compute_rankings(division)

    def record_game(
        self, home_id: str, away_id: str, home_score: int, away_score: int, week: int
    ) -> None:
        contexts = self.build_contexts()
        home_ctx = contexts[home_id]
        away_ctx = contexts[away_id]
        home_prev_rank = self._rank_for_team(home_id, home_ctx.division)
        away_prev_rank = self._rank_for_team(away_id, away_ctx.division)

        margin = abs(home_score - away_score)
        home_win = home_score > away_score
        away_win = away_score > home_score

        self._apply_result(
            team_id=home_id,
            opponent_id=away_id,
            won=home_win,
            margin=margin,
            week=week,
            opponent_rank=away_prev_rank,
        )
        self._apply_result(
            team_id=away_id,
            opponent_id=home_id,
            won=away_win,
            margin=margin,
            week=week,
            opponent_rank=home_prev_rank,
        )

        if (
            home_ctx.division != away_ctx.division
            and away_ctx.division == Division.FCS
            and away_win
        ):
            self._poll_scores[away_id] += 12
            self._poll_scores[home_id] -= 15

    def weekly_rankings(self, division: Division) -> list[PollRanking]:
        return self._compute_rankings(division)

    def _apply_result(
        self,
        team_id: str,
        opponent_id: str,
        won: bool,
        margin: int,
        week: int,
        opponent_rank: int,
    ) -> None:
        contexts = self._contexts_cache or {}
        team_ctx = contexts[team_id]
        opponent_ctx = contexts[opponent_id]
        wins, losses = self._poll_records.get(team_id, (0, 0))
        if won:
            wins += 1
        else:
            losses += 1
        self._poll_records[team_id] = (wins, losses)

        base = self._poll_scores.get(team_id, team_ctx.profile.computed_program_power)
        if won:
            swing = 5.0
            if 0 < opponent_rank <= 25:
                swing *= 1.25
            if 0 < opponent_rank <= 10:
                swing *= 1.40
            if opponent_rank > self._rank_for_team(team_id, team_ctx.division):
                swing *= 1.75
                swing += 4
        else:
            swing = -6.0
            if margin <= 7:
                swing *= 0.75
            if (
                opponent_ctx.division == Division.FCS
                and team_ctx.division == Division.FBS
            ):
                swing *= 1.50

        record_score = ((wins / max(wins + losses, 1)) * 100.0) * 0.35
        mov_score = min(24.0, margin) * 0.15
        opp_rank_score = (26 - min(max(opponent_rank, 1), 25)) * 0.10
        momentum_score = min(5, wins) * 1.5
        power_score = team_ctx.profile.computed_program_power * 0.10
        prestige_modifier = 1 + (0.15 * (team_ctx.profile.prestige / 100.0))

        new_score = (
            base
            + (swing * prestige_modifier)
            + record_score
            + mov_score
            + opp_rank_score
            + momentum_score
            + power_score
        )
        if week <= 4 and team_ctx.profile.tier == ProgramTier.ELITE and not won:
            new_score *= 0.85
        self._poll_scores[team_id] = new_score

    def _compute_rankings(self, division: Division) -> list[PollRanking]:
        contexts = self._contexts_cache or {}
        candidates = [ctx for ctx in contexts.values() if ctx.division == division]
        ordered = sorted(
            candidates,
            key=lambda ctx: self._poll_scores.get(ctx.team_id, 0.0),
            reverse=True,
        )[:25]
        previous = self._last_rankings.get(division, [])
        output: list[PollRanking] = []
        for idx, ctx in enumerate(ordered, start=1):
            wins, losses = self._poll_records.get(ctx.team_id, (0, 0))
            prev_rank = (
                previous.index(ctx.team_id) + 1 if ctx.team_id in previous else idx
            )
            output.append(
                PollRanking(
                    rank=idx,
                    team_id=ctx.team_id,
                    team_name=ctx.team_name,
                    record=f"{wins}-{losses}",
                    movement_from_last_week=prev_rank - idx,
                    points=int(round(self._poll_scores.get(ctx.team_id, 0.0))),
                    first_place_votes=1 if idx == 1 else 0,
                )
            )
        self._last_rankings[division] = [item.team_id for item in output]
        return output

    def _rank_for_team(self, team_id: str, division: Division) -> int:
        ranking = self._compute_rankings(division)
        for item in ranking:
            if item.team_id == team_id:
                return item.rank
        return 99

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(100.0, round(value, 2)))

    @staticmethod
    def _stable_noise(team_id: str) -> float:
        return float((sum(ord(ch) for ch in team_id) % 11) - 5)

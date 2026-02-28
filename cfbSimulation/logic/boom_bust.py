"""Boom/bust performance modeling for per-game effective ratings."""

from __future__ import annotations

import random
from dataclasses import dataclass

from cfbSimulation.data.repository import PlayerRecord


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


@dataclass(frozen=True)
class BoomBustContext:
    """Context inputs used to compute effective game multipliers."""

    home: bool = False
    road: bool = False
    rivalry: bool = False
    playoff: bool = False
    weather: str = "clear"
    crowd: float = 40.0
    travel_distance: float = 20.0
    team_avg_leadership: float = 50.0


@dataclass(frozen=True)
class TeamBoomBustEffect:
    offense_gpm: float
    defense_gpm: float
    special_gpm: float


class BoomBustEngine:
    """Computes bounded game multipliers based on player traits + context."""

    MIN_GPM = 0.75
    MAX_GPM = 1.25
    MIN_Z = -2.5
    MAX_Z = 2.5

    POSITION_MAX_SWING = {
        "QB": 0.22,
        "RB": 0.27,
        "WR": 0.30,
        "TE": 0.25,
        "OT": 0.18,
        "OG": 0.18,
        "C": 0.18,
        "DE": 0.26,
        "DT": 0.26,
        "LB": 0.24,
        "CB": 0.28,
        "S": 0.24,
        "K": 0.20,
        "P": 0.20,
    }

    OFFENSE_POSITIONS = {"QB", "RB", "WR", "TE", "OT", "OG", "C"}
    DEFENSE_POSITIONS = {"DE", "DT", "LB", "CB", "S"}
    SPECIAL_POSITIONS = {"K", "P"}

    def __init__(self, rng: random.Random):
        self.rng = rng

    def build_team_effect(self, players: list[PlayerRecord], context: BoomBustContext) -> TeamBoomBustEffect:
        offense = self._unit_gpm([p for p in players if p.position in self.OFFENSE_POSITIONS], context, "offense")
        defense = self._unit_gpm([p for p in players if p.position in self.DEFENSE_POSITIONS], context, "defense")
        special = self._unit_gpm([p for p in players if p.position in self.SPECIAL_POSITIONS], context, "special")
        return TeamBoomBustEffect(offense_gpm=offense, defense_gpm=defense, special_gpm=special)

    def _unit_gpm(self, players: list[PlayerRecord], context: BoomBustContext, unit: str) -> float:
        if not players:
            return 1.0

        samples = [self._player_gpm(player, context, unit) for player in players]
        return round(_clamp(sum(samples) / len(samples), self.MIN_GPM, self.MAX_GPM), 4)

    def _player_gpm(self, player: PlayerRecord, context: BoomBustContext, unit: str) -> float:
        cons, clu, awr, fatigue, morale, confidence, experience = self._trait_bundle(player)

        volatility = _clamp((100 - cons) / 100, 0.05, 0.85)
        volatility *= _clamp(1 - 0.20 * (experience / 100), 0.85, 1.0)

        if context.rivalry:
            volatility *= 1.10 * (1 - 0.05 * (clu / 100))
        if context.playoff:
            volatility *= 1.12
        if fatigue < 50:
            volatility *= 1 + 0.15 * ((50 - fatigue) / 50)

        z_score = _clamp(self.rng.gauss(0, 1), self.MIN_Z, self.MAX_Z)
        max_swing = self.POSITION_MAX_SWING.get(player.position, 0.25)
        gpm = 1 + (z_score * volatility * max_swing)

        if context.home:
            gpm += 0.01
        if context.road:
            gpm += -0.02 * _clamp((60 - awr) / 60, 0, 1)

        if context.playoff and clu < 55:
            gpm -= 0.02

        gpm += self._weather_modifier(context.weather, player.position, unit)
        if context.road:
            gpm += self._crowd_modifier(player.position, unit, context.crowd)

        if fatigue < 55:
            gpm += -0.06 * _clamp((55 - fatigue) / 55, 0, 1)

        gpm += self._centered_modifier(morale, max_bonus=0.05, max_penalty=-0.05)
        gpm += self._centered_modifier(confidence, max_bonus=0.03, max_penalty=-0.03)

        travel_norm = _clamp(context.travel_distance / 100, 0, 1)
        stamina = _clamp((player.overall + player.potential) / 2, 0, 100)
        gpm += -0.02 * travel_norm * _clamp((60 - stamina) / 60, 0, 1)

        gpm += _clamp(0.01 * ((context.team_avg_leadership - 50) / 50), -0.01, 0.01)

        if player.position in self.OFFENSE_POSITIONS or player.position in self.DEFENSE_POSITIONS:
            gpm += self._extreme_event(cons, awr, clu, context)

        return _clamp(gpm, self.MIN_GPM, self.MAX_GPM)

    def _trait_bundle(self, player: PlayerRecord) -> tuple[float, float, float, float, float, float, float]:
        base = _clamp((player.overall + player.potential) / 2, 0, 100)
        seeded = random.Random(player.player_id)
        spread = lambda amount: seeded.uniform(-amount, amount)

        cons = _clamp(base + spread(12), 20, 99)
        clu = _clamp(base + spread(15), 15, 99)
        awr = _clamp((base * 0.8) + spread(10), 15, 99)
        fatigue = _clamp(base - 8 + spread(18), 20, 100)
        morale = _clamp(50 + spread(30), 0, 100)
        confidence = _clamp(50 + spread(24), 0, 100)
        experience = _clamp((100 - max(player.age - 18, 0) * 12) if player.age < 23 else 45, 20, 100)
        return cons, clu, awr, fatigue, morale, confidence, experience

    @staticmethod
    def _centered_modifier(value: float, max_bonus: float, max_penalty: float) -> float:
        if value >= 50:
            return max_bonus * ((value - 50) / 50)
        return max_penalty * ((50 - value) / 50)

    @staticmethod
    def _weather_modifier(weather: str, position: str, unit: str) -> float:
        weather = weather.lower()
        if weather == "rain":
            if unit == "special":
                return -0.02
            return -0.02 if unit == "offense" else 0.0
        if weather == "snow":
            if unit == "special":
                return -0.03
            return -0.03 if unit == "offense" else 0.0
        if weather == "wind":
            if unit == "special":
                return -0.04
            if position == "QB":
                return -0.02
        return 0.0

    @staticmethod
    def _crowd_modifier(position: str, unit: str, crowd: float) -> float:
        intensity = _clamp(crowd / 100, 0, 1)
        if unit == "offense":
            if position == "QB":
                return -0.02 * intensity
            if position in {"OT", "OG", "C"}:
                return -0.01 * intensity
            if position in {"WR", "RB", "TE"}:
                return -0.005 * intensity
        if unit == "defense":
            if position in {"DE", "DT"}:
                return 0.005 * intensity
            if position == "LB":
                return 0.003 * intensity
            if position in {"CB", "S"}:
                return 0.002 * intensity
        return 0.0

    def _extreme_event(self, cons: float, awr: float, clu: float, context: BoomBustContext) -> float:
        hot = 0.03 * (1 - 0.40 * (cons / 100)) * (1 - 0.25 * (awr / 100))
        meltdown = 0.03 * (1 + 0.60 * _clamp((65 - awr) / 65, 0, 1)) * (1 - 0.35 * (clu / 100))
        if context.road:
            meltdown *= 1.15
        if context.playoff:
            meltdown *= 1.15

        roll = self.rng.random()
        if roll < hot:
            return 0.10
        if roll < hot + meltdown:
            return -0.10
        return 0.0

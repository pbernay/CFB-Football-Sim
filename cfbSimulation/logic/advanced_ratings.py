"""Advanced ratings metadata and helpers.

This module centralizes the expanded ratings taxonomy and provides helper
calculations for potential-driven growth plus position-based unit ratings.
"""

from __future__ import annotations

from dataclasses import dataclass

from cfbSimulation.data.repository import PlayerRecord


RATING_SCALE = {
    "min": 0,
    "max": 100,
    "meaning": {
        (0, 39): "Poor",
        (40, 59): "Average",
        (60, 74): "Good",
        (75, 89): "Great",
        (90, 100): "Elite",
    },
}

UNIVERSAL_RATINGS: dict[str, str] = {
    "SPD": "Speed",
    "ACC": "Acceleration",
    "AGI": "Agility",
    "STR": "Strength",
    "AWR": "Awareness",
    "STA": "Stamina",
    "INJ": "Injury",
    "TGH": "Toughness",
    "DISC": "Discipline",
    "CLU": "Clutch",
    "CONS": "Consistency",
}

POSITION_RATING_MAP: dict[str, tuple[str, ...]] = {
    "QB": ("THP", "SAC", "MAC", "DAC", "TOR", "UPR", "DEC", "POK", "PRS", "BSK", "CAR", "BCV"),
    "RB": ("CAR", "BCV", "ELU", "JUK", "SPN", "TRK", "BTK", "CTH", "RRT", "PBK", "RBK"),
    "WR": ("REL", "CTH", "CIT", "SPC", "JMP", "SRR", "MRR", "DRR", "RAC", "BCV"),
    "TE": ("CTH", "CIT", "SRR", "MRR", "RBK", "PBK", "IBL"),
    "OT": ("PBK", "RBK", "IBL", "PBF", "RBF", "HND"),
    "OG": ("PBK", "RBK", "IBL", "PBF", "RBF", "HND"),
    "C": ("PBK", "RBK", "IBL", "PBF", "RBF", "HND", "SNP", "LAD"),
    "DE": ("PMV", "FMV", "BSH", "PRC", "PUR", "TAK", "SPR"),
    "DT": ("PMV", "FMV", "BSH", "PRC", "PUR", "TAK"),
    "LB": ("TAK", "BSH", "PRC", "PUR", "MCV", "ZCV", "BLZ", "PMV", "FMV"),
    "CB": ("MCV", "ZCV", "PRS", "PLB", "CTH", "JMP"),
    "S": ("MCV", "ZCV", "PRC", "PUR", "TAK", "HIT", "PLB"),
    "K": ("KPW", "KAC", "KCL"),
    "P": ("PPW", "PAC", "CFC"),
    "RET": ("RVN", "ELU", "CAR"),
}


@dataclass(frozen=True)
class PlayerAdvancedRating:
    player_id: str
    position: str
    position_rating: int
    potential: int
    growth_headroom: int


def rating_tier(value: float) -> str:
    score = int(round(value))
    for bounds, label in RATING_SCALE["meaning"].items():
        low, high = bounds
        if low <= score <= high:
            return label
    return "Unknown"


def clamp_rating(value: float) -> int:
    return int(max(RATING_SCALE["min"], min(RATING_SCALE["max"], round(value))))


def position_based_player_rating(player: PlayerRecord, target_position: str | None = None) -> PlayerAdvancedRating:
    """Estimate a position-centric rating from current overall + potential.

    The model intentionally uses a mild bonus when a player is evaluated at
    their listed position and a small penalty when projected out of position.
    """

    target = (target_position or player.position).upper()
    in_position_bonus = 3 if target == player.position else -4
    rating = clamp_rating((player.overall * 0.78) + (player.potential * 0.22) + in_position_bonus)
    growth_headroom = max(0, int(player.potential) - int(player.overall))
    return PlayerAdvancedRating(
        player_id=player.player_id,
        position=target,
        position_rating=rating,
        potential=clamp_rating(player.potential),
        growth_headroom=growth_headroom,
    )


def unit_position_rating(players: list[PlayerRecord], positions: set[str], starters: int = 5) -> float:
    unit_players = [p for p in players if p.position in positions]
    if not unit_players:
        return 50.0
    ratings = sorted(
        (position_based_player_rating(player).position_rating for player in unit_players),
        reverse=True,
    )
    selected = ratings[: max(1, starters)]
    return round(sum(selected) / len(selected), 2)


def team_potential_rating(players: list[PlayerRecord]) -> float:
    if not players:
        return 50.0
    return round(sum(clamp_rating(player.potential) for player in players) / len(players), 2)


"""Player statistics tracking for simulated games."""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path

from cfbSimulation.data.repository import DatabaseRepository, PlayerRecord
from cfbSimulation.logic.simulator import TeamSnapshot

DEFAULT_PLAYER_STATS_PATH = Path(__file__).resolve().parents[2] / "datafiles" / "saveData" / "player_stats.json"


@dataclass
class PlayerSeasonStats:
    player_id: str
    team_id: str
    player_name: str
    position: str
    games_played: int = 0
    pass_yards: int = 0
    pass_tds: int = 0
    rush_yards: int = 0
    rush_tds: int = 0
    receiving_yards: int = 0
    receiving_tds: int = 0
    tackles: int = 0
    sacks: int = 0
    interceptions: int = 0
    field_goals: int = 0
    points_scored: int = 0


@dataclass
class TeamGameStats:
    team_id: str
    points: int
    pass_yards: int
    rush_yards: int


@dataclass
class GameStatsResult:
    team_stats: dict[str, TeamGameStats] = field(default_factory=dict)


class PlayerStatsManager:
    def __init__(
        self,
        repository: DatabaseRepository | None = None,
        save_path: Path | str = DEFAULT_PLAYER_STATS_PATH,
        seed: int | None = None,
    ) -> None:
        self.repository = repository or DatabaseRepository()
        self.save_path = Path(save_path)
        self.random = random.Random(seed)

    def record_game(self, home: TeamSnapshot, away: TeamSnapshot) -> GameStatsResult:
        existing = self._load()
        summary: dict[str, TeamGameStats] = {}
        for snapshot in (home, away):
            team_players = self.repository.get_players_for_team(snapshot.team_id)
            if not team_players:
                continue
            for player in team_players:
                stats = existing.get(player.player_id) or PlayerSeasonStats(
                    player_id=player.player_id,
                    team_id=player.team_id,
                    player_name=f"{player.first_name} {player.last_name}",
                    position=player.position,
                )
                stats.games_played += 1
                existing[player.player_id] = stats

            team_game = self._build_team_box_score(snapshot, team_players, existing)
            summary[snapshot.team_id] = team_game

        self._save(existing)
        return GameStatsResult(team_stats=summary)

    def top_players(self, limit: int = 25) -> list[PlayerSeasonStats]:
        all_stats = list(self._load().values())
        all_stats.sort(key=lambda p: (p.points_scored + p.pass_tds * 4 + p.rush_tds * 6 + p.receiving_tds * 6, p.pass_yards + p.rush_yards + p.receiving_yards), reverse=True)
        return all_stats[:limit]

    def get_player(self, player_id: str) -> PlayerSeasonStats | None:
        return self._load().get(player_id)

    def compare_players(self, player_ids: list[str]) -> list[PlayerSeasonStats]:
        stats = self._load()
        return [stats[p] for p in player_ids if p in stats]

    def _build_team_box_score(
        self,
        snapshot: TeamSnapshot,
        players: list[PlayerRecord],
        stat_map: dict[str, PlayerSeasonStats],
    ) -> TeamGameStats:
        qb = next((p for p in players if p.position == "QB"), players[0])
        rbs = [p for p in players if p.position == "RB"] or [qb]
        wrs = [p for p in players if p.position in {"WR", "TE"}] or [qb]
        defenders = [p for p in players if p.position in {"LB", "CB", "S", "DE", "DT"}] or [qb]
        kickers = [p for p in players if p.position == "K"]

        pass_ratio = 0.45 + ((snapshot.strategy.aggressiveness - 0.5) * 0.35)
        pass_ratio = max(0.25, min(0.8, pass_ratio))
        total_yards = int(round(220 + (snapshot.offensive_rating - 65) * 4 + self.random.randint(-45, 45)))
        pass_yards = max(60, int(total_yards * pass_ratio))
        rush_yards = max(40, total_yards - pass_yards)

        remaining_points = snapshot.score
        pass_tds = 0
        rush_tds = 0
        fgs = 0
        while remaining_points >= 3:
            if remaining_points >= 7 and self.random.random() < pass_ratio:
                pass_tds += 1
                remaining_points -= 7
            elif remaining_points >= 7:
                rush_tds += 1
                remaining_points -= 7
            else:
                fgs += 1
                remaining_points -= 3

        qb_stats = stat_map[qb.player_id]
        qb_stats.pass_yards += pass_yards
        qb_stats.pass_tds += pass_tds

        for _ in range(pass_tds):
            receiver = self.random.choice(wrs)
            receiver_stats = stat_map[receiver.player_id]
            receiver_stats.receiving_tds += 1

        for receiver in wrs[: min(3, len(wrs))]:
            stat_map[receiver.player_id].receiving_yards += max(0, int(pass_yards / max(1, len(wrs[:3])) + self.random.randint(-20, 20)))

        for _ in range(rush_tds):
            rusher = self.random.choice(rbs)
            stat_map[rusher.player_id].rush_tds += 1

        for rusher in rbs[: min(2, len(rbs))]:
            stat_map[rusher.player_id].rush_yards += max(0, int(rush_yards / max(1, len(rbs[:2])) + self.random.randint(-18, 18)))

        for _ in range(fgs):
            if kickers:
                stat_map[kickers[0].player_id].field_goals += 1

        for _ in range(max(5, int(snapshot.defensive_rating / 14))):
            defender = self.random.choice(defenders)
            stat_map[defender.player_id].tackles += 1
            if self.random.random() < 0.12:
                stat_map[defender.player_id].sacks += 1
            if self.random.random() < 0.05:
                stat_map[defender.player_id].interceptions += 1

        for player_id, player_stats in stat_map.items():
            if player_stats.team_id != snapshot.team_id:
                continue
            points = player_stats.pass_tds * 4 + player_stats.rush_tds * 6 + player_stats.receiving_tds * 6 + player_stats.field_goals * 3
            player_stats.points_scored = points

        return TeamGameStats(team_id=snapshot.team_id, points=snapshot.score, pass_yards=pass_yards, rush_yards=rush_yards)

    def _load(self) -> dict[str, PlayerSeasonStats]:
        if not self.save_path.exists():
            return {}
        with self.save_path.open("r", encoding="utf-8") as in_file:
            raw = json.load(in_file)
        return {player_id: PlayerSeasonStats(**stats) for player_id, stats in raw.items()}

    def _save(self, stats: dict[str, PlayerSeasonStats]) -> None:
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        serialized = {player_id: asdict(player_stats) for player_id, player_stats in stats.items()}
        with self.save_path.open("w", encoding="utf-8") as out_file:
            json.dump(serialized, out_file, indent=2)

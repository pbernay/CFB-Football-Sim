"""CLI entrypoint for running the CFB Football Sim."""

from __future__ import annotations

import argparse

from cfbSimulation.data.repository import DatabaseRepository
from cfbSimulation.logic.player_stats import PlayerStatsManager
from cfbSimulation.logic.simulator import GameSimulator, format_scoreboard


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a college football simulation game.")
    parser.add_argument("--home", help="Home team ID (example: tID8)")
    parser.add_argument("--away", help="Away team ID (example: tID3)")
    parser.add_argument("--seed", type=int, help="Random seed for reproducible simulations")
    parser.add_argument(
        "--list-teams",
        action="store_true",
        help="List available teams and exit",
    )
    parser.add_argument(
        "--team-limit",
        type=int,
        default=20,
        help="Limit for --list-teams output (default: 20)",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the Coach Career GUI",
    )
    parser.add_argument(
        "--home-strategy",
        default="Balanced",
        help="Strategy profile for the home team (default: Balanced)",
    )
    parser.add_argument(
        "--away-strategy",
        default="Balanced",
        help="Strategy profile for the away team (default: Balanced)",
    )
    parser.add_argument(
        "--player-stats",
        action="store_true",
        help="Show top saved player season stats and exit",
    )
    parser.add_argument(
        "--compare-players",
        help="Comma-separated player IDs to compare from saved stats",
    )
    return parser


def print_teams(repo: DatabaseRepository, limit: int) -> None:
    teams = repo.list_teams(limit=limit)
    print(f"Showing {len(teams)} teams:")
    for team in teams:
        print(f" - {team.team_id:<6} {team.name} ({team.location})")




def print_player_stats(stats_manager: PlayerStatsManager, compare_players: str | None) -> None:
    if compare_players:
        ids = [pid.strip() for pid in compare_players.split(",") if pid.strip()]
        compared = stats_manager.compare_players(ids)
        if not compared:
            print("No matching players found in saved stats.")
            return
        print("Player comparison:")
        for stat in compared:
            tds = stat.pass_tds + stat.rush_tds + stat.receiving_tds
            total_yards = stat.pass_yards + stat.rush_yards + stat.receiving_yards
            print(f" - {stat.player_name} ({stat.player_id}, {stat.team_id}/{stat.position}): {total_yards} yds, {tds} TD, {stat.tackles} tackles")
        return

    leaders = stats_manager.top_players(limit=20)
    if not leaders:
        print("No saved player stats yet. Simulate games in season/career to populate stats.")
        return
    print("Top player stats:")
    for stat in leaders:
        tds = stat.pass_tds + stat.rush_tds + stat.receiving_tds
        print(
            f" - {stat.player_name:<22} {stat.team_id:<5} {stat.position:<3} "
            f"GP {stat.games_played:<2} Pass {stat.pass_yards:<4} Rush {stat.rush_yards:<4} Rec {stat.receiving_yards:<4} TD {tds:<2}"
        )

def resolve_matchup(repo: DatabaseRepository, home: str | None, away: str | None) -> tuple[str, str]:
    if home and away:
        return home, away
    random_home, random_away = repo.get_two_random_team_ids()
    return home or random_home, away or random_away


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.gui:
        from cfbSimulation.gui import launch_gui

        launch_gui()
        return

    repo = DatabaseRepository()
    repo.health_check()

    if args.list_teams:
        print_teams(repo, args.team_limit)
        return

    if args.player_stats or args.compare_players:
        print_player_stats(PlayerStatsManager(repository=repo), args.compare_players)
        return

    home_team_id, away_team_id = resolve_matchup(repo, args.home, args.away)
    stats_manager = PlayerStatsManager(repository=repo, seed=args.seed)
    simulator = GameSimulator(repository=repo, seed=args.seed)

    strategies = simulator.predefined_strategies()
    result = simulator.simulate_single_game(
        home_team_id,
        away_team_id,
        home_strategy=strategies.get(args.home_strategy, strategies["Balanced"]),
        away_strategy=strategies.get(args.away_strategy, strategies["Balanced"]),
    )

    print("Team Ratings (Advanced):")
    print(
        f" - {result.home_team.name}: "
        f"OVR {result.home_team.overall_rating} | OFF {result.home_team.offensive_rating} "
        f"| DEF {result.home_team.defensive_rating} | ST {result.home_team.special_teams_rating} "
        f"| POT {result.home_team.potential_rating}"
    )
    print(
        f" - {result.away_team.name}: "
        f"OVR {result.away_team.overall_rating} | OFF {result.away_team.offensive_rating} "
        f"| DEF {result.away_team.defensive_rating} | ST {result.away_team.special_teams_rating} "
        f"| POT {result.away_team.potential_rating}"
    )

    print(format_scoreboard(result))

    if result.drives_log:
        print("Scoring Summary:")
        for line in result.drives_log:
            print(f" * {line}")

    stats_manager.record_game(result.home_team, result.away_team)


if __name__ == "__main__":
    main()

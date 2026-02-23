"""CLI entrypoint for running the CFB Football Sim."""

from __future__ import annotations

import argparse

from cfbSimulation.data.repository import DatabaseRepository
from cfbSimulation.gui import launch_gui
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
    return parser


def print_teams(repo: DatabaseRepository, limit: int) -> None:
    teams = repo.list_teams(limit=limit)
    print(f"Showing {len(teams)} teams:")
    for team in teams:
        print(f" - {team.team_id:<6} {team.name} ({team.location})")


def resolve_matchup(repo: DatabaseRepository, home: str | None, away: str | None) -> tuple[str, str]:
    if home and away:
        return home, away
    random_home, random_away = repo.get_two_random_team_ids()
    return home or random_home, away or random_away


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.gui:
        launch_gui()
        return

    repo = DatabaseRepository()
    repo.health_check()

    if args.list_teams:
        print_teams(repo, args.team_limit)
        return

    home_team_id, away_team_id = resolve_matchup(repo, args.home, args.away)
    simulator = GameSimulator(repository=repo, seed=args.seed)

    result = simulator.simulate_single_game(home_team_id, away_team_id)

    print("Team Ratings:")
    print(
        f" - {result.home_team.name}: "
        f"OVR {result.home_team.overall_rating} | OFF {result.home_team.offensive_rating} "
        f"| DEF {result.home_team.defensive_rating} | ST {result.home_team.special_teams_rating}"
    )
    print(
        f" - {result.away_team.name}: "
        f"OVR {result.away_team.overall_rating} | OFF {result.away_team.offensive_rating} "
        f"| DEF {result.away_team.defensive_rating} | ST {result.away_team.special_teams_rating}"
    )

    print(format_scoreboard(result))

    if result.drives_log:
        print("Scoring Summary:")
        for line in result.drives_log:
            print(f" * {line}")


if __name__ == "__main__":
    main()

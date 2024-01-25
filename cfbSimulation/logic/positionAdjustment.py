# helps calculate position adjustment overalls (per game)

import sqlite3
import sys
import os

# Database connection setup
conn = sqlite3.connect(
    "datafiles/saveData/theDatabase.db"
)  # Update the path and connector as per your database
cursor = conn.cursor()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gameLogic import Game, Player, Team
from utils.utils import positionNumbers


team_a_ID = "tID8"
team_b_ID = "tID3"


def get_position_averages(teamID):
    # Dictionary to hold the average overall for each position and role
    position_averages = {}

    # Iterate through each position and role to calculate averages
    for position, numbers in positionNumbers.items():
        # Calculate the average overall for starters at each position
        cursor.execute(
            """
            SELECT AVG(Players.Overall) as AvgOverall
            FROM Players
            JOIN "Team Lineups" ON Players.PlayerID = "Team Lineups".PlayerID
            WHERE Players.TeamID = ? AND "Team Lineups".Role = 'Starter' AND Players.Position = ?
            """,
            (teamID, position),
        )
        result = cursor.fetchone()
        position_averages[position] = {
            "Starter": result[0] if result[0] is not None else 0
        }

        # If there are substitutes to consider, calculate their average overall
        if numbers["subs"] > 0:
            cursor.execute(
                """
                SELECT AVG(Players.Overall) as AvgOverall
                FROM Players
                JOIN "Team Lineups" ON Players.PlayerID = "Team Lineups".PlayerID
                WHERE Players.TeamID = ? AND "Team Lineups".Role = 'Substitute' AND Players.Position = ?
                """,
                (teamID, position),
            )
            result = cursor.fetchone()
            position_averages[position]["Substitute"] = (
                result[0] if result[0] is not None else 0
            )

    return position_averages


average_position_team_a = get_position_averages(team_a_ID)
average_position_team_b = get_position_averages(team_b_ID)

for position in average_position_team_a:
    print(
        f"Team A {position} Starters Average: {average_position_team_a[position]['Starter']}"
    )
    if "Substitute" in average_position_team_a[position]:
        print(
            f"Team A {position} Substitutes Average: {average_position_team_a[position]['Substitute']}"
        )

for position in average_position_team_b:
    print(
        f"Team B {position} Starters Average: {average_position_team_b[position]['Starter']}"
    )
    if "Substitute" in average_position_team_b[position]:
        print(
            f"Team B {position} Substitutes Average: {average_position_team_b[position]['Substitute']}"
        )

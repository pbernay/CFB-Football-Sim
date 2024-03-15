# helps calculate position adjustment overalls (per game)

import random
import sqlite3
import sys
import os

# Database connection setup
conn = sqlite3.connect("datafiles/saveData/theDatabase.db")
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


# Iterate through each position and role to get relevant players
def fetch_and_instantiate_players(teamID):
    players = []
    for position, numbers in positionNumbers.items():
        # Get starters
        cursor.execute(
            """
            SELECT * 
            FROM Players
            JOIN "Team Lineups" ON Players.PlayerID = "Team Lineups".PlayerID
            WHERE Players.TeamID = ? AND "Team Lineups".Role = 'Starter' AND Players.Position = ?
            """,
            (teamID, position),
        )
        for row in cursor.fetchall():
            player = Player(
                PlayerID=row[0],
                Fname=row[1],
                Lname=row[2],
                Position=row[3],
                Overall=row[4],
                TeamID=row[5],
                Age=row[6],
                Year=row[7],
                InjuryType=row[8],
                InjuryDuration=row[9],
                Potential=row[10],
                PlayerStatus=row[11],
                Hometown=row[12],
                role=row[16],
                adjustedRating=0,
            )
            players.append(player)

    # Get substitutes if applicable
    if numbers["subs"] > 0:
        cursor.execute(
            """
            SELECT *
            FROM Players
            JOIN "Team Lineups" ON Players.PlayerID = "Team Lineups".PlayerID
            WHERE Players.TeamID = ? AND "Team Lineups".Role = 'Substitute' AND Players.Position = ?
            """,
            (teamID, position),
        )
        for row in cursor.fetchall():
            player = Player(
                PlayerID=row[0],
                Fname=row[1],
                Lname=row[2],
                Position=row[3],
                Overall=row[4],
                TeamID=row[5],
                Age=row[6],
                Year=row[7],
                InjuryType=row[8],
                InjuryDuration=row[9],
                Potential=row[10],
                PlayerStatus=row[11],
                Hometown=row[12],
                role=row[16],
                adjustedRating=0,
            )
            players.append(player)
    return players


# Instantiate teams
team_a_players = fetch_and_instantiate_players("tID8")
team_b_players = fetch_and_instantiate_players("tID3")


def instantiate_team(teamID):
    cursor.execute(
        """
        SELECT *
        FROM Teams
        WHERE TeamID = ?
        """,
        (teamID,),
    )
    result = cursor.fetchone()
    if result:
        # Unpack the result directly into the Team constructor
        team = Team(*result)
        return team
    else:
        print(f"No team found with TeamID: {teamID}")
        return None


team_a = instantiate_team(team_a_ID)
team_b = instantiate_team(team_b_ID)

team_a.players = team_a_players
team_b.players = team_b_players


# Function to calculate offensive and defensive rating averages
def update_team_averages(team, position_averages):
    # Offensive Line Average Calculation (Assuming OT, OG, and C are Offensive Line positions)
    team.OLAVG = (
        position_averages["OT"]["Starter"] * 2
        + position_averages["OG"]["Starter"] * 2
        + position_averages["C"]["Starter"]
    ) / 5
    # Other positions
    team.QBAVG = position_averages["QB"]["Starter"]
    team.RBAVG = (
        position_averages["RB"]["Starter"] * 0.8
        + position_averages["RB"]["Substitute"] * 0.2
    )
    team.WRAVG = (
        position_averages["WR"]["Starter"]
        + position_averages["WR"]["Substitute"] * 2 / 2
    )
    team.TEAVG = (
        position_averages["TE"]["Starter"] * 0.8
        + position_averages["TE"]["Substitute"] * 0.2
    )
    # Defensive Averages
    team.LBAVG = position_averages["LB"]["Starter"]
    team.DBAVG = (
        position_averages["CB"]["Starter"] * 0.8
        + position_averages["CB"]["Substitute"] * 0.2
    )
    team.SAVG = position_averages["S"]["Starter"]
    # DL Averages (Assuming DE and DT are part of Defensive Line)
    team.DLAVG = (
        position_averages["DE"]["Starter"] + position_averages["DT"]["Starter"]
    ) / 2
    # Individual Linemen Averages
    team.DEAVG = position_averages["DE"]["Starter"]
    team.DTAVG = position_averages["DT"]["Starter"]
    team.OTAVG = position_averages["OT"]["Starter"]
    team.OGAVG = position_averages["OG"]["Starter"]
    team.CAVG = position_averages["C"]["Starter"]
    # Kicker Average
    team.KAVG = position_averages["K"]["Starter"]
    # Punter Average
    team.PAVG = position_averages["P"]["Starter"]
    team.OGCAVG = (team.OGAVG + team.CAVG) / 2


# Update Team A and Team B with the calculated averages
update_team_averages(team_a, average_position_team_a)
update_team_averages(team_b, average_position_team_b)


def calculate_qb_psa(
    ol_average, wr_te_average, opposing_db_s_average, opposing_dl_average
):
    psa = 0

    if ol_average > 85:
        psa += 5
    elif ol_average < 60:
        psa -= 5

    if wr_te_average > 80:
        psa += 2
    elif wr_te_average < 60:
        psa -= 2

    if opposing_db_s_average > 85:
        psa -= 3
    elif opposing_db_s_average < 60:
        psa += 3

    if opposing_dl_average > 85:
        psa -= 3
    elif opposing_dl_average < 60:
        psa += 1

    return psa


def calculate_rb_psa(ol_average, opposing_dl_average, opposing_lb_average):
    psa = 0

    if ol_average > 85:
        psa += 5
    elif ol_average < 60:
        psa -= 5

    if opposing_dl_average > 85:
        psa -= 3
    elif opposing_dl_average < 60:
        psa += 1

    if opposing_lb_average > 85:
        psa -= 3
    elif opposing_lb_average < 60:
        psa += 3

    return psa


def calculate_wr_psa(qb_average, opposing_db_average, opposing_s_average):
    psa = 0

    if qb_average > 90:
        psa += 5
    elif qb_average < 60:
        psa -= 5

    if opposing_db_average > 85:
        psa -= 5
    elif opposing_db_average < 60:
        psa += 5

    if opposing_s_average > 85:
        psa -= 3
    elif opposing_s_average < 60:
        psa += 3

    return psa


def calculate_te_psa(qb_average, opposing_db_average, opposing_lb_average):
    psa = 0

    if qb_average > 90:
        psa += 5
    elif qb_average < 60:
        psa -= 5

    if opposing_db_average > 85:
        psa -= 3
    elif opposing_db_average < 60:
        psa += 3

    if opposing_lb_average > 85:
        psa -= 5
    elif opposing_lb_average < 60:
        psa += 5

    return psa


def calculate_ol_psa(ol_average, te_average, opposing_dl_average, opposing_lb_average):
    psa = 0

    if ol_average > 85:
        psa += 3
    elif ol_average < 60:
        psa -= 3

    if te_average > 85:
        psa += 1
    elif te_average < 60:
        psa -= 1

    if opposing_dl_average > 85:
        psa -= 5
    elif opposing_dl_average < 60:
        psa += 5

    if opposing_lb_average > 90:
        psa -= 2

    return psa


def calculate_de_psa(other_de_average, opposing_ot_average):
    psa = 0

    if other_de_average > 85:
        psa += 5
    elif other_de_average < 60:
        psa -= 5

    if opposing_ot_average > 85:
        psa -= 5
    elif opposing_ot_average < 60:
        psa += 5

    return psa


def calculate_dt_psa(lb_average, opposing_og_c_average, opposing_rb_average):
    psa = 0

    if lb_average > 90:
        psa += 2

    if opposing_og_c_average > 85:
        psa -= 5
    elif opposing_og_c_average < 60:
        psa += 5

    if opposing_rb_average > 85:
        psa -= 3
    elif opposing_rb_average < 60:
        psa += 3

    return psa


def calculate_db_s_psa(opposing_qb_average, opposing_wr_average):
    psa = 0

    if opposing_qb_average > 85:
        psa -= 3
    elif opposing_qb_average < 60:
        psa += 3

    if opposing_wr_average > 85:
        psa -= 5
    elif opposing_wr_average < 60:
        psa += 5

    return psa


def calculate_lb_psa(
    dl_average, opposing_qb_average, opposing_rb_average, opposing_te_average
):
    psa = 0

    if dl_average > 85:
        psa += 2
    elif dl_average < 60:
        psa -= 2

    if opposing_qb_average > 90:
        psa -= 5
    elif opposing_qb_average < 65:
        psa += 5

    if opposing_rb_average > 85:
        psa -= 3
    elif opposing_rb_average < 60:
        psa += 3

    if opposing_te_average > 85:
        psa -= 3
    elif opposing_te_average < 60:
        psa += 3

    return psa


def calculate_psa_adjustment(player, team, opposing_team):
    psa = 0

    if player.Position == "QB":
        psa += calculate_qb_psa(
            team.OLAVG, team.WRAVG, opposing_team.DBAVG, opposing_team.DLAVG
        )
    elif player.Position == "RB":
        psa += calculate_rb_psa(team.OLAVG, opposing_team.DLAVG, opposing_team.LBAVG)
    elif player.Position == "WR":
        psa += calculate_wr_psa(team.QBAVG, opposing_team.DBAVG, opposing_team.SAVG)
    elif player.Position == "TE":
        psa += calculate_te_psa(team.QBAVG, opposing_team.DBAVG, opposing_team.LBAVG)
    elif player.Position in ["OT", "OG", "C"]:
        psa += calculate_ol_psa(
            team.OLAVG, team.TEAVG, opposing_team.DLAVG, opposing_team.LBAVG
        )
    elif player.Position in ["DE"]:
        psa += calculate_de_psa(team.DEAVG, opposing_team.OTAVG)
    elif player.Position in ["DT"]:
        psa += calculate_dt_psa(team.LBAVG, opposing_team.OGCAVG, opposing_team.RBAVG)
    elif player.Position in ["CB", "S"]:
        psa += calculate_db_s_psa(opposing_team.QBAVG, opposing_team.WRAVG)
    elif player.Position in ["LB"]:
        psa += calculate_lb_psa(
            team.DLAVG,
            opposing_team.QBAVG,
            opposing_team.RBAVG,
            opposing_team.TEAVG,
        )

    return psa


def calculate_pa_adjustment(player):
    pa = 0
    random_number = random.randint(60, 100)

    if random_number < player.Potential:
        pa += 5
    elif random_number < player.Potential and player.Potential < player.Overall:
        pa -= 5

    return pa


# Calculate adjusted overall for each player
for player in team_a.players:
    psa = calculate_psa_adjustment(player, team_a, team_b)
    pa = calculate_pa_adjustment(player)
    adjusted_overall = player.Overall + psa + pa
    # Use the adjusted overall for further calculations or display

for player in team_b.players:
    psa = calculate_psa_adjustment(player, team_b, team_a)
    pa = calculate_pa_adjustment(player)
    adjusted_overall = player.Overall + psa + pa
    # Use the adjusted overall for further calculations or display

    # Display team starters and subs with name, current overall, and adjusted overall for Team A
    print("Team A Starters:")
    for player in team_a.players:
        psa = calculate_psa_adjustment(player, team_a, team_b)
        pa = calculate_pa_adjustment(player)
        adjusted_overall = player.Overall + psa + pa
        print(
            f"Name: {player.Fname} {player.Lname}, Current Overall: {player.Overall}, Adjusted Overall: {adjusted_overall}, Position: {player.Position}"
        )

    # Display team starters and subs with name, current overall, and adjusted overall for Team B
    print("Team B Starters:")
    for player in team_b.players:
        psa = calculate_psa_adjustment(player, team_b, team_a)
        pa = calculate_pa_adjustment(player)
        adjusted_overall = player.Overall + psa + pa
        print(
            f"Name: {player.Fname} {player.Lname}, Current Overall: {player.Overall}, Adjusted Overall: {adjusted_overall}, Position: {player.Position}"
        )

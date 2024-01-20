import sqlite3

# Database connection setup
conn = sqlite3.connect("data/saveData/theDatabase.db")
cursor = conn.cursor()

# Specific numbers for starters and subs for each position
positionNumbers = {
    "QB": {"starters": 1, "subs": 0},
    "RB": {"starters": 1, "subs": 1},
    "WR": {"starters": 1, "subs": 2},
    "TE": {"starters": 1, "subs": 1},
    "OT": {"starters": 2, "subs": 0},
    "OG": {"starters": 2, "subs": 0},
    "C": {"starters": 1, "subs": 0},
    "DE": {"starters": 2, "subs": 0},
    "DT": {"starters": 2, "subs": 0},
    "LB": {"starters": 3, "subs": 0},
    "CB": {"starters": 2, "subs": 1},
    "S": {"starters": 2, "subs": 0},
    "K": {"starters": 1, "subs": 0},
    "P": {"starters": 1, "subs": 0},
}


# Fetch players and coach's overall rating for each team
def getTeamData(teamID):
    cursor.execute(
        "SELECT PlayerID, Overall, Position FROM Players WHERE TeamID = ?", (teamID,)
    )
    players = cursor.fetchall()

    cursor.execute(
        """
        SELECT Coaches."Coach Overall"
        FROM Teams 
        JOIN Coaches ON Teams.CoachID = Coaches.CoachID 
        WHERE Teams.TeamID = ?
    """,
        (teamID,),
    )
    coachOverallResult = cursor.fetchone()
    coachOverall = coachOverallResult[0] if coachOverallResult else None

    return players, coachOverall


# assigns the role in linup, current implementation does not account for the coach overall
def assignRoles(players, coachOverall):
    roles = {}
    # makes everyone a reserve player to start off
    for player in players:
        roles[player[0]] = "Reserve"

    for position, counts in positionNumbers.items():
        # filter player by position
        positionPlayers = [player for player in players if player[2] == position]
        # sort players by overall, highest being first
        positionPlayers.sort(key=lambda x: x[1], reverse=True)

        # assign starters
        for i in range(counts["starters"]):
            if i < len(positionPlayers):
                roles[positionPlayers[i][0]] = "Starter"
        # assign subs
        for i in range(counts["starters"], counts["starters"] + counts["subs"]):
            if i < len(positionPlayers):
                roles[positionPlayers[i][0]] = "Substitute"

    return roles


# updates the linup table
def updateLineupTable(teamID, roles):
    for PlayerID, role in roles.items():
        cursor.execute(
            """
            INSERT INTO "Team Lineups" (TeamID, PlayerID, Role)
            VALUES (?, ?, ?)
            ON CONFLICT(TeamID, PlayerID) DO UPDATE SET
            Role = excluded.Role;
        """,
            (teamID, PlayerID, role),
        )
    conn.commit()


# main function to process all current teams
def processTeams():
    cursor.execute("SELECT DISTINCT TeamID FROM Teams;")
    teamIDs = [row[0] for row in cursor.fetchall()]

    for teamID in teamIDs:
        players, coachOverall = getTeamData(teamID)
        roles = assignRoles(players, coachOverall)
        updateLineupTable(teamID, roles)


processTeams()

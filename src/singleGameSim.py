# Basic Game Simulation

import sqlite3

# Database connection setup
conn = sqlite3.connect(
    "data/saveData/theDatabase.db"
)  # Update the path and connector as per your database
cursor = conn.cursor()


from gameLogic import Game, Player, Team

team_a_ID = "'tID8'"
team_b_ID = "'tID3'"


def get_players_for_team(teamID):
    query = f"SELECT PlayerID, Overall, Position FROM Players WHERE TeamID = {teamID}"
    cursor.execute(query)
    return [Player(row[0], row[1], row[2]) for row in cursor.fetchall()]


players_team_a = get_players_for_team(team_a_ID)
players_team_b = get_players_for_team(team_b_ID)

# Create an instance of the Team class for each team, passing their names
# and the player instances.
team_a = Team("Team A", players_team_a)
team_b = Team("Team B", players_team_b)

print(
    f"{team_a.name} Ratings: Ovr-{round((team_a.offensive_rating+team_a.defensive_rating+team_a.kicker_rating)/3)} Off-{round(team_a.offensive_rating)} Def-{round(team_a.defensive_rating)} Kicker-{round(team_a.kicker_rating)}"
)
print(
    f"{team_b.name} Ratings: Ovr-{round((team_b.offensive_rating+team_b.defensive_rating+team_b.kicker_rating)/3)} Off-{round(team_b.offensive_rating)} Def-{round(team_b.defensive_rating)} Kicker-{round(team_b.kicker_rating)}"
)

# Create an instance of the Game class using the two teams created above.
game = Game(team_a, team_b)
# Simulate the game to determine the scores.
game.simulateGame()

# Print the final score of Team A.
print(f"{team_a.name} Score: {team_a.score}")
# Print the final score of Team B.
print(f"{team_b.name} Score: {team_b.score}")
# Print final score in scoreboard form
game.scoreboard_display(team_a, team_b)

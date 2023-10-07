# Basic Game Simulation

from gameLogic import Game, Player, Team


players_team_a = [
    Player("Player A1", 75, "Quarterback"),
    Player("Player A2", 65, "Running Back"),
    Player("Player A3", 70, "Wide Receiver"),
    Player("Player A4", 60, "Kicker"),
    Player("Player A5", 40, "Linebacker"),
    Player("Player A6", 35, "Defensive Back"),
    Player("Player A7", 40, "Defensive Linemen"),
]
players_team_b = [
    Player("Player B1", 50, "Quarterback"),
    Player("Player B2", 45, "Running Back"),
    Player("Player B3", 55, "Wide Receiver"),
    Player("Player B4", 80, "Kicker"),
    Player("Player B5", 70, "Linebacker"),
    Player("Player B6", 75, "Defensive Back"),
    Player("Player B7", 85, "Defensive Linemen"),
]

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

# Basic Game Simulation

from gameLogic import Game, Player, Team


players_team_a = [
    Player("Player A1", 75),
    Player("Player A2", 65),
    Player("Player A3", 70),
]
players_team_b = [
    Player("Player B1", 50),
    Player("Player B2", 45),
    Player("Player B3", 55),
]

# Create an instance of the Team class for each team, passing their names
# and the player instances.
team_a = Team("Team A", players_team_a)
team_b = Team("Team B", players_team_b)

# Create an instance of the Game class using the two teams created above.
game = Game(team_a, team_b)
# Simulate the game to determine the scores.
game.simulate()

# Print the final score of Team A.
print(f"{team_a.name} Score: {team_a.score}")
# Print the final score of Team B.
print(f"{team_b.name} Score: {team_b.score}")

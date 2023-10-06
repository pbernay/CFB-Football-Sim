# Import the random module to generate random values for game simulation.
import random


# Define the Player class to represent an individual football player.
class Player:
    # Constructor for the Player class. Initializes a new player with a
    # given name and strength.
    def __init__(self, name, strength):
        self.name = name  # Assign the provided name to the player.
        self.strength = strength
        # Assign the provided strength value to the player.


# Define the Team class to represent a football team.
class Team:
    # Constructor for the Team class. Initializes a new team with a given name
    #  and a list of players.
    def __init__(self, name, players):
        self.name = name  # Assign the provided name to the team.
        self.players = players  # Assign the list of players to the team.
        self.score = 0  # Initialize the team's score to zero.

    # Property decorator to allow the method below to be accessed
    # as an attribute.
    @property
    def strength(self):
        # Calculate and return the average strength of all players in the team.
        return sum(player.strength for player in self.players) / len(self.players)


# Define the Game class to represent a football game between two teams.
class Game:
    # Constructor for the Game class. Initializes a new game
    # with two participating teams.
    def __init__(self, team1, team2):
        self.team1 = team1  # Assign the first provided team as team1.
        self.team2 = team2  # Assign the second provided team as team2.

    # Method to simulate the outcome of the game.
    def simulate(self):
        # Simulate the game quarter-by-quarter
        for _ in range(4):  # Assuming 4 quarters in a game
            # Team 1 scores
            if random.choices(
                [True, False], weights=[self.team1.strength, 100 - self.team1.strength]
            )[0]:
                self.team1.score += random.randint(0, 3) * 7

            # Team 2 scores
            if random.choices(
                [True, False], weights=[self.team2.strength, 100 - self.team2.strength]
            )[0]:
                self.team2.score += random.randint(0, 3) * 7


# Example usage:

# Create instances of the Player class for each player
# with their names and strengths.
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

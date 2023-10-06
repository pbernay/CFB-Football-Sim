# Where to place classes such as Player, Team, and Game
import random


# Define the Player class to represent an individual football player.
class Player:
    # Constructor for the Player class. Initializes a new player with a
    # given name, strength, position.
    def __init__(self, name, strength):
        self.name = name  # Assign the provided name to the player.
        self.strength = strength
        # Assign the provided strength value to the player.
        # self.position = position  # Assign a position


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

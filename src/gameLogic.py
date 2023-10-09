# Where to place classes such as Player, Team, and Game
import random

# Define a set of valid player positions
valid_positions = {
    "Offense": ["Quarterback", "Running Back", "Wide Receiver", "Offensive Linemen"],
    "Defense": ["Linebacker", "Defensive Back", "Defensive Linemen"],
    "Kicker": ["Kicker"],
    "Punter": ["Punter"],
}


# Define the Player class to represent an individual football player.
class Player:
    # Constructor for the Player class. Initializes a new player with a
    # given name, strength, position.
    def __init__(self, name, strength, position):
        self.name = name  # Assign the provided name to the player.
        self.strength = strength
        # Assign the provided strength value to the player.
        if position not in [
            pos for subcategory in valid_positions.values() for pos in subcategory
        ]:
            all_positions = ", ".join(
                [pos for subcategory in valid_positions.values() for pos in subcategory]
            )
            raise ValueError(
                f"Invalid position {position}. Must be one of {', '.join(all_positions)}"
            )
        self.position = position  # Assign a position


# Define the Team class to represent a football team.
class Team:
    # Constructor for the Team class. Initializes a new team with a given name
    #  and a list of players.
    def __init__(self, name, players):
        self.name = name  # Assign the provided name to the team.
        self.players = players  # Assign the list of players to the team.
        self.score = 0  # Initialize the team's score to zero.
        self.offensive_rating = self.strength("Offense")
        self.defensive_rating = self.strength("Defense")
        self.kicker_rating = self.strength("Kicker")

    def strength(self, category):
        relevant_players = [
            player
            for player in self.players
            if player.position in valid_positions[category]
        ]
        if not relevant_players:
            return 0
        # Calculate and return the average strength of all players in the team.
        return sum(player.strength for player in relevant_players) / len(
            relevant_players
        )


# Define the Game class to represent a football game between two teams.
class Game:
    # Constructor for the Game class. Initializes a new game
    # with two participating teams.
    def __init__(self, team1, team2):
        self.team1 = team1  # Assign the first provided team as team1.
        self.team2 = team2  # Assign the second provided team as team2.

    # Method to simulate the outcome of the game.
    def simulateGame(self):
        total_drives = 20

        teamOff = self.team1
        teamDef = self.team2

        for drive_number in range(total_drives):
            score = self.simulateDrive(teamOff, teamDef)
            if score > 0:
                print(
                    f"Drive {drive_number + 1}: {teamOff.name} scored {score} points!"
                )
            teamOff.score += score

            teamOff, teamDef = teamDef, teamOff
        # Creates an overtime period if both teams are tied at the end of regulation
        while teamOff.score == teamDef.score:
            print(f"Overtime Period:")
            total_drives = 4
            for drive_number in range(total_drives):
                score = self.simulateDrive(teamOff, teamDef)
                if score > 0:
                    print(
                        f"Drive {drive_number + 21}: {teamOff.name} scored {score} points!"
                    )
                teamOff.score += score

                teamOff, teamDef = teamDef, teamOff

    def simulateDrive(self, teamOff, teamDef):
        return self.simulateScoring(teamOff, teamDef)

    def simulateScoring(self, teamOff, teamDef):
        # Calculate probability of getting into a scoring position
        scoring_position_probability = teamOff.offensive_rating / (
            teamOff.offensive_rating + teamDef.defensive_rating
        )
        if random.random() < scoring_position_probability:
            outcome = random.choices(["td", "fg", "fd"], weights=[0.4, 0.4, 0.2])[0]

            if outcome == "td":
                if random.random() < (teamOff.kicker_rating)/101:
                    return 7
                else:
                    return 6
            elif outcome == "fg":
                if random.random() < (teamOff.kicker_rating)/101:
                    return 3
                else:
                    return 0
            else:
                return 0
        else:
            return 0

    def scoreboard_display(self, teamOff, teamDef):
        max_score_width = max(len(str(teamOff.score)), len(str(teamDef.score)))
        offscore = f"{teamOff.score:>{max_score_width}}"
        defscore = f"{teamDef.score:>{max_score_width}}"
        offNameLength = 18 - len(teamOff.name)
        defNameLength = 21 - len(teamDef.name)
        offNameLengthBottom = 16 - len(teamOff.name)
        offName = teamOff.name
        for _ in range(offNameLength):
            offName += " "
        defName = teamDef.name
        for _ in range(defNameLength):
            defName += " "
        offNameBottom = teamOff.name
        for _ in range(offNameLengthBottom):
            offNameBottom += " "
        print(" ___________________________________________________________________")
        print("/                             Scoreboard                            \\")
        print("|-------------------------------------------------------------------|")
        print("|                                                                   |")
        print("|     |  Qtr 1  |  Qtr 2  |  Qtr 3  |  Qtr 4  |  Total  |  Down  |  |")
        print("|-------------------------------------------------------------------|")
        print(
            f"| Home|                                            {offscore}               |"
        )
        print(
            f"| Away|                                            {defscore}               |"
        )
        print("|                                                                   |")
        print("|-------------------------------------------------------------------|")
        print(f"|                Time: 0:00              Possession: X              |")
        print("|-------------------------------------------------------------------|")
        print(f"|                Home: {offName}Away: {defName}|")
        print("|                                                                   |")
        print("|-------------------------------------------------------------------|")
        print(f"|                         Home of the {offNameBottom}              |")
        print("|___________________________________________________________________|")

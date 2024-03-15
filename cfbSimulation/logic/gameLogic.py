# Where to place classes such as Player, Team, and Game
import random

# Define a set of valid player positions - Will need to address the database names for positions
valid_positions = {
    "Offense": ["QB", "TE", "RB", "WR", "OT", "OG", "C"],
    "Defense": ["LB", "CB", "DE", "DT", "S"],
    "Kicker": ["K"],
    "Punter": ["P"],
}


# Define the Player class to represent an individual football player.
class Player:
    def __init__(
        self,
        PlayerID,
        Fname,
        Lname,
        Position,
        Overall,
        TeamID,
        Age,
        Year,
        InjuryType,
        InjuryDuration,
        Potential,
        PlayerStatus,
        Hometown,
        adjustedRating,
        role,
    ):
        self.PlayerID = PlayerID
        self.Fname = Fname
        self.Lname = Lname
        self.Position = Position
        self.Overall = Overall
        self.TeamID = TeamID
        self.Age = Age
        self.Year = Year
        self.InjuryType = InjuryType
        self.InjuryDuration = InjuryDuration
        self.Potential = Potential
        self.PlayerStatus = PlayerStatus
        self.Hometown = Hometown
        self.adjustedRating = adjustedRating
        self.role = role

    def calculate_strength(self):
        # Calculate the strength of the player based on their overall rating and potential.
        return (self.Overall + self.Potential) / 2


# Define the Team class to represent a football team.
class Team:
    def __init__(
        self, TeamID, name, wins, losses, ties, ConferenceID, CoachID, Location
    ):
        self.TeamID = TeamID
        self.name = name
        self.wins = wins
        self.losses = losses
        self.ties = ties
        self.ConferenceID = ConferenceID
        self.CoachID = CoachID
        self.Location = Location
        self.players = []
        self.OLAVG = 0
        self.DLAVG = 0
        self.KAVG = 0
        self.QBAVG = 0
        self.RBAVG = 0
        self.WRAVG = 0
        self.TEAVG = 0
        self.DBAVG = 0
        self.SAVG = 0
        self.LBAVG = 0
        self.DEAVG = 0
        self.DTAVG = 0
        self.PAVG = 0
        self.CAVG = 0
        self.OGAVG = 0
        self.OTAVG = 0
        self.OGCAVG = 0


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
                if random.random() < (teamOff.kicker_rating) / 101:
                    return 7
                else:
                    return 6
            elif outcome == "fg":
                if random.random() < (teamOff.kicker_rating) / 101:
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
        print("/                             Scoreboard                            \ ")
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

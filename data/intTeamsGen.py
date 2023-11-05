import csv
import random

used_locations = set()


def clearCSV():
    with open("saveData\players.csv", "w"):
        pass


clearCSV()

# sample data
numberOfTeams = 261
cities = []
states = []

with open("cities.txt", "r") as file:
    for line in file:
        city, state = line.strip().split(",")
        cities.append(city)
        cities.append(state)

with open("teamNames.txt", "r") as file:
    teamNames = [name.strip() for name in file.readlines()]

with open("cities.txt", "r") as file:
    locations = [city.strip() for city in file.readlines()]

filePath = "saveData\\teams.csv"


def uniqueLoc(locations):
    location = random.choice(locations)
    while location in used_locations:
        location = random.choice(locations)
    used_locations.add(location)
    return location


# Creates the csv
with open(filePath, "w", newline="") as file:
    writer = csv.writer(file)
    # Header
    writer.writerow(
        [
            "TeamID",
            "Team Name",
            "Wins",
            "Losses",
            "Ties",
            "ConferenceID",
            "CoachID",
            "Location",
        ]
    )

    # Sample Data
    for i in range(numberOfTeams):
        writer.writerow(
            [
                "tID" + str(i + 1),  # team ID
                random.choice(teamNames),  # team name
                0,  # Wins
                0,  # Losses
                0,  # Ties
                0,  # ConferenceID
                0,  # CoachID
                uniqueLoc(locations),
            ]
        )

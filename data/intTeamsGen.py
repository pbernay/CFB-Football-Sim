import csv
import random
import os

from src.utils import numberOfTeams

used_locations = set()


def clearCSV():
    # Correct relative path from the parent directory of 'intPlayerGen.py'
    directory = os.path.join("data", "saveData")
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Correct the path here as well
    with open(os.path.join(directory, "teams.csv"), "w"):
        pass


clearCSV()

# sample data
cities = []
states = []

script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
rel_path = "cities.txt"
abs_file_path = os.path.join(script_dir, rel_path)
with open(abs_file_path, "r") as file:
    for line in file:
        city, state = line.strip().split(",")
        cities.append(city)
        cities.append(state)

script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
rel_path = "teamNames.txt"
abs_file_path = os.path.join(script_dir, rel_path)
with open(abs_file_path, "r") as file:
    teamNames = [name.strip() for name in file.readlines()]

script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
rel_path = "cities.txt"
abs_file_path = os.path.join(script_dir, rel_path)
with open(abs_file_path, "r") as file:
    locations = [city.strip() for city in file.readlines()]

filePath = os.path.join("data", "saveData", "teams.csv")


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

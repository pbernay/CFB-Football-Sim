import csv
import os
import random


def clearCSV():
    # Correct relative path from the parent directory of 'intPlayerGen.py'
    directory = os.path.join("data", "saveData")
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Correct the path here as well
    with open(os.path.join(directory, "conferences.csv"), "w"):
        pass


clearCSV()

# sample data
numberOfConferences = 23

# grabs the conference names
script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
rel_path = "conferenceNames.txt"
abs_file_path = os.path.join(script_dir, rel_path)

with open(abs_file_path, "r") as file:
    conferenceNames = [name.strip() for name in file.readlines()]

save_directory = os.path.join(script_dir, "saveData")
if not os.path.exists(save_directory):
    os.makedirs(save_directory)

filePath = os.path.join(save_directory, "conferences.csv")

subdivisions = ["FBS"] * 10 + ["FCS"] * 13
random.shuffle(subdivisions)

# Creates the csv

with open(filePath, "w", newline="") as file:
    writer = csv.writer(file)
    # Header
    writer.writerow(["ConferenceID", "Conference Name", "Subdivision"])

    # Sample Data
    for i in range(numberOfConferences):
        writer.writerow(
            [
                "conID" + str(i + 1),  # ConferenceID
                random.choice(conferenceNames),  # Conference Name
                subdivisions[i],  # Subdivision
            ]
        )

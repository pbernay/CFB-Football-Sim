import csv
import random
import os


def clearCSV():
    # Correct relative path from the parent directory of 'intPlayerGen.py'
    directory = os.path.join("data", "saveData")
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Correct the path here as well
    with open(os.path.join(directory, "players.csv"), "w"):
        pass


clearCSV()

# Since your script is in the 'data' directory, the path to 'players.csv' should be directly to 'saveData'
filePath = os.path.join("data", "saveData", "players.csv")

# list of possible first names
script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
rel_path = "playerFirstNames.txt"
abs_file_path = os.path.join(script_dir, rel_path)
with open(abs_file_path, "r") as file:
    firstNames = [name.strip() for name in file.readlines()]

# list of possible last names
script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
rel_path = "playerLastNames.txt"
abs_file_path = os.path.join(script_dir, rel_path)
with open(abs_file_path, "r") as file:
    lastNames = [name.strip() for name in file.readlines()]

# list of possible hometowns
script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
rel_path = "cities.txt"
abs_file_path = os.path.join(script_dir, rel_path)
with open(abs_file_path, "r") as file:
    cities = [city.strip() for city in file.readlines()]

# list of possible positions
positions = [
    "QB",
    "RB",
    "WR",
    "TE",
    "OT",
    "OG",
    "C",
    "DE",
    "DT",
    "LB",
    "CB",
    "S",
    "K",
    "P",
]

# List of Possible Player Status
status = ["Recruit", "Current", "Graduated"]

# List of Possible Player Injuries
injuryTypes = {
    "Ankle Sprain": (0.20, (1, 3)),  # 20% chance, 1-3 games
    "Concussion": (0.10, (1, 6)),  # 10% chance, 1-6 games
    "Hamstring Strain": (0.15, (1, 4)),  # 15% chance, 1-4 games
    "ACL Tear": (0.05, (8, 12)),  # 5% chance, 8-12 games
    "MCL Sprain": (0.02, (3, 6)),  # 2% chance, 3-6 games
    "Meniscus Tear": (0.04, (4, 8)),  # 4% chance, 4-8 games
    "Groin Pull": (0.08, (1, 3)),  # 8% chance, 1-3 games
    "Shoulder Dislocation": (0.07, (2, 6)),  # 7% chance, 2-6 games
    "Achilles Tendonitis": (0.03, (3, 5)),  # 3% chance, 3-5 games
    "Turf Toe": (0.06, (2, 4)),  # 6% chance, 2-4 games
    "Quadriceps Strain": (0.07, (1, 3)),  # 7% chance, 1-3 games
    "Shin Splints": (0.04, (1, 3)),  # 4% chance, 1-3 games
    "Calf Strain": (0.06, (1, 3)),  # 6% chance, 1-3 games
    "Hip Flexor Strain": (0.05, (1, 4)),  # 5% chance, 1-4 games
    "Patellar Tendinitis": (0.03, (2, 4)),  # 3% chance, 2-4 games
    "Bicep Tendonitis": (0.02, (2, 4)),  # 2% chance, 2-4 games
    "Rotator Cuff Tear": (0.02, (4, 8)),  # 2% chance, 4-8 games
    "Fractured Clavicle": (0.01, (6, 10)),  # 1% chance, 6-10 games
    "Herniated Disc": (0.01, (4, 8)),  # 1% chance, 4-8 games
    "Pectoral Tear": (0.01, (5, 10)),  # 1% chance, 5-10 games
    "Plantar Fasciitis": (0.02, (3, 5)),  # 2% chance, 3-5 games
    "Elbow Dislocation": (0.01, (3, 6)),  # 1% chance, 3-6 games
    "Hand Fracture": (0.02, (2, 6)),  # 2% chance, 2-6 games
    "Neck Strain": (0.02, (1, 3)),  # 2% chance, 1-3 games
    "Lumbar Strain": (0.03, (2, 5)),  # 3% chance, 2-5 games
    "Disciplinary Suspension": (0.05, (1, 16)),  # 5% chance, 1-16 games
}


# generates the age and class while some ages more common
# binds age with class (so there is not an 18yo college senior)
def ageClass():
    ages = [18, 19, 20, 21, 22, 23, 24]
    weights = [0.1, 0.3, 0.3, 0.15, 0.05, 0.075, 0.025]
    age = random.choices(ages, weights, k=1)[0]

    if age == 18:
        classYear = "Freshman"
    elif age == 19:
        classYear = "Sophomore"
    elif age == 20:
        classYear = "Junior"
    else:
        classYear = "Senior"

    return age, classYear


# creates a weighted overall rating toward favoring lower ratings
def weightOverall():
    ratings = list(range(40, 101))

    weights = [
        0.1  # 10% 40-50
        if r <= 50
        else 0.3  # 30% 50-60
        if r <= 60
        else 0.3  # 30% 60-70
        if r <= 70
        else 0.2  # 20% 70-80
        if r <= 80
        else 0.1  # 10% 80-100
        for r in ratings
    ]

    # changes overall based on age
    if age <= 19:
        # half as likely to get an overall over 60
        adjustment = [0.5 if r > 60 else 1 for r in ratings]
    elif age == 20:
        # half as likely to get an overall over 75
        adjustment = [0.5 if r > 75 else 1 for r in ratings]
    else:
        adjustment = [1 for r in ratings]

    # applys the adjustment to the weights
    adjAgeWeights = [base * adj for base, adj in zip(weights, adjustment)]

    # normalize the weights so they can add to 1
    ttlWeights = sum(adjAgeWeights)
    normalizedWeights = [w / ttlWeights for w in adjAgeWeights]

    overall = random.choices(ratings, normalizedWeights, k=1)[0]
    return overall


def weightPotential():
    potentials = list(range(40, 101))

    weights = [
        0.1  # 10% 40-50
        if p <= 50
        else 0.3  # 30% 50-60
        if p <= 60
        else 0.3  # 30% 60-70
        if p <= 70
        else 0.2  # 20% 70-80
        if p <= 80
        else 0.1  # 10% 80-100
        for p in potentials
    ]
    potential = random.choices(potentials, weights, k=1)[0]
    return potential


# picks a random injury based on the injury types and probabilities
def injuryType():
    injuryTypeCondition = list(injuryTypes.keys())
    probs = [condition[0] for condition in injuryTypes.values()]
    randomCondition = random.choices(injuryTypeCondition, weights=probs)
    return randomCondition


# picks a random injury duration based on the injury type
def injuryDuration(injury):
    if injury == "N/A":
        return 0  # If there's no injury, the duration is 0
    duration_range = injuryTypes[injury][1]
    return random.randint(duration_range[0], duration_range[1])


# Creates the csv
with open(filePath, "w", newline="") as file:
    writer = csv.writer(file)
    # Header
    writer.writerow(
        [
            "PlayerID",
            "Fname",
            "Lname",
            "Position",
            "Overall",
            "TeamID",
            "Age",
            "Year",
            "InjuryType",
            "InjuryDuration",
            "Potential",
            "PlayerStatus",
            "Hometown",
        ]
    )

    # Sample Data
    for i in range(13050):
        age, classYear = ageClass()
        overall = weightOverall()
        potential = weightPotential()
        injury = injuryType()[
            0
        ]  # Get the first item from the list returned by injuryType
        injury_duration = injuryDuration(injury)

        writer.writerow(
            [
                "pID" + str(i + 1),  # player ID
                random.choice(firstNames),  # first name
                random.choice(lastNames),  # last name
                random.choice(positions),  # position
                overall,  # overall
                (i % 261) + 1,  # team
                age,  # age
                classYear,  # class/year
                "",  # injurytype
                "",  # injuryDuration
                potential,  # potential rating
                "Current",  # PlayerStatus
                random.choice(cities),  # hometown
            ]
        )

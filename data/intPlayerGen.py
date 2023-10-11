import csv
import random

# list of possible first names
with open("playerFirstNames.txt", "r") as file:
    firstNames = [name.strip() for name in file.readlines()]

# list of possible last names
with open("playerLastNames.txt", "r") as file:
    lastNames = [name.strip() for name in file.readlines()]

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


# File path please edit for what you need to generate
filePath = "saveData\players.csv"

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
            "InjuryStatus",
            "Potential",
        ]
    )

    # Sample Data
    for i in range(12500):
        age, classYear = ageClass()
        overall = weightOverall()
        potential = weightPotential()

        writer.writerow(
            [
                "pID" + str(i + 1),  # player ID
                random.choice(firstNames),  # first name
                random.choice(lastNames),  # last name
                random.choice(positions),  # position
                overall,  # overall
                (i % 128) + 1,  # team
                age,  # age
                classYear,  # class/year
                random.choices([0, 1], [0.995, 0.005], k=1)[0],  # injury
                potential,  # potential
            ]
        )

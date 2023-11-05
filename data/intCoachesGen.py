import csv
import random


def clearCSV():
    with open("saveData\coaches.csv", "w"):
        pass


clearCSV()


# list of possible first names
with open("coachFirstNames.txt", "r") as file:
    firstNames = [name.strip() for name in file.readlines()]

# list of possible last names
with open("coachLastNames.txt", "r") as file:
    lastNames = [name.strip() for name in file.readlines()]


# weights the ages to make them more normal
def weightAge():
    ages = list(range(25, 75))

    weights = [
        0.1
        if a <= 32
        else 0.3
        if a <= 40
        else 0.3
        if a <= 50
        else 0.2
        if a <= 60
        else 0.1
        for a in ages
    ]

    age = random.choices(ages, weights, k=1)[0]
    return age


# weights the years of exp to make them normal
def weightExp():
    # makes a max exp that a person can have based on their age
    maxExp = age - 25 if age > 25 else 0
    exp = list(range(0, maxExp + 1))

    weights = [
        0.4
        if e <= 2
        else 0.3
        if e <= 5
        else 0.2
        if e <= 9
        else 0.075
        if e <= 20
        else 0.025
        for e in exp
    ]

    exp = random.choices(exp, weights, k=1)[0]
    return exp


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
    # changes overall based on exp
    if yearsOfExp <= 5:
        # half as likely to get an overall over 60
        adjustment = [0.5 if r > 60 else 1 for r in ratings]
    elif yearsOfExp == 10:
        # half as likely to get an overall over 75
        adjustment = [0.5 if r > 75 else 1 for r in ratings]
    else:
        adjustment = [1 for r in ratings]

    # applys the adjustment to the weights
    adjExpWeights = [base * adj for base, adj in zip(weights, adjustment)]

    # normalize the weights so they can add to 1
    ttlWeights = sum(adjExpWeights)
    normalizedWeights = [w / ttlWeights for w in adjExpWeights]

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
filePath = "saveData\coaches.csv"

# Creates the csv
with open(filePath, "w", newline="") as file:
    writer = csv.writer(file)
    # Header
    writer.writerow(
        [
            "CoachID",
            "Fname",
            "Lname",
            "Years Of Exp",
            "Overall",
            "Age",
            "Potential",
        ]
    )

    # Sample Data
    for i in range(261):
        age = weightAge()
        yearsOfExp = weightExp()
        overall = weightOverall()
        potential = weightPotential()

        writer.writerow(
            [
                "cID" + str(i + 1),  # coach ID
                random.choice(firstNames),  # first name
                random.choice(lastNames),  # last name
                yearsOfExp,  # Years of exp
                overall,  # overall
                age,  # age
                potential,  # potential
            ]
        )

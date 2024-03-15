# helper functions or constants

# Number of initial teams
numberOfTeams = 261


# Calculates the number of initial players to generate
def calcNumberOfIntPlayers():
    numberOfIntPlayers = numberOfTeams * 64
    return numberOfIntPlayers


# Global player count
globalPlayerCount = 0


def incrementPlayerCount():
    global globalPlayerCount
    globalPlayerCount += 1
    return globalPlayerCount


def getPlayerCount():
    return globalPlayerCount


# Number of starters and subs per team
# Specific numbers for starters and subs for each position
positionNumbers = {
    'QB': {"starters": 1, "subs": 0},
    'RB': {"starters": 1, "subs": 1},
    'WR': {"starters": 1, "subs": 2},
    'TE': {"starters": 1, "subs": 1},
    'OT': {"starters": 2, "subs": 0},
    'OG': {"starters": 2, "subs": 0},
    'C': {"starters": 1, "subs": 0},
    'DE': {"starters": 2, "subs": 0},
    'DT': {"starters": 2, "subs": 0},
    'LB': {"starters": 3, "subs": 0},
    'CB': {"starters": 2, "subs": 1},
    'S': {"starters": 2, "subs": 0},
    'K': {"starters": 1, "subs": 0},
    'P': {"starters": 1, "subs": 0},
}

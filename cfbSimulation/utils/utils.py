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
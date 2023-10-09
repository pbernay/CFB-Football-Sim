def main_menu():
    print("Main Menu:")
    print("1) Quick Play") # aka single game mode
    print("2) Career Mode") # aka coach mode
    print("3) Season Mode")
    print("4) Settings")
    print("5) Quit")

def quickPlay():
    print("Quick Play:")
    #Quick play code

def careerMode():
    print("Career Mode:")
    #Career mode code

def seasonMode():
    print("Season Mode:")
    #Season mode code

def settingsMenu():
    print("Settings:")
    #Settings menu code

while True:
    main_menu()

    choice = input()

    if choice == '1':
        quickPlay()
    elif choice == '2':
        careerMode()
    elif choice == '3':
        seasonMode()
    elif choice == '4':
        settingsMenu()
    elif choice == '5':
        print("Exiting Game")
        break
    else:
        print("Invalid choice. Please try again")
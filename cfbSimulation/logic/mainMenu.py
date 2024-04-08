import pygame
import sys

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BRIGHT_GREEN = (50, 255, 50)

# Setup display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("CFB Football Sim")


def draw_button(message, x, y, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    if x + BUTTON_WIDTH > mouse[0] > x and y + BUTTON_HEIGHT > mouse[1] > y:
        pygame.draw.rect(screen, BRIGHT_GREEN, (x, y, BUTTON_WIDTH, BUTTON_HEIGHT))
        if click[0] == 1 and action != None:
            action()
    else:
        pygame.draw.rect(screen, GREEN, (x, y, BUTTON_WIDTH, BUTTON_HEIGHT))

    font = pygame.font.SysFont(None, 35)
    text = font.render(message, True, WHITE)
    screen.blit(
        text,
        (
            x + (BUTTON_WIDTH - text.get_width()) // 2,
            y + (BUTTON_HEIGHT - text.get_height()) // 2,
        ),
    )

def draw_image_button(image, x, y, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    if x + BUTTON_WIDTH > mouse[0] > x and y + BUTTON_HEIGHT > mouse[1] > y:
        if click[0] == 1 and action != None:
            action()
    screen.blit(image, (x, y))

def quit_game():
    pygame.quit()
    sys.exit()

def settings():
    # Coordinates for exit button
    x_exit = SCREEN_WIDTH / 2 - BUTTON_WIDTH / 2
    y_exit = SCREEN_HEIGHT / 2
    # Settings menu loop
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        screen.fill(WHITE)
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        # If exit button is clicked return out of stack to avoid overflow and repeated nested calls
        if x_exit + BUTTON_WIDTH > mouse[0] > x_exit and y_exit + BUTTON_HEIGHT > mouse[1] > y_exit:
            if click[0] == 1:
                # Delay so that button is not pressed on main menu
                pygame.time.delay(85)
                return False
        # Draws menu button but will never use action parameter to avoid never ending nested loops
        draw_button("Back", x_exit, y_exit, main_menu)
        pygame.display.update()
        print("Settings Opened!")

def start_game():
    print("Game Started!")
    # Add logic to start the game


def main_menu():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill(WHITE)
        ## Potential background image
        # background = pygame.image.load("../../assets/background.jpg")
        # background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        # screen.blit(background, (0, 0))

        draw_button(
            "Start Game",
            SCREEN_WIDTH / 2 - BUTTON_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            start_game,
        )
        draw_image_button(pygame.image.load("../../assets/exit.png"), SCREEN_WIDTH / 2 - BUTTON_WIDTH / 2, SCREEN_HEIGHT / 2 + 200, quit_game)
        draw_image_button(pygame.image.load("../../assets/settings.png"), SCREEN_WIDTH / 2 - BUTTON_WIDTH / 2, SCREEN_HEIGHT / 2 + 100, settings)


        pygame.display.update()


main_menu()

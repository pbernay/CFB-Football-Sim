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

        draw_button(
            "Start Game",
            SCREEN_WIDTH / 2 - BUTTON_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            start_game,
        )

        pygame.display.update()


main_menu()

import sys

import pygame
import pygame_menu

from settings import *
from logics import Controller, TestController

from helpers import get_random_rgb_tuple
from exceptions import GameOverException

# Создаем игру и окно
pygame.init()
pygame.mixer.init()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Snake Game")
clock = pygame.time.Clock()

current_snake_color = None


def start_game(**kwargs):
    """Функция для старта игры."""

    # Главный контроллер
    controller = Controller(window, **kwargs)

    # Цикл игры
    while True:
        # Держим цикл на правильной скорости
        clock.tick(FPS)
        try:
            # Обновление
            controller.update()
            # После отрисовки всего, переворачиваем экран
            pygame.display.flip()
        except GameOverException as e:
            game_over_message = str(e)
            break

        if not controller.is_running:
            sys.exit()

    menu_after_dead(game_over_message)


def play_button_handler(new_snake_color=None):
    """Обработчик кнопки Play в меню."""
    global current_snake_color
    if new_snake_color:
        current_snake_color = new_snake_color

    start_game(snake_color=current_snake_color)


def menu_after_dead(game_over_message):
    """Показ меню после гибели в игре."""
    end_menu = pygame_menu.Menu('Snake Game', WINDOW_WIDTH, WINDOW_HEIGHT,
                                theme=pygame_menu.themes.THEME_DARK)
    end_menu.add.label(game_over_message, margin=(0, 50))
    end_menu.add.button('Play again', play_button_handler)
    end_menu.mainloop(window)


def get_start_menu():
    """Функция для отображения стартового меню."""

    menu = pygame_menu.Menu('Snake Game', WINDOW_WIDTH, WINDOW_HEIGHT,
                            theme=pygame_menu.themes.THEME_DARK)
    menu.add.text_input('Name: ', default='Player')

    color_input = menu.add.color_input('Color: ', 'rgb')
    change_color_button = menu.add.button(
        'Randomize color',
        lambda: color_input.set_value(get_random_rgb_tuple()),
        margin=(0, 50)
    )
    change_color_button.apply()

    menu.add.button('Play', lambda: play_button_handler(
        new_snake_color=color_input.get_value(),
    ))
    menu.add.button('Quit', pygame_menu.events.EXIT)

    menu.mainloop(window)


if __name__ == '__main__':
    get_start_menu()

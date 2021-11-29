import sys

import pygame
import pygame_menu

from settings import *
from logics import Controller, TestController

from helpers import get_random_rgb_tuple

# Создаем игру и окно
pygame.init()
pygame.mixer.init()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Snake Game")
clock = pygame.time.Clock()


def start_game(**kwargs):
    """Функция для старта игры."""

    # Главный контроллер
    controller = Controller(window, **kwargs)

    # Цикл игры
    while controller.is_running:
        # Держим цикл на правильной скорости
        clock.tick(FPS)
        # Обновление
        controller.update()
        # После отрисовки всего, переворачиваем экран
        pygame.display.flip()
    sys.exit()


def get_menu():
    """Функция для отображения стартового меню."""

    menu = pygame_menu.Menu('Snake Game', WINDOW_WIDTH, WINDOW_HEIGHT,
                            theme=pygame_menu.themes.THEME_DARK)
    menu.add.text_input('Name: ', default='Player')
    difficulty_selector = menu.add.selector(
        'Difficulty: ', [('Easy', 1), ('Hard', 2)], onchange=lambda: None)
    # TODO: раскомментировать после реализации сложности
    difficulty_selector.hide()

    color_input = menu.add.color_input('Color: ', 'rgb')
    change_color_button = menu.add.button(
        'Change color',
        lambda: color_input.set_value(get_random_rgb_tuple()),
        margin=(0, 50)
    )
    change_color_button.apply()

    menu.add.button('Play', lambda: start_game(
        snake_color=color_input.get_value()))
    menu.add.button('Quit', pygame_menu.events.EXIT)

    menu.mainloop(window)


if __name__ == '__main__':
    get_menu()

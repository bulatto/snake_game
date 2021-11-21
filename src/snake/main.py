import pygame

from settings import *
from logics import Controller, TestController


# Создаем игру и окно
pygame.init()
pygame.mixer.init()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Snake")
clock = pygame.time.Clock()

# Главный контроллер
controller = Controller(window)

# Цикл игры
while controller.is_running:
    # Держим цикл на правильной скорости
    clock.tick(FPS)
    # Обновление
    controller.update()
    # После отрисовки всего, переворачиваем экран
    pygame.display.flip()

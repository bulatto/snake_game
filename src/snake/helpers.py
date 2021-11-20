import math
import random
from collections import namedtuple

import pygame

from settings import *


def get_points_distance(x1, y1, x2, y2):
    """Возвращает расстояние между точками."""
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def get_sign(num):
    """Определяет знак числа (1 - положительный, -1 - отрицательный, 0 - ноль"""
    return int(num // abs(num)) if num else 0


def get_angle_of_points(x, y, px, py):
    """Получение угла до точки горизонтального луча вправо от точки (x,y)."""
    dx = px - x
    dy = py - y
    if not dx:
        return 90 if dy >= 0 else 270
    angle = math.degrees(math.atan(abs(dy / dx)))
    if dx <= 0:
        angle = 180 - angle if dy >= 0 else 180 + angle
    else:
        if dy < 0:
            angle = 360 - angle
    return angle


def calculate_angle_to_point(x, y, pos_x, pos_y, current_angle):
    """
    Вычисление угла, на который надо повернуть при движении из одной точки
    в другую.
    """
    point_angle = get_angle_of_points(x, y, pos_x, pos_y)
    delta = point_angle - current_angle
    angle_diff = min((delta, delta - 360 * (current_angle <= point_angle)), key=abs)
    # TODO: если 180 градусов, то продолжать движение в том же направлении
    return angle_diff


def get_new_point_pos(x, y, angle, distance):
    """Получение координат новой точки на определенном угле и дистанции."""
    return (x + distance * math.cos(math.radians(angle)),
            y + distance * math.sin(math.radians(angle)))


def normalize_angle(angle):
    """Нормализация угла (чтобы был от 0 до 360)."""
    angle = angle % 360
    if angle < 0:
        angle = 360 - angle
    return angle


def get_random_pos(coef=0.1):
    """Получение случайных координат.

    Коэффицент нужен для отдаления от краев экрана.
    """
    assert coef < 0.5
    return (
        random.randint(WIDTH * coef, WIDTH * (1 - coef)),
        random.randint(HEIGHT * coef, HEIGHT * (1 - coef))
    )


class DirectionEnum:
    """Описание направлений"""

    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'
    NOTHING = 'nothing'

    LEFT_RIGHT = (LEFT, RIGHT)
    UP_DOWN = (UP, DOWN)

    sign_mapping = {LEFT: -1, UP: -1, DOWN: 1, RIGHT: 1}

    # Маппинг кнопок клавиатуры и направлений
    from_buttons_mapping = {
        pygame.K_LEFT: LEFT,
        pygame.K_RIGHT: RIGHT,
        pygame.K_UP: UP,
        pygame.K_DOWN: DOWN,
    }

    @classmethod
    def get_from_button(cls, key):
        return cls.from_buttons_mapping[key]


DE = DirectionEnum

# Маппинг нажатых клавиш и коэффициентов для увеличенение/уменьшения координат
KEY_SIGN_MAPPING = {
    pygame.K_LEFT: -1,
    pygame.K_UP: -1,
    pygame.K_RIGHT: 1,
    pygame.K_DOWN: 1
}

# Кнопки управления
LEFT_RIGHT_BUTTONS = (pygame.K_LEFT, pygame.K_RIGHT)
DIRECTIONS_BUTTONS = (*LEFT_RIGHT_BUTTONS, pygame.K_UP, pygame.K_DOWN)

# Прямоугольник с игровым полем
GameRect = pygame.Rect(0, 0, WIDTH, HEIGHT)

# namedtuple для хранения крайних координат
Coordinates = namedtuple('Coordinates', ['left', 'right', 'top', 'bottom'])

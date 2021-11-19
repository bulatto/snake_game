import datetime
import random
import sys

import pygame

from settings import *
from helpers import *
from base_classes import Circle, ObjectsContainer, BaseSnake, BaseController


class Food(Circle):
    """Класс еды."""
    color = (222, 205, 245)
    radius = 5

    def __init__(self, food_id, win, **kwargs):
        kwargs.setdefault('pos', get_random_pos(0.05))
        super().__init__(win, **kwargs)
        self.id = food_id

    def __repr__(self):
        return f'Food(x={self.x},y={self.y})'


class FoodContainer(ObjectsContainer):
    """Контейнер для еды."""
    obj_class = Food

    def get_eaten_food(self, snake_head):
        """Список съеденной еды."""
        return [
            food for food in self.objects.values()
            if food.get_distance_to_circle(snake_head) < (
               snake_head.radius + food.radius)
        ]

    def update_eaten_food(self, eaten_food):
        """Удаление съеденной еды и добавление новой."""
        count = len(eaten_food)
        for food in eaten_food:
            self.delete_by_id(food.id)
            self.add(1)
        return count

    def update(self, snake_head):
        eaten_food = self.get_eaten_food(snake_head)
        snake_food_count = self.update_eaten_food(eaten_food)
        return snake_food_count

    def get_nearest_food(self, rect, point, by_coordinates=False):
        """Поиск ближайшей еды."""
        # TODO: реализовать функцию по другому
        if by_coordinates:
            return min(
                self.objects.values(),
                key=lambda f: get_points_distance(*point, *f.xy)
            )

        food_in_rect = [
            f for f in self.objects.values() if rect.collidepoint(f.xy)]
        if food_in_rect:
            return min(
                food_in_rect,
                key=lambda f: get_points_distance(*point, *f.xy)
            )

    def get_next_food(self):
        """Возвращение первой попавшейся еды."""
        return next(iter(self.objects.values()), None)


class Snake(BaseSnake):
    """Обычная змея."""

    color = (255, 192, 203)
    head_color = (255, 192, 203)
    default_start_pos = (WIDTH / 2, HEIGHT / 2)


class BotSnake(BaseSnake):
    """Змея, управляемая компьютером"""

    color = (64, 255, 108)
    head_color = (60, 255, 113)
    default_start_pos = (100, 100)

    def __init__(self, snake_id, win, food_container, **kwargs):
        kwargs.setdefault('start_pos', get_random_pos())
        super().__init__(snake_id, win, **kwargs)
        self.current_food = None
        self.food_container = food_container
        self.angle_different = 0

        self.food_datetime = None

    def go_to_point(self, pos_x, pos_y):
        """Расчёт для перемещения в заданную точку."""
        angle_diff = calculate_angle_to_point(
            *self.head_xy, pos_x, pos_y, self.angle)

        self.set_turning(DE.RIGHT if angle_diff >= 0 else DE.LEFT)
        turning_angle = (
            self.turning_angle if abs(angle_diff) > self.max_turning_angle
            else angle_diff
        )
        self.change_angle(turning_angle)

    def has_to_find_food(self, food_count):
        """Проверяет необходимости выбора другой еды."""
        return (
            food_count or
            not self.current_food or
            not self.food_container.has_object(self.current_food.id) or
            not self.food_datetime or
            not datetime.datetime.now() - self.food_datetime <=
                datetime.timedelta(seconds=1)
        )

    def update(self, food_count):
        if self.has_to_find_food(food_count):
            for delta_angle in (0, 90, 180, 270):
                near_food = self.food_container.get_nearest_food(
                    self.get_rectangle(delta_angle), self.head_xy)
                if near_food:
                    self.current_food = near_food
                    self.food_datetime = datetime.datetime.now()
                    break

        if self.current_food:
            pygame.draw.line(self.win, GREEN, self.head_xy, self.current_food.xy, 1)

        if not all(GameRect.collidepoint(*c.xy) for c in self.circles):
            self.go_to_point(WIDTH / 2,  HEIGHT / 2)
        else:
            self.go_to_point(*self.current_food.xy)
        self.move()
        if food_count:
            self.add_tail(food_count)


class SnakeContainer(ObjectsContainer):
    """Контейнер для змей."""
    obj_class = Food

    def __init__(self, food_container, win, count=0):
        super().__init__(win, count)
        self.food_container = food_container
        self.main_snake_id = None

    @property
    def main_snake(self):
        """Змея игрока."""
        if not self.main_snake_id:
            raise Exception('Главная змея не найдена')
        return self.objects[self.main_snake_id]

    def get_snake_generator(self, only_bots=False):
        """Генератор для перебора змей."""
        return (snake for k, snake in self.objects.items()
                if not only_bots or k != self.main_snake_id)

    @property
    def all_snakes(self):
        return list(self.get_snake_generator())

    @property
    def bot_snakes(self):
        return list(self.get_snake_generator(only_bots=True))

    def create_bot_snake(self, **kwargs):
        """Создание змеи - бота"""
        bot = BotSnake(self.get_id(), self.win, self.food_container, **kwargs)
        self.add_obj(bot)
        return bot.id

    def create_main_snake(self, **snake_params):
        """Создание змеи игрока"""
        snake = Snake(self.get_id(), self.win, **snake_params)
        self.add_obj(snake)
        self.main_snake_id = snake.id
        return snake

    def snake_is_dead(self, snake):
        """Смерть змеи."""
        snake.is_alive = False
        self.delete_by_id(snake.id)


class GameLogic:
    """Класс с игровой логикой."""

    def __init__(self, win):
        self.win = win

        self.bot_snakes = []
        self.food_container = FoodContainer(self.win, count=100)
        self.snake_container = SnakeContainer(self.food_container, self.win)
        self.snake = self.snake_container.create_main_snake()

        for one_pos in (100, 300, 500, 700):
            self.snake_container.create_bot_snake(start_pos=(one_pos, one_pos))

    def get_snakes(self, only_bots=False, only_alive=True):
        """Получение списка змей."""
        snakes = (self.snake_container.bot_snakes if only_bots
                   else self.snake_container.all_snakes)
        if only_alive:
            snakes = [snake for snake in snakes if snake.is_alive]
        return snakes

    def snake_is_dead(self, snake):
        """Отработка гибели змеи."""
        if snake is self.snake:
            print('Игра закончена')
            sys.exit()
        else:
            self.snake_container.snake_is_dead(snake)
            for circle in snake.circles:
                self.food_container.add_new_obj(pos=circle.xy)
            self.snake_container.create_bot_snake()

    def check_collisions(self):
        """Проверка коллизий."""
        snakes_was_updated = False

        for snake in self.get_snakes():
            snake_food_count = self.food_container.update(snake.head)
            snake.update(food_count=snake_food_count)

            for other_snake in self.get_snakes():
                collision = snake.find_collision_with_other_snake(
                    other_snake, exclude_self=True)
                if collision is not None:
                    self.snake_is_dead(snake)
                    snakes_was_updated = True

        if snakes_was_updated:
            self.check_collisions()

    def draw(self):
        """Отрисовка всего."""
        self.food_container.draw()
        for snake in self.get_snakes():
            snake.draw()


class Controller(BaseController):
    """Контроллер."""

    background_color = (248, 241, 255)

    def __init__(self, win):
        super().__init__(win)
        self.game = GameLogic(self.win)
        self.snake = self.game.snake

    def handle_event(self, event):
        # Проверка зажатия клавиши
        if event.type == pygame.KEYDOWN:
            if event.key in LEFT_RIGHT_BUTTONS:
                self.snake.set_turning(DE.get_from_button(event.key))
        # Проверка отжатия клавиши
        elif event.type == pygame.KEYUP:
            if event.key in LEFT_RIGHT_BUTTONS:
                self.snake.set_turning(None)

    def update(self):
        super().update()
        self.game.check_collisions()
        self.game.draw()


class TestController(BaseController):
    """Тестовый контроллер для проверки отдельных элементов."""
    center_xy = (WIDTH // 2, HEIGHT // 2)

    def update(self):
        super().update()

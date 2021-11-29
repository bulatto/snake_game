import datetime
import random
import sys
from functools import partial

import pygame

from settings import *
from helpers import *
from base_classes import Circle, ObjectsContainer, BaseSnake, BaseController


class Food(Circle):
    """Класс еды."""
    color = PURPLE
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
    # Коэффицент для соотношения угла поворота и дистанции для поиска еды
    ANGLE_TO_DISTANCE_COEF = 1
    max_food_count = MAX_FOOD_COUNT

    def add_obj(self, obj, force=False):
        if force or len(self.objects) < self.max_food_count:
            return super().add_obj(obj)
        return False

    def add_new_obj(self, force=False, **kwargs):
        obj = self.get_new_obj(**kwargs)
        result = self.add_obj(obj, force)
        return obj if result else None

    def get_eaten_food(self, snake_head):
        """Список съеденной еды."""
        return [
            food for food in self.objects.values()
            if abs(food.x - snake_head.x) <= snake_head.radius + food.radius and
               abs(food.y - snake_head.y) <= snake_head.radius + food.radius and
               food.get_distance_to_circle(snake_head) < (
               snake_head.radius + food.radius)
        ]

    def update_eaten_food(self, eaten_food):
        """Удаление съеденной еды и добавление новой."""
        count = len(eaten_food)
        for food in eaten_food:
            self.delete_by_id(food.id)
            self.add_new_obj()
        return count

    def update(self, snake_head):
        eaten_food = self.get_eaten_food(snake_head)
        snake_food_count = self.update_eaten_food(eaten_food)
        return snake_food_count

    def _get_food_priority_coef(self, point, current_angle, food):
        """Вычисление коэффицента для определения удобной еды. Меньше-лучше."""
        angle_to_rotate = calculate_angle_to_point(
            *point, *food.xy, current_angle)
        distance = get_points_distance(*point, *food.xy)
        return abs(angle_to_rotate) * self.ANGLE_TO_DISTANCE_COEF + distance

    def get_nearest_food(self, point, current_angle):
        """Поиск ближайшей еды по параметрами."""
        if not self.objects:
            return None
        key_func = partial(self._get_food_priority_coef, point, current_angle)
        return min(self.objects.values(), key=key_func)

    def get_next_food(self):
        """Возвращение первой попавшейся еды."""
        return next(iter(self.objects.values()), None)


class Snake(BaseSnake):
    """Обычная змея."""

    default_color = (255, 192, 203)
    default_start_pos = (WIDTH / 2, HEIGHT / 2)


class BotSnake(BaseSnake):
    """Змея, управляемая компьютером"""

    default_color = (64, 255, 108)
    default_start_pos = (100, 100)
    # Определение времени до смены еды, если еда не была сьедена за это время
    food_delta_seconds = 1
    # Рисовать линию до еды и линию для избегания других змей
    draw_food_path = DRAW_FOOD_PATH
    draw_collision_avoiding_lines = DRAW_COLLISION_AVOIDING_LINES

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

    def is_food_expired(self):
        """Проверяет, испортилась ли еда"""
        return (
            not self.food_datetime or
            not datetime.datetime.now() - self.food_datetime <=
                datetime.timedelta(seconds=self.food_delta_seconds)
        )

    def has_to_find_food(self, food_count):
        """Проверяет необходимости выбора другой еды."""
        return (
            food_count or
            not self.current_food or
            not self.food_container.has_object(self.current_food.id) or
            self.is_food_expired()
        )

    def find_new_food(self):
        """Нахождение новой еды."""
        self.current_food = self.food_container.get_nearest_food(
            self.head_xy, self.angle)
        self.food_datetime = datetime.datetime.now()

    def draw_food_line(self):
        """Рисование линии до еды"""
        if self.current_food and self.draw_food_path:
            self.draw_line_from_head(self.current_food.xy, PURPLE)

    def avoid_collision(self, is_collide_snakes_rectangles):
        """Избегание выхода за карту и избегание других змей."""
        normal_angles = set()
        for delta in (0, -45, -90, 45, 90):
            new_pos = self.get_new_position_from_head(self.angle + delta, 50)
            is_normal = (
                not is_collide_snakes_rectangles(new_pos, exclude_snake=self)
                and GameRect.collidepoint(*new_pos)
            )
            if is_normal:
                normal_angles.add(delta)
            if self.draw_collision_avoiding_lines:
                color = GREEN if is_normal else RED
                self.draw_line_from_head(new_pos, color)

        # Обработка ситуаций, когда сбоку препятствие
        for angle_set, new_angle in (({-45, -90}, 45), ({45, 90}, -45)):
            if not angle_set.issubset(normal_angles):
                self.change_angle(new_angle)
                return True

        # Проверка возможности пройти вперед, если нет - поворачиваем
        if 0 in normal_angles:
            return False
        else:
            self.change_angle(normal_angles.pop() if normal_angles else 180)
            return True

    def update(self, food_count, is_collide_snakes_rectangles, **kwargs):
        collision_is_avoided = self.avoid_collision(
            is_collide_snakes_rectangles)
        if not collision_is_avoided:
            if self.has_to_find_food(food_count):
                self.find_new_food()
            if self.current_food:
                self.go_to_point(*self.current_food.xy)
        self.draw_food_line()
        self.move()
        if food_count:
            self.add_tail(food_count)


class SnakeContainer(ObjectsContainer):
    """Контейнер для змей."""
    obj_class = Food

    def __init__(self, snake_color, food_container, win, count=0):
        super().__init__(win, count)
        self.snake_color = snake_color
        self.food_container = food_container
        self.main_snake_id = None
        self._snakes_rectangles = None

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
        snake_params['color'] = self.snake_color
        snake = Snake(self.get_id(), self.win, **snake_params)
        self.add_obj(snake)
        self.main_snake_id = snake.id
        return snake

    def snake_is_dead(self, snake):
        """Смерть змеи."""
        snake.is_alive = False
        self.delete_by_id(snake.id)

    def clear_snakes_rectangles(self):
        """Застаявляем при следующем обращении пересчитывать прямоугольники."""
        self._snakes_rectangles = None

    @property
    def snakes_rectangles(self):
        """Получение прямоугольников для змей."""
        if self._snakes_rectangles is not None:
            return self._snakes_rectangles
        return [(snake, snake.get_collision_rectangles())
                for snake in self.get_snake_generator()]

    def is_collide_snakes_rectangles(self, pos, exclude_snake=None):
        """Проверка, что точка лежит в каком-нибудь прямоугольнике змеи."""
        return any(
            rect.collidepoint(*pos)
            for s, rectangles in self.snakes_rectangles for rect in rectangles
            if not exclude_snake or (exclude_snake and s is not exclude_snake)
        )


class GameLogic:
    """Класс с игровой логикой."""

    def __init__(self, win, snake_color=None):
        self.win = win

        self.bot_snakes = []
        self.food_container = FoodContainer(self.win, count=INITIAL_FOOD_COUNT)
        self.snake_container = SnakeContainer(
            snake_color, self.food_container, self.win)
        self.snake = self.snake_container.create_main_snake()

        for one_pos in (100, 300, 500, 700):
            self.snake_container.create_bot_snake(start_pos=(one_pos, one_pos))

    def get_snakes(self, only_bots=False, only_alive=True):
        """Получение списка змей."""
        return [
            s for s in self.snake_container.get_snake_generator(only_bots)
            if not only_alive or (only_alive and s.is_alive)
        ]

    def snake_is_dead(self, snake):
        """Отработка гибели змеи."""
        if snake is self.snake:
            print('Игра закончена')
            sys.exit()
        else:
            self.snake_container.snake_is_dead(snake)
            for circle in snake.circles:
                self.food_container.add_new_obj(pos=circle.xy, force=True)
            self.snake_container.create_bot_snake(
                start_pos=self.get_random_free_position())

    def get_random_free_position(self, check_distance_to_head=True):
        """Получение точки далеко от других змей и игрока"""
        is_normal_distance = True
        for i in range(10):
            pos = get_random_pos(0.15)
            is_in_rect = self.snake_container.is_collide_snakes_rectangles(pos)
            if check_distance_to_head:
                is_normal_distance = (
                    not check_distance_to_head or check_distance_to_head and
                    get_points_distance(*pos, *self.snake.head_xy) > (
                        self.snake.current_speed * FPS * 3)
                )
            if not is_in_rect and is_normal_distance:
                return pos
        return random.choice((0, WIDTH)), random.randint(0, HEIGHT)

    def check_collisions(self):
        """Проверка коллизий."""
        snakes_was_updated = False

        for snake in self.get_snakes():
            for other_snake in self.get_snakes():
                collision = snake.find_collision_with_other_snake(
                    other_snake, exclude_self=True)
                if collision is None:
                    continue
                elif collision == 0:
                    # Погибает та змея, у которой меньше угол до другой головы,
                    # т.е. та змея, которая въехала
                    snake_angle = abs(calculate_angle_to_point(
                        *snake.head_xy, *other_snake.head_xy, snake.angle))
                    other_snake_angle = abs(calculate_angle_to_point(
                        *other_snake.head_xy, *snake.head_xy,
                        other_snake.angle))
                    self.snake_is_dead(snake if snake_angle <= other_snake_angle
                                       else other_snake)
                else:
                    self.snake_is_dead(snake)
                snakes_was_updated = True

        if snakes_was_updated:
            self.check_collisions()

    def check_snakes_in_game_rect(self):
        """Проверка гибели змеи при выходе за границы игры."""
        for snake in self.get_snakes():
            if not all(GameRect.collidepoint(*circle.xy)
                       for circle in snake.circles):
                self.snake_is_dead(snake)

    def set_snake_turning(self, direction):
        """Установка направления поворота змеи."""
        self.snake.set_turning(direction)

    def set_snake_boost(self, enable_boost):
        """Установка ускорения змеи."""
        self.snake.set_boost(enable_boost)

    def draw(self):
        """Отрисовка всего."""
        self.food_container.draw()
        for snake in self.get_snakes():
            snake.draw()

    def update(self, **kwargs):
        self.snake_container.clear_snakes_rectangles()
        self.check_snakes_in_game_rect()
        self.check_collisions()
        for snake in self.get_snakes():
            snake_food_count = self.food_container.update(snake.head)
            snake.update(
                food_count=snake_food_count,
                is_collide_snakes_rectangles=(
                    self.snake_container.is_collide_snakes_rectangles),
            )
        self.draw()

    @property
    def game_surface_offset(self):
        """Смещение игровой площадки."""
        return (
            WINDOW_WIDTH // 2 - self.snake.head.x,
            WINDOW_HEIGHT // 2 - self.snake.head.y
        )


class Controller(BaseController):
    """Контроллер."""

    default_color = GAME_DEFAULT_COLOR
    background_color = GAME_BACKGROUND_COLOR

    def __init__(self, win, **kwargs):
        super().__init__(win)
        self.game = GameLogic(self.game_surface, **kwargs)

    def handle_event(self, event):
        # Проверка зажатия клавиши
        if event.type == pygame.KEYDOWN:
            if event.key in LEFT_RIGHT_BUTTONS:
                self.game.set_snake_turning(DE.get_from_button(event.key))
            elif event.key == pygame.K_UP:
                self.game.set_snake_boost(True)
        # Проверка отжатия клавиши
        elif event.type == pygame.KEYUP:
            if event.key in LEFT_RIGHT_BUTTONS:
                self.game.set_snake_turning(None)
            elif event.key == pygame.K_UP:
                self.game.set_snake_boost(False)

    def draw_mini_map(self, size):
        """Отрисовка мини карты."""
        mini_map = pygame.transform.scale(self.game_surface, (size, size))
        self.win.blit(mini_map, (0, WINDOW_HEIGHT - size))
        pygame.draw.rect(
            self.win, BLACK,
            pygame.Rect(0, WINDOW_HEIGHT - size, size, size), 1
        )

    def update(self):
        super().update()
        self.game.update()

        self.win.fill(self.default_color)
        self.win.blit(self.game_surface, self.game.game_surface_offset)
        if SHOW_MINI_MAP:
            self.draw_mini_map(MINI_MAP_SIZE)


class TestController(BaseController):
    """Тестовый контроллер для проверки отдельных элементов."""
    center_xy = (WIDTH // 2, HEIGHT // 2)

    def update(self):
        super().update()

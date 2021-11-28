import abc
import functools
import random

from settings import *
from helpers import *


class Drawable(abc.ABC):
    """Объект, который можно отрисовать на экране"""

    @abc.abstractmethod
    def draw(self, **kwargs):
        """Отрисовка объекта на экране."""
        pass


class AbstractFigure(Drawable):
    """Абстрактная фигура."""
    # Цвет
    color = WHITE

    def __init__(self, win, pos, color=None, **kwargs):
        """
        :param win: Окно
        :param pos: Позиция фигуры
        """
        self.win = win
        self.color = color if color else self.color
        self.x, self.y = pos

    def set_random_positions(self):
        """Установка случайных координат."""
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)


class Circle(AbstractFigure):
    """Круг."""
    # Радиус круга
    radius = 1

    def __init__(self, win, radius=None, **kwargs):
        super().__init__(win, **kwargs)
        self.radius = radius if radius else self.radius

    def draw(self, **kwargs):
        """Отрисовка круга."""
        pygame.draw.circle(self.win, self.color, (self.x, self.y), self.radius)

    @property
    def xy(self):
        return self.x, self.y

    @property
    def coords(self):
        """Именованный кортеж с координатами сторон."""
        half_radius = self.radius / 2
        return Coordinates(
            self.x - half_radius, self.x + half_radius,
            self.y - half_radius, self.y + half_radius,
        )

    def set_coordinate(self, side, value):
        """Устанавливает координату стороны фигуры."""
        half_radius = self.radius / 2
        new_value = value + half_radius * DE.sign_mapping[side]
        if side in DE.LEFT_RIGHT:
            self.x = new_value
        elif side in DE.UP_DOWN:
            self.y = new_value
        else:
            raise ValueError(f'Неправильная сторона - "{side}"')

    def get_distance_to_circle(self, circle):
        """Растояние от центра круга до центра другого круга."""
        return get_points_distance(*self.xy, *circle.xy)

    @property
    def rect(self):
        """Получение прямоугольника."""
        coords = self.coords
        return pygame.Rect(
            (coords.left, coords.top,
             coords.right - coords.left, coords.bottom - coords.top)
        )


class ObjectsContainer(Drawable):
    """Контейнер для объектов."""
    max_id = 10000
    current_id = 0
    obj_class = None

    def __init__(self, win, count=0):
        self.win = win
        self.objects = {}
        if count:
            self.add_multiple_objs(count, force=True)

    def get_new_obj(self, **kwargs):
        """Получение нового объекта"""
        return self.obj_class(self.get_id(), self.win, **kwargs)

    def add_obj(self, obj):
        """Добавление объекта"""
        self.objects[obj.id] = obj
        return True

    def add_new_obj(self, **kwargs):
        """Добавление нового объекта"""
        obj = self.get_new_obj(**kwargs)
        self.add_obj(obj)
        return obj

    def add_multiple_objs(self, count, **kwargs):
        """Добавление нескольких элементв"""
        return [self.add_new_obj(**kwargs) for _ in range(count)]

    @classmethod
    def get_id(cls):
        """Получение нового id для объекта."""
        cls.current_id += 1
        return (cls.current_id + 1) % cls.max_id

    def draw(self, **kwargs):
        """Отрисовка объектов."""
        for obj in self.objects.values():
            obj.draw()

    def delete_by_id(self, obj_id):
        """Удаление объекта по id."""
        if obj_id in self.objects:
            self.objects.pop(obj_id)

    def has_object(self, obj_id):
        """Проверка наличия объекта."""
        return obj_id in self.objects.keys()


class BaseSnake(Drawable):
    """Базовый класс змеи."""

    angle = 0
    max_turning_angle = 10
    # Обычная скорость
    usual_speed = 5
    # Величина увеличения скорости в секунду
    acceleration = 3
    # Максимальная скорость с ускорением
    max_speed_with_boost = 10
    default_start_pos = (WIDTH / 2, HEIGHT / 2)
    head_color = WHITE
    color = WHITE
    radius_increase_coef = 1.007
    max_radius = 25
    # Рисовать ли треугольники для расчёта коллизий
    draw_collision_rectangles = DRAW_COLLISION_RECTANGLES

    def __init__(self, snake_id, win, **kwargs):
        self.id = snake_id
        self.win = win
        self.angle = kwargs.get('angle', self.angle)
        self.start_pos = kwargs.get('start_pos', self.default_start_pos)
        self.radius = 10
        self.is_alive = True
        self.turning_direction = None
        self.is_boost_enabled = False
        self.current_speed = self.usual_speed

        head = self.get_circle(pos=self.start_pos, color=self.head_color)
        self.circles = [head]
        self.add_tail(2, initial=True)

    def get_circle(self, pos, **kwargs):
        """Получение круга с нужными параметрами."""
        circle_dict = dict(radius=self.radius, pos=pos, color=self.color)
        circle_dict.update(kwargs)
        return Circle(self.win, **circle_dict)

    @property
    def head(self):
        """Голова."""
        return self.circles[0]

    @property
    def head_xy(self):
        """Координаты головы."""
        head = self.head
        return head.x, head.y

    @property
    def double_r_coef(self):
        return 2 * self.radius * 0.7

    def add_tail(self, count=1, initial=False):
        """Добавление элементов в хвост."""
        for _ in range(count):
            last_circle = self.circles[-1]
            radian_angle = math.radians(self.angle)
            if initial:
                pos = (
                    last_circle.x - self.double_r_coef * math.cos(radian_angle),
                    last_circle.y - self.double_r_coef * math.sin(radian_angle)
                )
            else:
                pos = last_circle.xy
            self.circles.append(self.get_circle(pos=pos))

        self.update_radius(self.radius * self.radius_increase_coef)

    def update_radius(self, new_radius):
        """Обновить радиус."""
        self.radius = min(new_radius, self.max_radius)
        for circle in self.circles:
            circle.radius = self.radius

    def update_current_speed(self):
        """Обновить текущую скорость с учетом ускорения/замедления."""
        if self.is_boost_enabled:
            self.current_speed = self.current_speed + self.acceleration / FPS
            if self.current_speed > self.max_speed_with_boost:
                self.current_speed = self.max_speed_with_boost
        elif self.current_speed == self.usual_speed:
            return
        else:
            self.current_speed = self.current_speed - self.acceleration / FPS
            if self.current_speed < self.usual_speed:
                self.current_speed = self.usual_speed

    def move(self):
        """Движение вперед."""
        if not self.circles:
            return

        prev_x = prev_y = None
        for i, circle in enumerate(self.circles):
            if i == 0:
                circle.x, circle.y = get_new_point_pos(
                    *circle.xy, self.angle, self.current_speed)
                prev_x, prev_y = circle.x, circle.y
                continue

            distance = get_points_distance(*circle.xy, prev_x, prev_y)
            if distance > 0.5 * self.radius:
                angle = get_angle_of_points(prev_x, prev_y, *circle.xy)
                circle.x, circle.y = get_new_point_pos(
                    prev_x, prev_y, angle, self.double_r_coef)

            prev_x, prev_y = circle.xy

    @property
    def turning_angle(self):
        """Угол поворота."""
        if not self.turning_direction:
            return 0
        return self.max_turning_angle * DE.sign_mapping.get(
            self.turning_direction, 0)

    def change_angle(self, delta_angle=None):
        """Изменение угла."""
        if delta_angle is None:
            delta = self.turning_angle
        else:
            max_angle = get_sign(delta_angle) * self.max_turning_angle
            delta = min(delta_angle, max_angle, key=abs)
        self.angle = normalize_angle(self.angle + delta)

    def set_turning(self, direction=None):
        """Установка/отключение поворота в сторону."""
        if not direction:
            self.turning_direction = None
        elif direction not in DE.LEFT_RIGHT:
            raise ValueError('Неверное направление поворота')
        else:
            self.turning_direction = direction

    def set_boost(self, enable_boost=True):
        """Установка/отключение ускорения в сторону."""
        self.is_boost_enabled = enable_boost

    def draw(self, **kwargs):
        for circle in reversed(self.circles):
            circle.draw()

    def find_collision_with_other_snake(self, snake, exclude_self=False):
        """Нахождение столкновения головы этой змеи с другой."""
        if exclude_self and snake is self:
            return

        for i, circle in enumerate(snake.circles):
            if circle.get_distance_to_circle(self.head) < (
                    self.radius + snake.radius):
                # Пропускаем коллизии, если это сама же змея и её голова
                if not (snake is self and i <= 1):
                    return i

    def get_collision_rectangles(self, step=5):
        """Получение прямоугольников для определения коллизий."""
        rects = [circle.rect for circle in self.circles]
        rectangles = [
            functools.reduce(pygame.Rect.union, rects[i * step: (i + 1) * step])
            for i in range(math.ceil(len(rects) / step))
        ]
        if self.draw_collision_rectangles:
            for r in rectangles:
                self.draw_rect(r, RED)
        return rectangles

    def get_new_position_from_head(self, angle, distance):
        """Получение новой позиции, начиная от головы."""
        return get_new_point_pos(*self.head_xy, angle, distance)

    def draw_rect(self, rectangle, color):
        """Нарисовать прямоугольник на экране."""
        pygame.draw.rect(self.win, color, rectangle, 1)

    def draw_line_from_head(self, pos, color=None):
        """Нарисовать линию из точки головы"""
        pygame.draw.line(self.win, color or self.color, self.head_xy, pos)

    def update(self, **kwargs):
        """Базовое обновление змеи (движение и поедание еды."""
        food_count = kwargs.get('food_count', 0)
        self.update_current_speed()
        self.change_angle()
        self.move()
        if food_count:
            self.add_tail(food_count)


class BaseController:
    """Базовый класс контроллера."""

    background_color = WHITE

    def __init__(self, win):
        self.win = win
        self.game_surface = pygame.Surface((WIDTH, HEIGHT))
        self.is_running = True

    def update(self):
        """Обновление данных."""
        self.check_events()
        self.game_surface.fill(self.background_color)

    def handle_event(self, event):
        """Обработка событий."""
        pass

    def check_events(self):
        """Проверка событий."""
        # Ввод процесса (события)
        for event in pygame.event.get():
            # Проверка закрытия окна
            if event.type == pygame.QUIT:
                self.is_running = False
            else:
                self.handle_event(event)

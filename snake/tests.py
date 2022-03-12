import unittest
from functools import partial

from snake.helpers import get_angle_of_points, calculate_angle_to_point


class BaseAngleTest(unittest.TestCase):
    """Базовый тест для проверки углов."""

    center_xy = (200, 200)
    function_params = [
        (100, 100, *center_xy),
        (200, 0,  *center_xy),
        (300, 100, *center_xy),
        (300, 200, *center_xy),
        (300, 300, *center_xy),
        (200, 300, *center_xy),
        (100, 300, *center_xy),
        (100, 200, *center_xy),
    ]
    function = None
    correct_values = ()

    def test_function(self):
        for func_param, correct_value in zip(
                self.function_params, self.correct_values):
            self.assertEqual(self.function(*func_param), correct_value,
                             msg=f'params={func_param}')


class TestAngleOfPoints(BaseAngleTest):
    """Проверка вычисления угла до точки."""
    function = staticmethod(get_angle_of_points)
    correct_values = (45, 90, 135, 180, 225, 270, 315, 0)


class TestCalculateAngleToPoint(BaseAngleTest):
    """Проверка вычисления угла, на который надо повернуть """
    function = staticmethod(partial(calculate_angle_to_point, current_angle=0))
    correct_values = (45, 90, 135, 180, -135, -90, -45, 0)


if __name__ == '__main__':
    unittest.main()

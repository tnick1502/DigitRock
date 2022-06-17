import math
from k0_test.triaxial_k0_model import ModelK0
import pytest


""" Константы для тестирования """
TESTING_DICTS = [{}]

PLOT = False


@pytest.mark.parametrize("__test_data", TESTING_DICTS)
def test_ModelK0_set_test_data(__test_data):
    """ Проверка создания тестовых данных """
    model = ModelK0()

    try:
        model.set_test_data(__test_data)
    except RuntimeWarning:
        if "sigma_1" not in __test_data or "sigma_3" not in __test_data:
            print(f"\n __test_data is empty\n")


def test_lse_linear_estimation():
    """ Проверка МНК на данных с протокола 762-21/48-1/БП"""
    _test_x = [0, 0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2]
    _test_y = [0, 0.082, 0.190, 0.280, 0.362, 0.429, 0.524, 0.580, 0.712, 0.774, 0.854]
    k, *__ = ModelK0.lse_linear_estimation(_test_x, _test_y)
    assert math.trunc(k * 100) / 100 == 0.42


def test_define_ko_sand():
    """ Проверка МНК на данных с протокола 762-21/48-1/БП"""
    _test_x = [0, 0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2]
    _test_y = [0, 0.082, 0.190, 0.280, 0.362, 0.429, 0.524, 0.580, 0.712, 0.774, 0.854]
    k, b = ModelK0.define_ko(_test_x, _test_y)
    assert k == 0.42


def test_define_ko_clay():
    """ Проверка МНК на данных с протокола 762-21/53-6/БП"""
    _test_x = [0, 0.150, 0.300, 0.450, 0.600, 0.750, 0.900, 1.050, 1.200]
    _test_y = [0, 0.017, 0.039, 0.071, 0.108, 0.208, 0.265, 0.368, 0.486]
    k, b = ModelK0.define_ko(_test_x, _test_y)
    assert k == 0.62  # в протоколе 0.62 я не знаю как это так


def test_define_ko_sand_2():
    """ Проверка МНК на данных с протокола 762-21/49-1/БП"""
    _test_x = [0, 0.200, 0.400, 0.600, 0.800, 1.000, 1.200, 1.400, 1.600, 1.800, 2.000]
    _test_y = [0, 0.076, 0.171, 0.250, 0.341, 0.446, 0.516, 0.604, 0.677, 0.797, 0.856]
    k, b = ModelK0.define_ko(_test_x, _test_y)
    assert k == 0.44  # в протоколе 0.44 я не знаю как это так


def test_plotter():
    _test_data = {"sigma_1": [0, 0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2],
                  "sigma_3": [0, 0.082, 0.190, 0.280, 0.362, 0.429, 0.524, 0.580, 0.712, 0.774, 0.854]}

    model = ModelK0()
    model.set_test_data(_test_data)

    if PLOT:
        model.plotter()

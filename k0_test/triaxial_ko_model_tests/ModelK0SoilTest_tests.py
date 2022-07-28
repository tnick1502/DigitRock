from k0_test.triaxial_k0_model import ModelK0SoilTest
from excel_statment.properties_model import K0Properties

PLOT = True


def test_model_k0_simple():
    """ Данные с протокола 762-21/53-6/БП"""
    print('\n')
    _test_params = {"K0nc": 0.62, "OCR": 1.3, "depth": 23, "sigma_1_step": 0.150, "sigma_1_max": 1.200}

    sigma_p, sigma_3_p = K0Properties.define_sigma_p(_test_params["OCR"], _test_params["depth"], _test_params["K0nc"])
    _test_params["sigma_p"] = sigma_p
    _test_params["sigma_3_p"] = sigma_3_p

    model = ModelK0SoilTest()
    model.set_test_params(_test_params)

    if PLOT:

        model.plotter()

    assert ModelK0SoilTest.is_debug_ok, "Выходные массивы модели не сходятся с входными массивами на обработку"

    check_test(model._test_result, model._test_params)

    assert model.get_test_results()["K0nc"] == 0.62


def test_model_k0_zero_depth():
    """ Тест от Люды с нулевой глубиной"""
    print('\n')
    _test_params = {"K0nc": 0.62, "OCR": 1.3, "depth": 0, "sigma_1_step": 0.150, "sigma_1_max": 1.200}

    sigma_p, sigma_3_p = K0Properties.define_sigma_p(_test_params["OCR"], _test_params["depth"], _test_params["K0nc"])
    _test_params["sigma_p"] = sigma_p
    _test_params["sigma_3_p"] = sigma_3_p

    model = ModelK0SoilTest()
    model.set_test_params(_test_params)

    if PLOT:

        model.plotter()

    assert ModelK0SoilTest.is_debug_ok, "Выходные массивы модели не сходятся с входными массивами на обработку"

    check_test(model._test_result, model._test_params)

    assert model.get_test_results()["K0nc"] == 0.62


def test_model_k0():
    """ Данные с протокола 762-21/53-6/БП"""
    print('\n')
    _test_params = {"K0nc": 0.43, "OCR": 1, "depth": 1, "sigma_1_step": 0.150, "sigma_1_max": 1.200}

    sigma_p, sigma_3_p = K0Properties.define_sigma_p(_test_params["OCR"], _test_params["depth"], _test_params["K0nc"])
    _test_params["sigma_p"] = sigma_p
    _test_params["sigma_3_p"] = sigma_3_p

    model = ModelK0SoilTest()
    model.set_test_params(_test_params)

    if PLOT:

        model.plotter()

    assert ModelK0SoilTest.is_debug_ok, "Выходные массивы модели не сходятся с входными массивами на обработку"

    check_test(model._test_result, model._test_params)

    assert model.get_test_results()["K0nc"] == 0.43


def test_model_k0_2():
    """ Данные с протокола 762-21/53-6/БП"""
    print('\n')
    _test_params = {"K0nc": 0.63, "OCR": 1.36, "depth": 29, "sigma_1_step": 0.200, "sigma_1_max": 1.400}

    sigma_p, sigma_3_p = K0Properties.define_sigma_p(_test_params["OCR"], _test_params["depth"], _test_params["K0nc"])
    _test_params["sigma_p"] = sigma_p
    _test_params["sigma_3_p"] = sigma_3_p

    model = ModelK0SoilTest()
    model.set_test_params(_test_params)

    if PLOT:

        model.plotter()

    assert ModelK0SoilTest.is_debug_ok, "Выходные массивы модели не сходятся с входными массивами на обработку"

    check_test(model._test_result, model._test_params)

    assert model.get_test_results()["K0nc"] == 0.63


def test_model_k0_3():
    """ Данные с протокола 762-21/53-6/БП"""
    print('\n')
    _test_params = {"K0nc": 0.63, "OCR": 1.36, "depth": 70, "sigma_1_step": 0.200, "sigma_1_max": 1.400}

    sigma_p, sigma_3_p = K0Properties.define_sigma_p(_test_params["OCR"], _test_params["depth"], _test_params["K0nc"])
    _test_params["sigma_p"] = sigma_p
    _test_params["sigma_3_p"] = sigma_3_p

    model = ModelK0SoilTest()
    model.set_test_params(_test_params)

    if PLOT:

        model.plotter()

    assert ModelK0SoilTest.is_debug_ok, "Выходные массивы модели не сходятся с входными массивами на обработку"

    check_test(model._test_result, model._test_params)

    # Этот тест иногда не выполняется в угоду больших шумов
    assert model.get_test_results()["K0nc"] == 0.63, "Этот тест иногда не выполняется в угоду больших шумов"


def check_test(__test_data, __test_params):
    # проверка числа точек
    assert int((__test_params["sigma_1_max"]*1000)/(__test_params["sigma_1_step"]*1000)) + 1 == len(__test_data["sigma_1"])

    for sigma_1 in __test_data["sigma_1"]:
        left = round(sigma_1 % __test_params["sigma_1_step"], 4)
        assert (left >= __test_params["sigma_1_step"]*0.95) or (left <= __test_params["sigma_1_step"]*0.05)


def test_model_nuur():
    print('\n')
    _test_params = {"K0nc": 0.35, "OCR": 1.0, "depth": 10, "sigma_1_step": 0.400,
                    "sigma_1_max": 2.000, "mode_ur": True, "K0oc": 0.01, "Nuur": 0.15}

    sigma_p, sigma_3_p = K0Properties.define_sigma_p(_test_params["OCR"], _test_params["depth"], _test_params["K0nc"])
    _test_params["sigma_p"] = sigma_p
    _test_params["sigma_3_p"] = sigma_3_p

    model = ModelK0SoilTest()
    model.set_test_params(_test_params)

    # if PLOT:
    #
    #     model.plotter()
    #
    # assert ModelK0SoilTest.is_debug_ok, "Выходные массивы модели не сходятся с входными массивами на обработку"
    #
    # check_test(model._test_result, model._test_params)
    #
    # # Этот тест иногда не выполняется в угоду больших шумов
    # assert model.get_test_results()["K0nc"] == 0.63, "Этот тест иногда не выполняется в угоду больших шумов"
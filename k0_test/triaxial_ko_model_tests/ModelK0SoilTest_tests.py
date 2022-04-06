from k0_test.triaxial_k0_model import ModelK0SoilTest
from excel_statment.properties_model import K0Properties

PLOT = False


def test_model_k0_simple():
    """ Данные с протокола 762-21/53-6/БП"""
    print('\n')
    _test_params = {"K0": 0.62, "OCR": 1.3, "depth": 23, "sigma_1_step": 0.150, "sigma_1_max": 1.200}

    sigma_p, sigma_3_p = K0Properties.define_sigma_p(_test_params["OCR"], _test_params["depth"], _test_params["K0"])
    _test_params["sigma_p"] = sigma_p
    _test_params["sigma_3_p"] = sigma_3_p

    model = ModelK0SoilTest()
    model.set_test_params(_test_params)

    if PLOT:

        model.plotter()

    test_data = model.test_data

    check_test(test_data, _test_params)

    assert model.get_test_results()["K0"] == 0.62


def test_model_k0_zero_depth():
    """ Тест от Люды с нулевой глубиной"""
    print('\n')
    _test_params = {"K0": 0.62, "OCR": 1.3, "depth": 0, "sigma_1_step": 0.150, "sigma_1_max": 1.200}

    sigma_p, sigma_3_p = K0Properties.define_sigma_p(_test_params["OCR"], _test_params["depth"], _test_params["K0"])
    _test_params["sigma_p"] = sigma_p
    _test_params["sigma_3_p"] = sigma_3_p

    model = ModelK0SoilTest()
    model.set_test_params(_test_params)

    if PLOT:

        model.plotter()

    test_data = model.test_data
    check_test(test_data, _test_params)

    assert model.get_test_results()["K0"] == 0.62


def test_model_k0():
    """ Данные с протокола 762-21/53-6/БП"""
    print('\n')
    _test_params = {"K0": 0.43, "OCR": 1, "depth": 1, "sigma_1_step": 0.150, "sigma_1_max": 1.200}

    sigma_p, sigma_3_p = K0Properties.define_sigma_p(_test_params["OCR"], _test_params["depth"], _test_params["K0"])
    _test_params["sigma_p"] = sigma_p
    _test_params["sigma_3_p"] = sigma_3_p

    model = ModelK0SoilTest()
    model.set_test_params(_test_params)

    if PLOT:

        model.plotter()

    test_data = model.test_data

    check_test(test_data, _test_params)

    assert model.get_test_results()["K0"] == 0.43


def check_test(__test_data, __test_params):
    # проверка числа точек
    assert int(__test_params["sigma_1_max"]/__test_params["sigma_1_step"]) + 1 == len(__test_data["sigma_1"])

    for sigma_1 in __test_data["sigma_1"]:
        left = sigma_1 % __test_params["sigma_1_step"]
        assert left > __test_params["sigma_1_step"]*0.95 or left < __test_params["sigma_1_step"]*0.05

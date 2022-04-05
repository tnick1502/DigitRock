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

    assert model.get_test_results()["K0"] == 0.62

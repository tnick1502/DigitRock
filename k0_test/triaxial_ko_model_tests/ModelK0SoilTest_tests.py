from k0_test.triaxial_k0_model import ModelK0SoilTest

PLOT = True


def test_model_k0_simple():
    print('\n')
    _test_params = {"K0": 0.62, "OCR": 1.3, "depth": 23, "sigma_1_step": 0.150, "sigma_1_max": 1.2}
    model = ModelK0SoilTest()
    model.set_test_params(_test_params)

    if PLOT:

        model.plotter()

    assert model.get_test_results()["K0"] == 0.62

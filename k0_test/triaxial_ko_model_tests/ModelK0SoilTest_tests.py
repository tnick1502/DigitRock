from k0_test.triaxial_k0_model import ModelK0SoilTest

PLOT = True


def test_model_k0_simple():
    print('\n')
    _test_params = {"K0": 0.42, "M": 0.1, "sigma_1_step": 0.2, "sigma_1_max": 2.0}
    model = ModelK0SoilTest()
    model.set_test_params(_test_params)

    if PLOT:

        model.plotter()

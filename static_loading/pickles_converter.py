from singletons import E_models, E_models_old, FC_models, FC_models_old
from static_loading.triaxial_static_loading_test_model import ModelTriaxialStaticLoadSoilTest
from static_loading.mohr_circles_test_model import ModelMohrCirclesSoilTest




def E():
    E_models_old.load("C:/Users/Пользователь/Desktop/Новая папка (6)/Архив/Трёхосное сжатие (F, C, E)/E_models - 1.pickle")
    E_models.setModelType(ModelTriaxialStaticLoadSoilTest)

    for test in E_models_old:
        E_models.tests[test] = ModelTriaxialStaticLoadSoilTest()
        E_models[test].set_pickle_data(E_models_old[test])

    E_models.dump("C:/Users/Пользователь/Desktop/Новая папка (6)/Архив/Трёхосное сжатие (F, C, E)/E_models - 1.0.pickle")


def FC():
    FC_models_old.load(
        "C:/Users/Пользователь/Desktop/Новая папка (6)/Архив/Трёхосное сжатие (F, C, E)/FC_models - 1.pickle")
    FC_models.setModelType(ModelMohrCirclesSoilTest)

    for test in FC_models_old:
        FC_models.tests[test] = ModelMohrCirclesSoilTest()
        for i in FC_models_old[test]._tests:
            FC_models[test]._tests.append(ModelTriaxialStaticLoadSoilTest())
            FC_models[test]._tests[-1].set_pickle_data(i)

        FC_models.tests[test]._test_processing()

    FC_models.dump(
        "C:/Users/Пользователь/Desktop/Новая папка (6)/Архив/Трёхосное сжатие (F, C, E)/FC_models - 1.0.pickle")

FC()
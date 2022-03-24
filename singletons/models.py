from excel_statment.statment_model import Statment
from descriptors import DataTypeValidation
from loggers.logger import app_logger, log_this
import pickle
import os

instances = {}

def singleton(aClass):
    instance = None
    def onCall(*args, **kwargs):
        nonlocal instance
        if instance == None:
            instance = aClass(*args, **kwargs)
        return instance
    return onCall


class Models:
    tests = DataTypeValidation(dict)
    model_class = None

    def __init__(self):
        self.tests = {}
        self.model_class = None

    def setModelType(self, model):
        self.model_class = model

    def generateTests(self):
        for test_name in statment:
            try:
                statment.current_test = test_name
                self.tests[test_name] = self.model_class()
                self.tests[test_name].set_test_params()
            except:
                app_logger.exception(f"Ошибка моделирования опыта {test_name}")
                break

    def dump(self, path):
        with open(path, "wb") as file:
            pickle.dump(self.tests, file)

    def load(self, path):
        with open(path, 'rb') as f:
            self.tests = pickle.load(f)

    def __iter__(self):
        for key in self.tests:
            yield key

    def __getitem__(self, key):
        if key is None:
            raise KeyError(f"No test with key None")
        elif not key in list(self.tests.keys()):
            raise KeyError(f"No test with key {key}")
        return self.tests[key]

    def __len__(self):
        return len(self.tests)


@singleton
class ModelsE(Models):
    pass

@singleton
class ModelsEur(Models):
    pass

@singleton
class ModelsFC(Models):
    pass

@singleton
class ModelsVibrationFC(Models):
    pass

@singleton
class ModelsVibrationCreep(Models):
    pass

@singleton
class ModelsRC(Models):
    pass

@singleton
class ModelsCyclic(Models):
    pass

@singleton
class ModelsConsolidation(Models):
    pass

@singleton
class ModelsShear(Models):
    pass

@singleton
class ModelsShearDilatancy(Models):
    pass

@singleton
class ModelsK0(Models):
    pass

statment = Statment()

E_models = ModelsE()

Eur_models = ModelsEur()

FC_models = ModelsFC()

VC_models = ModelsVibrationCreep()

Cyclic_models = ModelsCyclic()

RC_models = ModelsRC()

Consolidation_models = ModelsConsolidation()

Shear_models = ModelsShear()

Shear_Dilatancy_models = ModelsShearDilatancy()

VibrationFC_models = ModelsVibrationFC()

K0_models = ModelsK0()


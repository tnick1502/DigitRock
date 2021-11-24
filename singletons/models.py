from excel_statment.statment_model import Statment
from descriptors import DataTypeValidation
from loggers.logger import app_logger, log_this
import pickle

instances = {}

def singleton(aClass):
    def onCall(*args, **kwargs):
        if aClass not in instances:
            instances[aClass] = aClass(*args, **kwargs)
        return instances[aClass]
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

    def dump(self, directory, name="models.pickle"):
        with open(directory + "/" + name, "wb") as file:
            pickle.dump(self.tests, file)

    def load(self, file):
        with open(file, 'rb') as f:
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
class ModelsFC(Models):
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


statment = Statment()

E_models = ModelsE()

FC_models = ModelsFC()

VC_models = ModelsVibrationCreep()

Cyclic_models = ModelsCyclic()

RC_models = ModelsRC()

Consolidation_models = ModelsConsolidation()






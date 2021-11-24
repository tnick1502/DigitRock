from excel_statment.statment_model import Statment
from descriptors import DataTypeValidation
from loggers.logger import app_logger, log_this
import pickle

class Models:
    tests = DataTypeValidation(dict)
    model_class = None

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Models, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.tests = {}
        self.model_class = None

    def setModelType(self, model):
        self.model_class = model

    #@log_this(app_logger, "debug")
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

class Models_E:
    tests = DataTypeValidation(dict)
    model_class = None

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Models_E, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.tests = {}
        self.model_class = None

    def setModelType(self, model):
        self.model_class = model

    #@log_this(app_logger, "debug")
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

class Models_FC:
    tests = DataTypeValidation(dict)
    model_class = None

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Models_FC, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.tests = {}
        self.model_class = None

    def setModelType(self, model):
        self.model_class = model

    #@log_this(app_logger, "debug")
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

class Models_VibrationCreep:
    tests = DataTypeValidation(dict)
    model_class = None

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Models_VibrationCreep, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.tests = {}
        self.model_class = None

    def setModelType(self, model):
        self.model_class = model

    #@log_this(app_logger, "debug")
    def generateTests(self):
        for test_name in statment:
            try:
                statment.current_test = test_name
                self.tests[test_name] = self.model_class()
                self.tests[test_name].set_test_params()
            except:
                app_logger.exception(f"Ошибка моделирования опыта {test_name}")

        #app_logger.info(f"Моделирование прошло успешно")

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

statment = Statment()

models = Models()

E_models = Models_E()

FC_models = Models_FC()

VC_models = Models_VibrationCreep()
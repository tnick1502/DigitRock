from excel_statment.statment_model import Statment
from descriptors import DataTypeValidation
from loggers.logger import app_logger, log_this
import pickle
import os
from version_control.configs import actual_version
__version__ = actual_version

from threading import Lock, Thread

class SingletonMeta(type):
    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class Model(metaclass=SingletonMeta):
    keys: dict = {}
    data: dict = {}
    handler: dict = {}
    data_class = None
    handler_class = None
    version = None

    def __init__(self):
        self.data = {}
        self.handler = {}
        self.data_class = None
        self.handler_class = None
        self.version = "{:.2f}".format(__version__)

    def setDataClass(self, data_class, handler_class):
        self.data_class = data_class
        self.handler_class = handler_class

    def generateTests(self, generate=True):
        for key in statment:
            try:
                statment.current_test = key
                self.data[key] = self.data_class()
                self.handler[key] = self.handler_class()
                if generate:
                    self.handler[key].set_test_params()
            except:
                app_logger.exception(f"Ошибка моделирования опыта {key}")
                break

    def dump(self, dir: str, key: str):
        data_dir, handler_dir = Model.create_save_dir(dir, statment.general_parameters.test_mode)

        data_path = os.path.join(data_dir, f"data {key}.pickle")
        handler_path = os.path.join(handler_dir, f"handler {key}.pickle")

        with open(data_path, "wb") as file:
            pickle.dump(
                {
                    "data": self.data[key],
                    "version": self.version
                },
                file
            )

        with open(handler_path, "wb") as file:
            pickle.dump(
                {
                    "data": self.handler[key],
                    "version": self.version
                },
                file
            )

    def dump_all(self, dir: str, model_name: str):
        for key in self.data:
            self.dump(dir, model_name, key)

    def load(self, dir):
        data_dir, handler_dir = Model.create_save_dir(dir, statment.general_parameters.test_mode)

        load_data_keys = []
        load_handler_keys = []

        for key in statment:
            statment.current_test = key

            data_path = os.path.join(data_dir, f"data {key}.pickle")
            handler_path = os.path.join(handler_dir, f"handler {key}.pickle")
            if os.path.exists(data_path):
                with open(data_path, 'rb') as f:
                    data = pickle.load(f)
                    self.data[key] = data["data"]
                load_data_keys.append(key)
            else:
                self.data[key] = self.data_class()

            if os.path.exists(handler_path):
                with open(handler_path, 'rb') as f:
                    data = pickle.load(f)
                    assert data.get("version", None), \
                        f"Несовпадение версии модели и программы. Программа: {self.version}, модель: неизвестно"
                    assert self.version == data["version"], \
                        f"Несовпадение версии модели и программы. Программа: {self.version}, модель: {data['version']}"
                    self.handler[key] = data["data"]
                load_handler_keys.append(key)
            else:
                self.handler[key] = self.handler_class()
                self.handler[key].set_test_params()
        return load_data_keys, load_handler_keys

    def __iter__(self):
        for key in self.tests:
            yield key

    def __getitem__(self, key):
        if key is None:
            raise KeyError(f"No test with key None")
        elif not key in list(self.handler.keys()):
            raise KeyError(f"No test with key {key}")
        return self.handler[key]

    def __len__(self):
        return len(self.data)

    @staticmethod
    def create_save_dir(dir, model_name):
        if statment.general_data.shipment_number:
            shipment_number = f" - {statment.general_data.shipment_number}"
        else:
            shipment_number = ""

        data_dir = os.path.join(dir, "data_models " + model_name + shipment_number)
        handler_dir = os.path.join(dir, "handler_models " + model_name + shipment_number)
        for dir in [data_dir, handler_dir]:
            if not os.path.isdir(dir):
                os.mkdir(dir)
        return data_dir, handler_dir

for model_name in ["FC_models", "E_models", "VC_models", "Cyclic_models", "Consolidation_models", "RC_models",
                   "Shear_models", "Shear_Dilatancy_models", "VibrationFC_models", "RayleighDamping_models",
                   "K0_models"]:
    class_for_gen = type(model_name, (Model, ), {})
    locals()[model_name] = class_for_gen()

statment = Statment()



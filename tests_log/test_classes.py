from datetime import datetime, timedelta
from abc import abstractmethod
import numpy as np
import random
from tests_log.path_processing import cyclic_path_processing, FCE_path_processing
from singletons import statment, models, E_models, FC_models

def timedelta_to_dhms(duration, config=["дней", "часов", "минут"]):
    # преобразование в дни, часы, минуты и секунды
    days, seconds = duration.days, duration.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    return f'{days} {config[0]}, {hours} {config[1]}, {minutes} {config[2]}'

class DataTypeValidation:
    """Дескриптор для валидации данных"""
    def __init__(self, data_type):
        self.data_type = data_type

    def __set_name__(self, owner, name):
        self.attr = name

    def __set__(self, instance, value):
        if value is None:
            instance.__dict__[self.attr] = value
        elif isinstance(value, self.data_type):
            instance.__dict__[self.attr] = value
        else:
            raise ValueError(f"{instance} must be a {self.data_type}")

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self.attr, None)

class AttrDisplay:
    """Миксин для отображения"""
    pass

class CameraAssembly:
    """Non-data дескриптор, моделирующий сборку-разборку камеры
    Аргументы при инициализации:
        min: минимальное время сборки-разборки камеры
        max: максимальное время сборки-разборки камеры"""
    def __init__(self, min: float, max: float):
        assert max > min, "Минимальное время меньше максимального"
        self.min = min
        self.max = max

    def __get__(self, instance, owner):
        return timedelta(minutes=np.random.uniform(self.min, self.max))


class Test:
    """Суперкласс опыта

    Атрибуты:
        start_datetime: Дата начала опыта
        duration: Продолжительность опыта
        additional_data: Дополнительные данные опыта
        equipment - прибор, на котором проведен опыт


    Классы конкретных опытов наследуются от этого класса.

    !!! Необходимо перегрузить метод self._get_duration !!!

    При инициализации подается лабораторный номер и путь к файлу опыта. Можно вместо файла подать длину опыта в формате
    timedelta
    Файл опыта обрабатывается методом self._get_duration и определяется длина опыта.
    После необходимо подать дату начала опыта методом set_start_datetime
    Дату и время окончания опыта можно получить с помошью атрибута только для чтения self.end_datetime"""

    start_datetime: datetime = DataTypeValidation(datetime)
    duration: timedelta = DataTypeValidation(timedelta)
    additional_data = None
    equipment: DataTypeValidation(str)

    def __init__(self, test_file: str, additional_data=None):
        self.duration = test_file if isinstance(test_file, timedelta) else self._get_duration(test_file)
        self.additional_data = additional_data
        self.equipment = "Не назначен"

    def __str__(self):
        if self.start_datetime and self.end_datetime:
            return f"Дата начала: {self.start_datetime:%H:%M %d.%m.%Y}, Дата окончания: {self.end_datetime:%H:%M %d.%m.%Y}, Продолжительность: {timedelta_to_dhms(self.duration)}, Прибор: {self.equipment}"
        else:
            return f"Дата начала: Не установлена, Дата окончания: Не установлена, Продолжительность: {timedelta_to_dhms(self.duration)}"

    def get_dict(self):
        return self.__dict__

    @property
    def end_datetime(self):
        assert self.start_datetime, "Чтобы получить время окончания установите дату начала"
        assert self.duration, "Чтобы получить время окончания опыта задайте продолжительность"
        return self.start_datetime + self.duration

    @abstractmethod
    def _get_duration(self, test_file) -> timedelta:
        pass

class TestsLog:
    """Суперкласс журнала опытов

    Атрибуты:
        tests: Словарь с опытами (ключ - название пробы, значение - экземпляр класса Test)
        test_class: Класс с типами опытов
        equipment_count: Число приборов
        start_datetime: Дата и время начала проведения опытов
        duration: Продолжительность всех опытов
        camera_assembly: моделированиесборки-разборки камеры
        equipment_names: Массив имен приборов, если не задать, создается автоматически

    Классы журналов конкретных опытов наследуются от этого класса.

    !!! Необходимо перегрузить метод self.set_directory !!!

    Метод self.set_directory находит все файлы в папке и заполняет словарь self.tests"""
    tests: dict
    test_class: Test = None
    start_datetime: datetime = DataTypeValidation(datetime)
    duration: timedelta = DataTypeValidation(timedelta)
    camera_assembly = CameraAssembly(20, 40)
    equipment_names: list = None

    def __init__(self):
            self.tests = {}
            self.duration = timedelta()

    def __iter__(self):
        for key in self.tests:
            yield key

    def __getitem__(self, key):
        if not key in list(self.tests.keys()):
            return KeyError(f"No test with key {key}")
        return self.tests[key]

    def __setitem__(self, key, value):
        if isinstance(value, self.test_class):
            self.tests[key] = value
        else:
            raise TypeError("value must has type Test")

    def __str__(self):
        if self.start_datetime and self.end_datetime:
            main_data = f"Дата начала опытов: {self.start_datetime:%H:%M %d.%m.%Y}, Дата окончания опытов: {self.end_datetime:%H:%M %d.%m.%Y}, Продолжительность: {timedelta_to_dhms(self.duration)}, Приборы {self.equipment_names if self.equipment_names else self.equipment_count}"
        else:
            main_data =  f"Дата начала: Не установлена, Дата окончания: Не установлена, Продолжительность: Не определена"

        return main_data + "\n\n" + "Список опытов:\n" + "\n".join(map(lambda key: f"'{key}': {str(self.tests[key])}", list(self.tests.keys())))

    def __len__(self):
        return len(self.tests)

    def __bool__(self):
        if not len(self.tests):
            return False
        for test in self.tests:
            try:
                self.tests[test].end_datetime
            except AssertionError:
                return False
        return True

    def processing(self, work_at_night=False):
        assert self.start_datetime, "Не выбрано время начала серии опытов"
        assert len(self.tests), "Не загружено ни одного опыта"
        assert len(self.equipment_names), "Не задано число стабилометров"

        def vacant_devise(tests_object, equipment_names) -> tuple:
            """Функция определяет освободившийся прибор"""
            device_time = {devise: None for devise in equipment_names}
            for device in equipment_names:
                for test in tests_object:
                    if tests_object[test].equipment == device:
                        device_time[device] = max(device_time[device], tests_object[test].end_datetime) if device_time[
                            device] else tests_object[test].end_datetime

            key_min = min(device_time, key=device_time.get)

            return (key_min, device_time[key_min])

        def find_same_keys(keys, key):
            if key:
                find_base = lambda x: x[:x.find("№") - 1] if x.find("№") != -1 else x
                match_keys = []
                for element in keys:
                    if find_base(element) == find_base(key) and key != element:
                        match_keys.append(element)
                return match_keys
            else:
                return []

        for test in self.tests:
            self.tests[test].start_datetime = None
            self.tests[test].equipment = ""


        equipment_names = self.equipment_names
        keys = list(self.tests.keys())
        # заполняем первую партию
        last_key = None
        for device in equipment_names:
            # берем случайный образец
            random_key = last_key if last_key and len(find_same_keys(keys, last_key)) else np.random.choice(keys)
            match_keys = find_same_keys(keys, random_key)
            key = np.random.choice(match_keys) if len(match_keys) else random_key
            self[key].start_datetime = self.start_datetime + timedelta(minutes=np.random.uniform(0, 15))
            # закидываем на стабилометр
            self[key].equipment = device
            keys.remove(key)
            last_key = key
            if not keys:
                break

        # распределяем оставшиеся опыты
        while len(keys):
            device, time = vacant_devise(self.tests, equipment_names)
            random_key = last_key if last_key and len(find_same_keys(keys, last_key)) else np.random.choice(keys)
            match_keys = find_same_keys(keys, random_key)
            key = np.random.choice(match_keys) if len(match_keys) else random_key
            if not work_at_night:
                if 20 <= time.hour < 24:
                    time_to_next_day = timedelta(hours=8 + (24 - time.hour)) + self.camera_assembly
                elif 0 <= time.hour < 8:
                    time_to_next_day = timedelta(hours=8 - time.hour) + self.camera_assembly
                else:
                    time_to_next_day = self.camera_assembly
                self.tests[key].start_datetime = time + time_to_next_day
            else:
                self.tests[key].start_datetime = time + self.camera_assembly

            # закидываем на стабилометр
            self.tests[key].equipment = device
            last_key = key
            keys.remove(key)

        min_time = None
        max_time = None
        for test in self.tests:
            min_time = min(min_time, self.tests[test].start_datetime) if min_time else self.tests[test].start_datetime
            max_time = max(max_time, self.tests[test].end_datetime) if max_time else self.tests[test].end_datetime
        self.duration = max_time - self.start_datetime

    @property
    def end_datetime(self):
        assert self.start_datetime, "Чтобы получить время окончания установите дату начала"
        assert self.duration, "Чтобы получить время окончания опыта задайте продолжительность"
        return self.start_datetime + self.duration

    @abstractmethod
    def set_directory(self) -> None:
        pass

class CyclicTest(Test):
    """Опыт циклики"""
    def _get_duration(self, test_file):
        # Считываем файл
        f = open(test_file)
        lines = f.readlines()
        f.close()

        index = (lines[0].split("\t").index("Time"))
        time = np.array(list(map(lambda x: float(x.split("\t")[index]), lines[2:])))

        return timedelta(seconds=np.max(time))

class TestsLogCyclic(TestsLog):
    test_class = CyclicTest
    equipment_names = ["Wille", "Geotech"]
    camera_assembly = CameraAssembly(30, 40)

    def set_directory(self, directory) -> int:
        self.tests = {}
        data = cyclic_path_processing(directory)
        keys = [key for key in data if data[key] is not None]
        if len(data) and len(keys):
            for key in keys:
                self.tests[key] = CyclicTest(data[key])
            return len(self.tests)
        return 0

    def processing_models(self):
        self.tests = {}
        for key in models:
            self.tests[key] = CyclicTest(models[key].test_duration)


class TriaxialStaticTest(Test):
    """Опыт циклики"""
    def _get_duration(self, path):
        f = open(path)
        lines = f.readlines()
        f.close()

        index = (lines[0].split("\t").index("Time"))
        time = np.array(list(map(lambda x: float(x.split("\t")[index]), lines[1:])))

        return timedelta(minutes=np.max(time))

class TestsLogTriaxialStatic(TestsLog):
    test_class = CyclicTest
    equipment_names = ["Geotech", 'лига']
    def set_directory(self, directory) -> int:
        self.tests = {}
        data = FCE_path_processing(directory)
        keys = [key for key in data if data[key]["FC"] is not None or data[key]["E"] is not None]
        if len(data) and len(keys):
            for key in keys:
                if data[key]["E"] is not None:
                    self.tests[key] = TriaxialStaticTest(data[key]["E"])
                if data[key]["FC"] is not None:
                    for i, path in enumerate(data[key]["FC"]):
                        self.tests[f"{key} № {i + 1}"] = TriaxialStaticTest(path)
            return len(self.tests)
        return 0

    def processing_models(self):
        self.tests = {}

        if statment.general_parameters.test_mode == "Трёхосное сжатие (E)" or statment.general_parameters.test_mode == "Трёхосное сжатие с разгрузкой":
            for key in E_models:
                self.tests[key] = TriaxialStaticTest(E_models[key].test_duration)

        if statment.general_parameters.test_mode == "Трёхосное сжатие (F, C)":
            for key in FC_models:
                for i, test in enumerate(FC_models[key]):
                    self.tests[f"{key} № {i + 1}"] = TriaxialStaticTest(test.test_duration)

        elif statment.general_parameters.test_mode == "Трёхосное сжатие (F, C, E)":
            for key in E_models:
                self.tests[key] = TriaxialStaticTest(E_models[key].test_duration)

            for key in FC_models:
                for i, test in enumerate(FC_models[key]):
                    self.tests[f"{key} № {i + 1}"] = TriaxialStaticTest(test.test_duration)

if __name__ == "__main__":
    """test_1 = CyclicTest("C:/Users/Пользователь/Desktop/Тест/Сейсморазжижение/Архив/Темплет В (V7) доп.1-9/Косинусное значение напряжения.txt")
    test_1.start_datetime = 67
    
    test_2 = CyclicTest("C:/Users/Пользователь/Desktop/Тест/Сейсморазжижение/Архив/Темплет В (V7) доп.1-9/Косинусное значение напряжения.txt")
    test_2.duration = timedelta(minutes=500)
    test_2.start_datetime = test_1.end_datetime + timedelta(minutes=20)
    print(test_1)
    print(test_2)"""

    #log = TestsLogCyclic()
    #log.set_directory("C:/Users/Пользователь/Desktop/Тест/Сейсморазжижение/Архив")
    #log.start_datetime = datetime.now()
    #log.processing(work_at_night=False)
    #log.dump('C:/Users/Пользователь/Desktop/data.pickle')

    #with open('C:/Users/Пользователь/Desktop/data.pickle', 'wb') as f:
        #pickle.dump(log, f)

    #log.load('C:/Users/Пользователь/Desktop/data.pickle')
    #print(log)
    log = TestsLogTriaxialStatic()
    log.set_directory("C:/Users/Пользователь/Desktop/Тест/Трёхосное сжатие (F, C, E)/Архив — копия")
    log.start_datetime = datetime.now()
    log.processing(work_at_night=False)
    print(log)
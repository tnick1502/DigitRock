from datetime import datetime, timedelta
from abc import abstractmethod
import numpy as np
from tests_log.path_processing import cyclic_path_processing


class DataTypeValidation:
    """Дескриптор для валидации данных"""
    def __init__(self, data_type):
        self.data_type = data_type

    def __set_name__(self, owner, name):
        self.attr = name

    def __set__(self, instance, value):
        if isinstance(value, self.data_type):
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


class Test:
    """Суперкласс опыта

    Атрибуты:
        start_datetime: Дата начала опыта
        duration: Продолжительность опыта
        additional_data: Дополнительные данные опыта

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

    def __init__(self, test_file: str, additional_data=None):
        self.duration = test_file if isinstance(test_file, timedelta) else self._get_duration(test_file)
        self.additional_data = additional_data

    def __str__(self):

        def timedelta_to_dhms(duration):
            # преобразование в дни, часы, минуты и секунды
            days, seconds = duration.days, duration.seconds
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = (seconds % 60)
            return f'{days} дней {hours} часов {minutes} минут'

        if self.start_datetime and self.end_datetime:
            return f"Дата начала: {self.start_datetime:%H:%M %d.%m.%Y}, Дата окончания: {self.end_datetime:%H:%M %d.%m.%Y}, Продолжительность: {timedelta_to_dhms(self.duration)}"
        else:
            return f"Дата начала: Не установлена, Дата окончания: Не установлена, Продолжительность: {timedelta_to_dhms(self.duration)}"

    @property
    def end_datetime(self):
        assert self.start_datetime, "Чтобы получить время окончания дату начала"
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

    Классы журналов конкретных опытов наследуются от этого класса.

    !!! Необходимо перегрузить метод self.set_directory !!!

    Метод self.set_directory находит все файлы в папке и заполняет словарь self.tests"""

    tests: dict
    test_class: Test = None
    equipment_count: int = DataTypeValidation(int)
    start_datetime: datetime = DataTypeValidation(datetime)
    duration: timedelta = DataTypeValidation(timedelta)
    equipment_splittig: dict = None

    def __init__(self):
            self.tests = {}
            self.duration = timedelta()
            self.equipment_count = 1

    def __iter__(self):
        for key in self.tests:
            yield key

    def __getitem__(self, key):
        assert key in list(self.tests.keys()), f"No test with key {key}"
        return self.tests[key]

    def __setitem__(self, key, value):
        if isinstance(value, self.test_class):
            self.tests[key] = value
        else:
            raise TypeError("value must has type Test")

    def __str__(self):
        return "\n".join(map(lambda key: f"'{key}': {str(self.tests[key])}", list(self.tests.keys())))

    def processing(self):
        assert self.start_datetime, "Не выбрано время начала серии опытов"
        assert len(self.tests), "Не загружено ни одного опыта"
        assert self.equipment_count, "Не задано число стабилометров"

        equipment_splittig = {
            "equipment": {
                f"device_{i}": list() for i in range(1, self.equipment_count + 1)
            }
        }

        keys = list(self.tests.keys())

        # заполняем первую партию
        for i in range(1, self.equipment_count + 1):
            random_key = np.random.choice(keys)
            random_test = object[random_key]  # берем лучайный образец
            equipment_splittig["stab_{}".format(i)].append([random_key, random_test.duration])  # закидываем на стабилометр
            keys = np.delete(keys, random_key)


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
    def set_directory(self, directory):
        data = cyclic_path_processing(directory)
        for key in data:
            self.tests[key] = CyclicTest(data[key])


if __name__ == "__main__":
    '''test_1 = CyclicTest("C:/Users/Пользователь/Desktop/Тест/Сейсморазжижение/Архив/Темплет В (V7) доп.1-9/Косинусное значение напряжения.txt")
    test_1.start_datetime = datetime.now()
    
    test_2 = CyclicTest("C:/Users/Пользователь/Desktop/Тест/Сейсморазжижение/Архив/Темплет В (V7) доп.1-9/Косинусное значение напряжения.txt")
    test_2.duration = timedelta(minutes=500)
    test_2.start_datetime = test_1.end_datetime + timedelta(minutes=20)
    print(test_1)
    print(test_2)'''

    log = TestsLogCyclic()
    log.set_directory("C:/Users/Пользователь/Desktop/Тест/Сейсморазжижение/Архив")
    print(log)
from datetime import datetime
from openpyxl import load_workbook
import pandas as pd
import os
import pyexcel as p
import pickle

from excel_statment.properties_model import PhysicalProperties, MechanicalProperties, PropertiesDict, ConsolidationProperties, CyclicProperties
from descriptors import DataTypeValidation
from excel_statment.position_configs import PhysicalPropertyPosition, MechanicalPropertyPosition, c_fi_E_PropertyPosition, \
    DynamicsPropertyPosition, IdentificationColumns
from excel_statment.functions import str_df, float_df
from general.general_functions import read_json_file, create_json_file
import shelve


class StatmentData:
    """Класс, хранящий данные ведомости"""
    object_name = DataTypeValidation(str)
    customer = DataTypeValidation(str)
    start_date = DataTypeValidation(datetime)
    end_date = DataTypeValidation(datetime)
    accreditation = DataTypeValidation(str)
    accreditation_key = DataTypeValidation(str)
    object_number = DataTypeValidation(str)

    def __init__(self, statment_path):
        wb = load_workbook(statment_path, data_only=True)
        object_name = str(wb["Лист1"]["A2"].value)
        customer = str(wb["Лист1"]["A1"].value)
        accreditation = str(wb["Лист1"]["I2"].value)

        if accreditation in ["OAO", "ОАО"]:
            accreditation = "АО"
        elif accreditation == "OOO":
            accreditation = "ООО"

        object_number = str(wb["Лист1"]["AI1"].value)
        start_date = wb["Лист1"]["U1"].value
        end_date = wb["Лист1"]["Q1"].value
        wb.close()

        assert not isinstance(self.start_date, datetime), "Не установлена дата начала опытов"
        assert not isinstance(self.end_date, datetime), "Не установлена дата окончания опытов"
        assert object_name, "Не указано имя объекта"
        assert customer, "Не указан заказчик"
        assert customer, "Не указан заказчик"
        assert accreditation, "Не указана аккредитация"

        if accreditation in ["AO", "АО"]:
            self.accreditation_key = "новая"
        elif accreditation == "ООО" or accreditation == "OOO":
            self.accreditation_key = "2"

        self.object_name = object_name
        self.customer = customer
        self.accreditation = accreditation
        self.object_number = object_number
        self.start_date = start_date
        self.end_date = end_date

    def __repr__(self):
        return str(self.__dict__)

    def get_json(self):
        return self.__dict__

class GeneralParameters:
    """Класс, хранящий общие свойства по испытаниям"""
    def __init__(self, data: dict):
        for key in data:
            setattr(self, key, data[key])
        if not hasattr(self, "test_mode"):
            setattr(self, "test_mode", None)

    def __repr__(self):
        return str(self.__dict__)

    def get_json(self):
        return self.__dict__

class Test:
    physical_properties = DataTypeValidation(PhysicalProperties)
    mechanical_properties = DataTypeValidation(MechanicalProperties, ConsolidationProperties)

    def __init__(self, test_class=None, data_frame=None, i=None, test_mode=None, K0_mode=None,
                 identification_column=None, physical_properties_dict=None, mechanical_properties_dict=None):
        if physical_properties_dict and mechanical_properties_dict:
            self.physical_properties = PhysicalProperties()
            for attr in physical_properties_dict:
                if attr == "date":
                    if physical_properties_dict[attr] is None:
                        setattr(self.physical_properties, attr, physical_properties_dict[attr])
                    else:
                        setattr(self.physical_properties, attr,
                                datetime.strptime(physical_properties_dict[attr].split(".")[0], "%Y-%m-%d %H:%M:%S"))
                else:
                    setattr(self.physical_properties, attr, physical_properties_dict[attr])

            self.mechanical_properties = test_class()
            for attr in mechanical_properties_dict:
                setattr(self.mechanical_properties, attr, mechanical_properties_dict[attr])

        else:
            self.physical_properties = PhysicalProperties()
            self.physical_properties.defineProperties(data_frame=data_frame, string=i,
                                                          identification_column=identification_column)
            self.mechanical_properties = test_class()
            self.mechanical_properties.defineProperties(self.physical_properties, data_frame=data_frame, string=i,
                                                        test_mode=test_mode, K0_mode=K0_mode)


    def get_json(self):
        return {
            "physical_properties": self.physical_properties.__dict__,
            "mechanical_properties": self.mechanical_properties.__dict__
        }

    def __repr__(self):
        return f"Физические свойства: {self.physical_properties}, Механические свойства {self.mechanical_properties}"

class Statment:
    tests = DataTypeValidation(dict)
    general_data = DataTypeValidation(StatmentData)
    general_parameters = DataTypeValidation(GeneralParameters)
    test_class = None
    current_test: str
    original_keys: list = None

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Statment, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.test_class = None
        self.general_parameters = None
        self.tests = {}
        self.current_test = None

    def setTestClass(self, cls):
        self.test_class = cls

    def setCurrentTest(self, lab):
        self.current_test = lab

    def getLaboratoryNumber(self):
        return self.tests[self.current_test].physical_properties.lab_number

    def readExcelFile(self, excel_path, identification_column):
        self.tests = {}

        assert self.general_parameters, "Определите начальные параметры"

        self.general_data = StatmentData(excel_path)

        data_frame = Statment.createDataFrame(excel_path)

        if not hasattr(self.general_parameters, "K0_mode"):
            self.general_parameters.K0_mode = None

        if data_frame is not None:
            for i in range(len(data_frame["Лаб. № пробы"])):
                self.tests[str_df(data_frame.iat[i, PhysicalPropertyPosition["laboratory_number"][1]])] = \
                    Test(self.test_class, data_frame, i, self.general_parameters.test_mode,
                         self.general_parameters.K0_mode, identification_column)
        self.original_keys = list(self.tests.keys())

    def setGeneralParameters(self, data):
        self.general_parameters = GeneralParameters(data)

    def sort(self, key):
        if key == "origin":
            self.tests = {key: self.tests[key] for key in self.original_keys}
        elif hasattr(self.tests[self.original_keys[0]].physical_properties, key):
            self.tests = dict(sorted(self.tests.items(), key=lambda x: getattr(self.tests[x[0]].physical_properties, key)))
        elif hasattr(self.tests[self.original_keys[0]].mechanical_properties, key):
            self.tests = dict(sorted(self.tests.items(), key=lambda x: getattr(self.tests[x[0]].mechanical_properties, key)))

    def dump(self, directory, name="statment.pickle"):
        general_data = {
            "tests": self.tests,
            "general_data": self.general_data,
            "general_parameters": self.general_parameters,
            "test_class": self.test_class,
            "original_keys": self.original_keys
        }
        with open(directory + "/" + name, "wb") as file:
            pickle.dump(general_data, file)

    def load(self, file):
        with open(file, 'rb') as f:
            data = pickle.load(f)
            self.tests = data["tests"]
            self.general_data = data["general_data"]
            self.general_parameters = data["general_parameters"]
            self.test_class = data["test_class"]
            self.original_keys = data["original_keys"]

    @staticmethod
    def createDataFrame(excel_path, read_xls=False) -> pd.DataFrame:
        """Функция считывания файла excel в датафрейм"""

        def resave_xls_to_xlsx(file):
            """Пересохраняет файл excel из формата xls в xlsx
                    Вернет имя нового файла
                    Если файл уже есть, то вернет его"""

            current_file_name = ""

            if file != "":
                # Проверим наличие документа Exel. Если он в старом формате то пересохраним в новый
                if file[-1] == "x":
                    current_file_name = file
                elif file[-1] == "s":
                    p3 = file + "x"
                    if os.path.exists(p3):
                        current_file_name = file
                        pass
                    else:
                        p.save_book_as(file_name=file,
                                       dest_file_name=p3)  # проверяем есть ли xlsx. Если нет то создаем копию файла в этом формате
                    file = p3
                    current_file_name = file
                else:
                    pass
                current_file_name = file

            return current_file_name

        if (excel_path.endswith("xlsx") or excel_path.endswith("xls")) and not read_xls:
            wb = resave_xls_to_xlsx(excel_path)
        elif excel_path.endswith("xls") and read_xls:
            wb = excel_path
        else:
            return None

        df = pd.read_excel(wb, usecols="A:IV", skiprows=[0, 1, 3, 4, 5])
        df = df[df['Лаб. № пробы'].notna()]

        return df

    def __iter__(self):
        for key in self.tests:
            yield key

    def __getitem__(self, key):
        if not key in list(self.tests.keys()):
            return KeyError(f"No test with key {key}")
        return self.tests[key]

    def __len__(self):
        return len(self.tests)

    def __str__(self):
        customer = f"Общие данные:\n {self.general_data}\n"
        general_parameters = f"Данные опыта:\n {self.general_parameters}\n"
        tests = "Опыты\n" + "\n".join(f"{key}: {self.tests[key]}" for key in self.tests.keys())
        return customer + general_parameters + tests


if __name__ == '__main__':

    s = Statment()
    s.setTestClass(CyclicProperties)
    s.setGeneralParameters({'equipment': 'ЛИГА КЛ-1С', 'test_mode': 'Штормовое разжижение', 'K0_mode': 'K0: По ГОСТ-65353'})
    s.readExcelFile(r"C:\Users\Пользователь\Desktop\Новая папка (4)\987-21 Карское море - шторм.xlsx", None)
    s.dump(r"C:\Users\Пользователь\Desktop\Новая папка (4)")
    print(s)
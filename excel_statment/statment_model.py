from datetime import datetime
from openpyxl import load_workbook
import pandas as pd
import os
import pyexcel as p

from excel_statment.properties_model import PhysicalProperties, MechanicalProperties, CyclicProperties, \
    DataTypeValidation, RCProperties
from loggers.logger import excel_logger, log_this
from excel_statment.position_configs import PhysicalPropertyPosition, MechanicalPropertyPosition, c_fi_E_PropertyPosition, \
    DynamicsPropertyPosition, IdentificationColumns
from excel_statment.functions import str_df, float_df

class StatmentData:
    """Класс, хранящий данные ведомости"""
    object_name = DataTypeValidation(str)
    customer = DataTypeValidation(str)
    start_date = DataTypeValidation(datetime)
    end_date = DataTypeValidation(datetime)
    accreditation = DataTypeValidation(str)
    object_number = DataTypeValidation(str)

    @log_this(excel_logger, "debug")
    def __init__(self, statment_path):
        wb = load_workbook(statment_path, data_only=True)
        object_name = str(wb["Лист1"]["A2"].value)
        customer = str(wb["Лист1"]["A1"].value)
        accreditation = str(wb["Лист1"]["I2"].value)
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

        self.object_name = object_name
        self.customer = customer
        self.accreditation = accreditation
        self.object_number = object_number
        self.start_date = start_date
        self.end_date = end_date

    def __repr__(self):
        return str(self.__dict__)

class GeneralParameters:
    """Класс, хранящий общие свойства по испытаниям"""
    def __init__(self, data: dict):
        for key in data:
            setattr(self, key, data[key])
        if not hasattr(self, "test_mode"):
            setattr(self, "test_mode", None)

    def __repr__(self):
        return str(self.__dict__)

class Test:
    physical_properties = DataTypeValidation(PhysicalProperties)
    mechanical_properties = DataTypeValidation(MechanicalProperties)

    def __init__(self, test_class, data_frame, i, test_mode, K0_mode, identification_column):
        self.physical_properties = PhysicalProperties()
        self.physical_properties.defineProperties(data_frame=data_frame, string=i,
                                                      identification_column=identification_column)
        self.mechanical_properties = test_class()
        self.mechanical_properties.defineProperties(self.physical_properties, data_frame=data_frame, string=i,
                                                    test_mode=test_mode, K0_mode=K0_mode)

    def __repr__(self):
        return f"Физические свойства: {self.physical_properties}, Механические свойства {self.mechanical_properties}"

class Statment:
    tests = DataTypeValidation(dict)
    general_data = DataTypeValidation(StatmentData)
    general_parameters = DataTypeValidation(GeneralParameters)
    test_class = None
    model_class = None
    current_test: str

    def __init__(self, test_class):
        self.test_class = test_class
        self.general_parameters = GeneralParameters(
            {
                "test_mode": "Сейсморазжижение",
                "K0_mode": "K0: K0 = 1"
            }
        )
        self.tests = {}
        self.current_test = None

    @log_this(excel_logger, "debug")
    def readExcelFile(self, excel_path, identification_column):

        assert self.general_parameters, "Определите начальные параметры"

        self.general_data = StatmentData(excel_path)

        data_frame = Statment.createDataFrame(excel_path)

        if data_frame is not None:
            for i in range(len(data_frame["Лаб. № пробы"])):
                self.tests[str_df(data_frame.iat[i, PhysicalPropertyPosition["laboratory_number"][1]])] = \
                    Test(self.test_class, data_frame, i, self.general_parameters.test_mode,
                         self.general_parameters.K0_mode, identification_column)

    def setGeneralParameters(self, data):
        self.general_parameters = GeneralParameters(data)

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
    f = Statment(CyclicProperties)
    f.readExcelFile("C:/Users/Пользователь/Desktop/Тест/818-20 Атомфлот - мех.xlsx", 219)
    print(f)

    # print(getCyclicExcelData("C:/Users/Пользователь/Desktop/Тест/818-20 Атомфлот - мех.xlsx", "Сейсморазжижение", "K0: K0 = 1"))


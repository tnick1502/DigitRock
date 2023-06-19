import pandas as pd

from plaxis_average.statment.descriptor import DataTypeValidation
from plaxis_average.statment.params import params

def read_df(x):
    if str(x) in ['nan', 'NaT', '-']:
        return None
    return x

class Properties:
    borehole = DataTypeValidation(str)
    depth = DataTypeValidation(int)
    ground_name = DataTypeValidation(str)
    EGE = DataTypeValidation(str)
    E50_ref = DataTypeValidation(float)
    Eoed_ref = DataTypeValidation(float)
    Eur_ref = DataTypeValidation(float)
    m = DataTypeValidation(float)
    c = DataTypeValidation(float)
    fi = DataTypeValidation(float)
    dilatancy_angle = DataTypeValidation(float)
    v_ur = DataTypeValidation(float)
    p_ref = DataTypeValidation(float)
    К0nc = DataTypeValidation(float)
    Rf = DataTypeValidation(float)
    OCR = DataTypeValidation(float)
    POP = DataTypeValidation(float)
    sample_number = DataTypeValidation(int)


    def __init__(self):
        for key in Properties.__dict__:
            if isinstance(getattr(Properties, key), DataTypeValidation):
                object.__setattr__(self, key, None)

    def defineProperties(self, data_frame: pd.DataFrame, number: int) -> None:
        """Считывание строки свойств

            :argument data_frame: dataframe excel файла ведомости
            :argument number: номер строки пробы в dataframe
            :return None
        """
        for attr_name in params:
            setattr(self, attr_name, read_df(
                data_frame.iat[number, params[attr_name][1]])
                    )
        self.sample_number = number

    def getData(self) -> dict:
        """Получение всех параметров
        """
        return {
            attr_name: self.__dict__[attr_name] for attr_name in self.__dict__
        }
from dataclasses import dataclass
from openpyxl import load_workbook
import pandas as pd
import numpy as np
import os
from typing import Dict, List
from datetime import datetime
from scipy.interpolate import interp1d, griddata
import pyexcel as p
from general.general_functions import sigmoida, mirrow_element
from cyclic_loading.cyclic_stress_ratio_function import define_fail_cycle
from resonant_column.rezonant_column_function import define_G0_threshold_shear_strain
from cyclic_loading.cyclic_loading_model import ModelTriaxialCyclicLoadingSoilTest



PhysicalPropertyPosition = {
    "laboratory_number": ["A", 0],
    "borehole": ['B', 1],
    "depth": ['C', 2],
    "soil_name": ['D', 3],
    "ige": ['ES', 148],
    "rs": ['P', 15],
    "r": ['Q', 16],
    "rd": ['R', 17],
    "n": ['S', 18],
    "e": ['T', 19],
    "W": ['U', 20],
    "Sr": ['V', 21],
    "Wl": ['W', 22],
    "Wp": ['X', 23],
    "Ip": ['Y', 24],
    "Il": ['Z', 25],
    "Ir": ['AE', 30],
    "stratigraphic_index": ['AH', 34],
    "ground_water_depth": ['AJ', 35],
    "granulometric_10": ['E', 4],
    "granulometric_5": ['F', 5],
    "granulometric_2": ['G', 6],
    "granulometric_1": ['H', 7],
    "granulometric_05": ['I', 8],
    "granulometric_025": ['J', 9],
    "granulometric_01": ['K', 10],
    "granulometric_005": ['L', 11],
    "granulometric_001": ['M', 12],
    "granulometric_0002": ['N', 13],
    "granulometric_0000": ['O', 14],
    "Rc": ['ER', 147],
    "date": ['IF', 239]
}

MechanicalPropertyPosition = {
    "build_press": ['AK', 36],
    "pit_depth": ['AL', 37],
    "OCR":["GB", 183],
    "Cv": ["CC", 80],
    "Ca": ["CF", 83],
    "K0nc": ["GZ", 207],
    "K0oc": ["GY", 206],
    "pressure_array": ["BO", 66]
}

c_fi_E_PropertyPosition = {
    "Трёхосное сжатие (E)": [["BI", "BJ", "BK"], [60, 61, 62]],
    "Трёхосное сжатие (F, C)": [["BF", "BG", "BH"], [57, 58, 59]],
    "Трёхосное сжатие (F, C, E)": [["BC", "BD", "BE"], [54, 55, 56]],
    "Трёхосное сжатие с разгрузкой": [["BL", "BM", "BN"], [63, 64, 65]],
    "Сейсморазжижение": [["BY", "BZ", "CA"], [76, 77, 78]],
    "Штормовое разжижение": [["BY", "BZ", "CA"], [76, 77, 78]],
    "Виброползучесть": [["BS", "BT", "BU"], [70, 71, 72]],
    "Резонансная колонка": [["BC", "BD", "BE"], [54, 55, 56]]
}

DynamicsPropertyPosition = {
    "magnitude": ["AQ", 42],
    "intensity": ["AM", 38],
    "reference_pressure": ["FV", 177],
    "acceleration": ["AP", 41],
    "rw": ["HU", 228],
    "Hw": ["HS", 226],
    "frequency_storm": ["HT", 227],
    "cycles_count_storm": ["HT", 225],
    "frequency_vibration_creep": ["AN", 39],
    "Kd_vibration_creep": ["CB", 79],
    "sigma_d_vibration_creep": ["AO", 40],
}

IdentificationColumns = {
    "Резонансная колонка": 219,
    "Сейсморазжижение": 230,
    "Штормовое разжижение": 230,
}


def float_df(x):
    if str(x) != "nan" and str(x) != "NaT":
        try:
            return float(x)
        except ValueError:
            return x
        except TypeError:
            return x
    else:
        return None

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


@dataclass
class PhysicalProperties:
    """Класс, хранящий свойсва грунтов, которые считываются без обработки"""
    def __init__(self):
        self.laboratory_number: str = None
        self.borehole: str = None
        self.depth: float = None
        self.soil_name: str = None
        self.ige: str = None
        self.rs: float = None
        self.r: float = None
        self.rd: float = None
        self.n: float = None
        self.e: float = None
        self.W: float = None
        self.Sr: float = None
        self.Wl: float = None
        self.Wp: float = None
        self.Ip: float = None
        self.Il: float = None
        self.Ir: float = None
        self.stratigraphic_index: str = None
        self.ground_water_depth: float = None
        self.granulometric_10: float = None
        self.granulometric_5: float = None
        self.granulometric_2: float = None
        self.granulometric_1: float = None
        self.granulometric_05: float = None
        self.granulometric_025: float = None
        self.granulometric_01: float = None
        self.granulometric_005: float = None
        self.granulometric_001: float = None
        self.granulometric_0002: float = None
        self.granulometric_0000: float = None
        self.complete_flag: bool = False
        self.sample_number: int = None
        self.type_ground: int = None
        self.Rc: float = None
        self.date: datetime = None
        self.sample_size: tuple = None

    def definePhysicalProperties(self, data_frame, string, identification_column=None) -> None:
        """Считывание строки свойств"""
        for attr_name in PhysicalPropertyPosition:
            setattr(self, attr_name, float_df(data_frame.iat[string, PhysicalPropertyPosition[attr_name][1]]))

        if identification_column:
            if float_df(data_frame.iat[string, identification_column]):
                self.complete_flag = True
            else:
                self.complete_flag = False

        #if identification_column:
            #cell = wb["Лист1"][identification_column + str(string)]
            #color_in_hex = cell.fill.start_color.index  # this gives you Hexadecimal value of the color
            ## color = tuple(int(color_in_hex[i:i + 2], 16) for i in (0, 2, 4))
            #if color_in_hex == "FF81D8D0":
                #self.complete_flag = True
            #else:
                #self.complete_flag = False

        self.sample_number = string

        new_lab_number = float_df(data_frame.iat[string, 240])
        if new_lab_number:
            self.laboratory_number = new_lab_number

        self.type_ground = PhysicalProperties.define_type_ground(self._granulometric_to_dict(), self.Ip,
                                                                 self.Ir)

        self.sample_size = PhysicalProperties.define_sample_size(self.granulometric_10, self.granulometric_5)

    def getDict(self):
        return self.__dict__

    def setDict(self, data):
        for attr in data:
            setattr(self, attr, data[attr])

    def _granulometric_to_dict(self) -> dict:
        granulometric_dict = {}
        for key in ['10', '5', '2', '1', '05', '025', '01', '005', '001', '0002', '0000']:
            granulometric_dict[key] = getattr(self, "granulometric_" + key)
        return granulometric_dict

    def __str__(self):
        return str(self.__dict__)

    @staticmethod
    def define_type_ground(data_gran: dict, Ip: float, Ir: float) -> int:
        """Функция определения типа грунта через грансостав"""
        none_to_zero = lambda x: 0 if not x else x
        gran_struct = ['10', '5', '2', '1', '05', '025', '01', '005', '001', '0002', '0000']  # гран состав
        accumulate_gran = [none_to_zero(data_gran[gran_struct[0]])]  # Накоплено процентное содержание
        for i in range(10):
            accumulate_gran.append(accumulate_gran[i] + none_to_zero(data_gran[gran_struct[i + 1]]))

        if none_to_zero(Ir) >= 50:  # содержание органического вещества Iom=hg10=Ir
            type_ground = 9  # Торф
        elif none_to_zero(Ip) < 1:  # число пластичности
            if accumulate_gran[2] > 25:
                type_ground = 1  # Песок гравелистый
            elif accumulate_gran[4] > 50:
                type_ground = 2  # Песок крупный
            elif accumulate_gran[5] > 50:
                type_ground = 3  # Песок средней крупности
            elif accumulate_gran[6] >= 75:
                type_ground = 4  # Песок мелкий
            else:
                type_ground = 5  # Песок пылеватый
        elif 1 <= Ip < 7:
            type_ground = 6  # Супесь
        elif 7 <= Ip < 17:
            type_ground = 7  # Суглинок
        else:  # data['Ip'] >= 17:
            type_ground = 8  # Глина

        return type_ground

    @staticmethod
    def define_sample_size(granulometric_10: float, granulometric_5: float) -> tuple:
        """Функция возвращает размеры образца в зависимости от грансостава"""
        granulometric_10 = granulometric_10 if granulometric_10 else 0
        granulometric_5 = granulometric_5 if granulometric_5 else 0

        if granulometric_10 >= 3:
            return 100, 200
        elif granulometric_10 + granulometric_5 >= 3:
            return 50, 100
        else:
            return 38, 76

@dataclass
class MechanicalProperties:
    """Расширенный класс с дополнительными обработанными свойствами"""
    def __init__(self, for_copy=None):
        self.physical_properties: PhysicalProperties = PhysicalProperties()
        self.Cv: float = None
        self.Ca: float = None
        self.m: float = None
        self.E50: float = None
        self.c: float = None
        self.fi: float = None
        self.K0: float = None
        self.dilatancy_angle: float = None
        self.sigma_3: float = None
        self.qf: float = None
        self.sigma_1: float = None
        self.poisons_ratio: float = None
        self.OCR: float = None
        self.build_press: float = None
        self.pit_depth: float = None
        self.Eur: float = None
        self.pressure_array: dict = {
            "set_by_user": None,
            "calculated_by_pressure": None,
            "state_standard": None,
        }

        if for_copy:
            for attr in for_copy.__dict__:
                setattr(self, attr, for_copy.__dict__[attr])

    def __getattr__(self, name):
        """Метод позволяет обращаться к атрибудам физических параметров напрямую"""
        if name in self.__dict__:
            return self.__dict__[name]
        elif name in self.physical_properties.__dict__:
            return self.physical_properties.__dict__[name]
        else:
            raise AttributeError(f"Несуществующий атрибут {name}")

    def __str__(self):
        return str(self.getDict())

    def getDict(self) -> dict:
        data = self.__dict__
        data["physical_properties"] = self.physical_properties.getDict()
        return data

    def setDict(self, data: dict) -> None:
        for attr in data:
            if attr == "physical_properties":
                physical_properties = PhysicalProperties()
                physical_properties.setDict(data[attr])
                setattr(self, "physical_properties", physical_properties)
            else:
                setattr(self, attr, data[attr])

    def defineMechanicalProperties(self, data_frame: pd.DataFrame, string: int, test_mode=None, K0_mode=None,
                                   identification_column=None) -> None:
        """Считывание строки свойств"""
        self.physical_properties = PhysicalProperties()
        self.physical_properties.definePhysicalProperties(data_frame, string, identification_column)

        self.c, self.fi, self.E50 = MechanicalProperties.define_c_fi_E(data_frame, test_mode, string)

        if self.c and self.fi and self.E50:

            self.E50 *= 1000

            Cv = float_df(data_frame.iat[string, MechanicalPropertyPosition["Cv"][1]])
            Ca = float_df(data_frame.iat[string, MechanicalPropertyPosition["Ca"][1]])

            self.m = MechanicalProperties.define_m(self.physical_properties.e, self.physical_properties.Il)
            self.Cv = Cv if Cv else np.round(MechanicalProperties.define_Cv(
                MechanicalProperties.define_kf(self.physical_properties.type_ground, self.physical_properties.e)), 3)
            self.Ca = Ca if Ca else np.round(np.random.uniform(0.01, 0.03), 5)

            self.K0 = MechanicalProperties.define_K0(data_frame, K0_mode, string, self.physical_properties.Il,
                                                         self.fi)

            self.sigma_3 = MechanicalProperties.round_sigma_3(
                MechanicalProperties.define_sigma_3(self.K0, self.physical_properties.depth))

            if self.sigma_3 < 100:
                self.sigma_3 = 100

            self.qf = MechanicalProperties.define_qf(self.sigma_3, self.c, self.fi)
            self. sigma_1 = np.round(self.qf + self.sigma_3, 1)

            self.poisons_ratio = MechanicalProperties.define_poissons_ratio(
                self.physical_properties.Rc,
                self.physical_properties.Ip,
                self.physical_properties.Il,
                self.physical_properties.Ir,
                self.physical_properties.granulometric_10,
                self.physical_properties.granulometric_5,
                self.physical_properties.granulometric_2)

            self.dilatancy_angle = MechanicalProperties.define_dilatancy(
                self.sigma_1, self.sigma_3, self.fi, self.qf, self.E50, self.physical_properties.type_ground,
                self.physical_properties.rs, self.physical_properties.e, self.physical_properties.Il)

            self.build_press = float_df(data_frame.iat[string, MechanicalPropertyPosition["build_press"][1]])
            if self.build_press:
                self.build_press *= 1000

            self.pit_depth = float_df(data_frame.iat[string, MechanicalPropertyPosition["pit_depth"][1]])

            self.OCR = float_df(data_frame.iat[string, MechanicalPropertyPosition["OCR"][1]])
            if not self.OCR:
                self.OCR = 1

            self.Eur = True if test_mode == "Трёхосное сжатие с разгрузкой" else None

            self.pressure_array = {
                "set_by_user": MechanicalProperties.define_reference_pressure_array_set_by_user(
                    float_df(data_frame.iat[string, MechanicalPropertyPosition["pressure_array"][1]])),

                "calculated_by_pressure": MechanicalProperties.define_reference_pressure_array_calculated_by_pressure(
                    self.build_press, self.pit_depth, self.physical_properties.depth, self.K0),

                "state_standard": MechanicalProperties.define_reference_pressure_array_state_standard(
                    self.physical_properties.e, self.physical_properties.Il, self.physical_properties.type_ground)
            }

    @staticmethod
    def round_sigma_3(sigma_3, param=5):
        integer = sigma_3 // param
        remains = sigma_3 % param
        return int(integer * param) if remains < (param / 2) else int(integer * param + param)

    @staticmethod
    def define_m(e: float, Il: float) -> float:
        """Функция расчета параметра m - показатель степени для зависимости жесткости от уровня напряжений
         Входные параметры:
            :param e: пористость
            :param Il: число пластичности"""
        if (not Il or not e):
            return np.round(np.random.uniform(0.5, 0.65), 2)
        else:
            default_Il = [-0.25, 0, 0.25, 0.5, 0.75, 1]
            default_e = [0.5, 0.8, 1.2]
            default_m = [0.5, 0.6, 0.6, 0.7, 0.8, 0.8, 0.4, 0.5, 0.6, 0.7, 0.7, 0.9, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0]

            if Il < default_Il[0]:
                Il = default_Il[0]
            if Il > default_Il[-1]:
                Il = default_Il[-1]
            if e < default_e[0]:
                e = default_e[0]
            if e > default_e[-1]:
                e = default_e[-1]

            default_e_Il = []
            for _e in default_e:
                default_e_Il.extend(list(map(lambda Il: [_e, Il], default_Il)))

            m = griddata(default_e_Il, default_m, (e, Il), method='cubic').item()

            try:
                return np.round(m, 2)
            except:
                np.round(np.random.uniform(0.5, 0.65), 2)

    @staticmethod
    def define_kf(type_ground: int, e) -> float:
        """ Определение коэффициента фильтрации по грансоставу
            :param type_ground: тип грунта
            :param e: коэффициент пористости
            :return: kf в метрах/сутки"""
        e = e if e else np.random.uniform(0.6, 0.7)
        # Функция сигмоиды для kf
        kf_sigmoida = lambda e, e_min, e_max, k_min, k_max: sigmoida(e, amplitude=(k_max - k_min) / 2,
                                                                     x_indent=e_min + (e_max - e_min) / 2,
                                                                     y_indent=k_min + (k_max - k_min) / 2,
                                                                     shape=e_max - e_min)
        # Общие параметры сигмоиды
        e_borders = [0.3, 1.2]

        # Зависимость коэффициента фильтрации от грансостава
        """dependence_kf_on_type_ground = {
            1: kf_sigmoida(e, *e_borders, 8.64, 86.4), # Песок гравелистый
            2: kf_sigmoida(e, *e_borders, 8.64, 86.4), # Песок крупный
            3: kf_sigmoida(e, *e_borders, 0.864, 86.4), # Песок средней крупности
            4: kf_sigmoida(e, *e_borders, 8.64 * 10 ** (-2), 0.864), # Песок мелкий
            5: kf_sigmoida(e, *e_borders, 8.64 * 10 ** (-2), 0.864), # Песок пылеватый
            6: kf_sigmoida(e, *e_borders, 8.64 * 10 ** (-4), 8.64 * 10 ** (-2)), # Супесь
            7: kf_sigmoida(e, *e_borders, 8.64 * 10 ** (-5), 8.64 * 10 ** (-4)), # Суглинок
            8: kf_sigmoida(e, *e_borders, 0.0000001, 8.64 * 10 ** (-5)), # Глина
            9: kf_sigmoida(e, *e_borders, 8.64 * 10 ** (-4), 8.64 * 10 ** (-2)), # Торф
        }"""

        dependence_kf_on_type_ground = {
            1: kf_sigmoida(e, *e_borders, 10, 50),                  # Песок гравелистый
            2: kf_sigmoida(e, *e_borders, 5, 30),                   # Песок крупный
            3: kf_sigmoida(e, *e_borders, 1, 20),                   # Песок средней крупности
            4: kf_sigmoida(e, *e_borders, 0.5, 2),                  # Песок мелкий
            5: kf_sigmoida(e, *e_borders, 10 ** (-2), 10 ** (-1)),  # Песок пылеватый
            6: kf_sigmoida(e, *e_borders, 10 ** (-4), 10 ** (-2)),  # Супесь
            7: kf_sigmoida(e, *e_borders, 10 ** (-5), 10 ** (-4)),  # Суглинок
            8: kf_sigmoida(e, *e_borders, 10 ** (-8), 10 ** (-5)),  # Глина
            9: kf_sigmoida(e, *e_borders, 10 ** (-3), 10 ** (-2)),  # Торф
        }

        return dependence_kf_on_type_ground[type_ground]

    @staticmethod
    def define_Cv(kf: float, m: float = 0.6) -> float:
        """ Определение коэффициента первичной консолидации Сv в см^2/мин
            :param kf: коэффициент фильтрации
            :param m: коэффициент относительной сжимаемости
            :return: Cv в см^2/мин"""

        # Переведем м/сут в см/мин
        kf *= 0.0694444

        # Переведем 1/МПа в 1 / (кгс / см2)
        m /= 10.197162

        # Удельный вес воды в кгс/см3
        gamma = 0.001

        Cv = kf / (m * gamma)

        if Cv > 0.8:
            return np.round(np.random.uniform(0.5, 0.8), 4)
        elif Cv <= 0.02:
            return np.round(np.random.uniform(0.01, 0.02), 4)

        return np.round(Cv, 4)

    @staticmethod
    def define_K0(data_frame: pd.DataFrame, K0_mode: str, string: int, Il: float, fi: float) -> float:
        """Функция определения K0"""
        def define_K0_GOST(Il) -> float:
            if not Il:
                return 0.5
            elif Il < 0:
                return 0.6
            elif 0 <= Il < 0.25:
                return 0.7
            elif 0.25 <= Il < 0.5:
                return 0.8
            else:
                return 1

        def readDataFrame(string, column) -> float:
            K0 = float_df(data_frame.iat[string, column])
            if K0:
                return np.round(K0, 2)
            return np.round(K0, 2) if K0 else None

        dict_K0 = {
            "K0: По ГОСТ-65353": define_K0_GOST(Il),
            "K0: K0nc из ведомости": readDataFrame(string, MechanicalPropertyPosition["K0nc"][1]),
            "K0: K0 из ведомости": readDataFrame(string, MechanicalPropertyPosition["K0oc"][1]),
            "K0: Формула Джекки": np.round((1 - np.sin(np.pi * fi / 180)), 2),
            "K0: K0 = 1": 1
        }

        return dict_K0[K0_mode]

    @staticmethod
    def define_c_fi_E(data_frame: pd.DataFrame, test_mode: str, string: int) -> float:
        """Функция определения K0"""
        return [float_df(data_frame.iat[string, column]) for column in c_fi_E_PropertyPosition[test_mode][1]]

    @staticmethod
    def define_sigma_3(K0: float, depth: float) -> float:
        """Функция определяет обжимающее давление"""
        return round(K0 * (2 * 9.81 * depth), 1)

    @staticmethod
    def define_qf(sigma_3: float, c: float, fi: float) -> float:
        """Функция определяет qf через обжимающее давление и c fi"""
        fi = fi * np.pi / 180
        return np.round((2 * (c * 1000 + (np.tan(fi)) * sigma_3)) / (np.cos(fi) - np.tan(fi) + np.sin(fi) * np.tan(fi)), 1)

    @staticmethod
    def define_poissons_ratio(Rc: float, Ip: float, Il: float, Ir: float, size_10: float, size_5: float,
                              size_2: float) -> float:

        round_ratio = 2  # число знаков после запятой

        check_size = lambda size: size if size else 0
        # Скала
        if Rc:
            if (Rc > 0) and (Rc <= 50):
                return np.round(np.random.uniform(0.22, 0.28), round_ratio)
            elif (Rc > 50) and (Rc <= 150):
                return np.round(np.random.uniform(0.18, 0.25), round_ratio)
            elif (Rc > 150):
                return np.round(np.random.uniform(0.18, 0.25), round_ratio)

        # Крупнообломочный
        if (check_size(size_10) + check_size(size_5) + check_size(size_2)) > 50:
            return np.round(np.random.uniform(0.18, 0.27), round_ratio)

        # Торф
        if Ir:
            if (Ir >= 50):
                return np.round(np.random.uniform(0.35, 0.4), round_ratio)

        # Пески
        if Ip == None:
            return np.round(np.random.uniform(0.25, 0.35), round_ratio)
        # Глины, суглинки
        if Ip:
            if not Il:  # проверка на заполненность
                Il = 0.5

            if Ip >= 17:
                if Il <= 0:
                    return np.round(np.random.uniform(0.2, 0.3), round_ratio)
                elif (Il > 0) and (Il <= 0.25):
                    return np.round(np.random.uniform(0.3, 0.38), round_ratio)
                elif (Il > 0.25) and (Il <= 0.75):
                    return np.round(np.random.uniform(0.35, 0.42), round_ratio)
                elif Il > 0.75:
                    return np.round(np.random.uniform(0.4, 0.47), round_ratio)
            elif (Ip >= 7) and (Ip < 17):
                if Il <= 0:
                    return np.round(np.random.uniform(0.22, 0.32), round_ratio)
                elif (Il > 0) and (Il <= 0.25):
                    return np.round(np.random.uniform(0.28, 0.35), round_ratio)
                elif (Il > 0.25) and (Il <= 0.75):
                    return np.round(np.random.uniform(0.33, 0.4), round_ratio)
                elif Il > 0.75:
                    return np.round(np.random.uniform(0.38, 0.47), round_ratio)
            elif (Ip >= 1) and (Ip < 7):
                if Il <= 0:
                    return np.round(np.random.uniform(0.21, 0.26), round_ratio)
                elif (Il > 0) and (Il <= 0.75):
                    return np.round(np.random.uniform(0.25, 0.32), round_ratio)
                elif Il > 0.75:
                    return np.round(np.random.uniform(0.3, 0.36), round_ratio)
            else:
                return np.round(np.random.uniform(0.25, 0.35), round_ratio)

    @staticmethod
    def define_dilatancy(sigma_1: float, sigma_3: float, fi: float, qf: float, E50: float, type_ground: int, rs: float,
                         e: float, Il: float) -> float:

        def define_dilatancy(sigma_1, sigma_3, fi, OCR, type_ground, rs, e):
            """Определяет угол дилатансии
            data_gran - словарь гран состава
            rs - плотность грунта
            e - коэффициент пористости
            fi - угол внутреннего трения
            OCR - параметр переуплотнения
            """

            def define_ID(type_ground, rs, e):
                """Функция рассчитывает параметр ID"""
                if type_ground == 1:
                    rmin = np.random.uniform(1.55, 1.65)
                    rmax = np.random.uniform(1.75, 1.9)
                elif type_ground == 2:
                    rmin = np.random.uniform(1.55, 1.65)
                    rmax = np.random.uniform(1.75, 1.9)
                elif type_ground == 3:
                    rmin = np.random.uniform(1.5, 1.59)
                    rmax = np.random.uniform(1.7, 1.85)
                elif type_ground == 4:
                    rmin = np.random.uniform(1.4, 1.48)
                    rmax = np.random.uniform(1.6, 1.7)
                elif type_ground == 5:
                    rmin = np.random.uniform(1.3, 1.4)
                    rmax = np.random.uniform(1.55, 1.6)

                if rs == '-':
                    rs = np.random.uniform(0.99 * rmin, 0.99 * rmax)

                emin = (rs - rmax) / rmax
                emax = (rs - rmin) / rmin
                if e == '-':
                    e = np.random.uniform(0.99 * emin, 0.99 * emax)
                if e < emin:
                    e = np.random.uniform(0.99 * emin, 0.99 * emax)

                ID = (emax - e) / (emax - emin)

                return ID

            if not e:
                e = np.random.uniform(0.6, 0.7)

            p = (sigma_1 + 2 * sigma_3) / 3
            if type_ground <= 5:
                ID = define_ID(type_ground, rs, e)
                IR = ID * (10 - np.log(p)) - 1
                angle_of_dilatancy = (3 * IR / 0.8)  # в градусах
            else:
                Mc = (6 * np.sin(np.deg2rad(fi))) / (3 - np.sin(np.deg2rad(fi))) * (
                            (1 / OCR) ** np.random.uniform(0.4, 0.6))
                q = sigma_1 - sigma_3
                n = q / p
                Dmcc = (Mc ** 2 - n ** 2) / (2 * n)
                angle_of_dilatancy = np.rad2deg(np.arcsin(Dmcc / (-2 + Dmcc)))

            return np.round(angle_of_dilatancy, 1)

        def define_dilatancy_from_xc_qres(xc, qres):
            """Определяет угол дилатансии"""
            k_xc = sigmoida(mirrow_element(xc, 0.075), 7, 0.075, 7, 0.15)
            k_qres = sigmoida(mirrow_element(qres, 0.75), 5, 0.75, 8, 0.5)
            angle_of_dilatancy = (k_xc + k_qres)/2
            return round(angle_of_dilatancy, 1)

        def define_xc_qf_E(qf, E50):
            try:
                k = E50 / qf
            except (ValueError, ZeroDivisionError):
                return 0.15

            # Если все норм, то находим Xc
            xc = 1.37 / (k ** 0.8)
            # Проверим значение
            if xc >= 0.15:
                xc = 0.15
            elif xc <= qf / E50:
                xc = qf / E50
            return xc

        def define_k_q(il, e0, sigma3):
            """ Функция определяет насколько выраженный пик на диаграмме
            :param il: показатель текучести
            :param e0: пористость
            :param sigma3: обжимающее напряжение в кПа
            :return: отношение qr к qf
            """
            # Параметры, определяющие распределения
            # Для песков:

            if not e0:
                e0 = np.random.uniform(0.5, 0.7)

            sand_sigma3_min = 100  # размах напряжений (s3) для сигмоиды
            sand_sigma3_max = 1000
            sand_k_e0_min = 0  # значения понижающего коэффициента показателя пористости e0 соответвующее минимальному s3
            sand_k_e0_max = 0.15  # соответствующее макисмальному s3

            sand_e0_red_min = 0.4  # размах приведенной пористости для сигмоиды
            sand_e0_red_max = 0.8
            sand_k_q_min = 0.5  # значения k_q соотв. минимальному e0приведенн
            sand_k_q_max = 0.8  # значения k_q соотв. максимальному e0приведенн

            # Для глин:
            clay_sigma3_min = 100  # размах напряжений (s3) для сигмоиды
            clay_sigma3_max = 1000
            clay_k_il_min = 0  # значения понижающего коэффициента показателя текучести IL соответвующее минимальному s3
            clay_k_il_max = 0.3  # соответствующее макисмальному s3

            clay_il_red_min = 0  # размах приведенного показателя текучести для сигмоиды
            clay_il_red_max = 1
            clay_k_q_min = 0.6  # значения k_q соотв. минимальному ILприведенн
            clay_k_q_max = 0.95  # значения k_q соотв. максимальному ILприведенн

            if not il:  # Пески

                # Заивсимость k_e0 от sigma3
                sand_s3_0 = (sand_sigma3_max + sand_sigma3_min) / 2  # x_0
                sand_shape_s3 = sand_sigma3_max - sand_sigma3_min  # delta x

                k_e0_0 = (sand_k_e0_max + sand_k_e0_min) / 2  # y_0
                amplitude_k_e0 = (sand_k_e0_max - sand_k_e0_min) / 2  # amplitude y

                k_e0 = sigmoida(sigma3, amplitude_k_e0, sand_s3_0, k_e0_0, sand_shape_s3)
                e0_red = e0 - k_e0

                # plot_sigmoida(amplitude_k_e0, sand_s3_0, k_e0_0, sand_shape_s3,
                # sand_sigma3_min, sand_sigma3_max, sigma3, k_e0, 'K_e0 от sigma3')

                # Заивсимость k_q от e0приведенной
                e0_red_0 = (sand_e0_red_max + sand_e0_red_min) / 2  # x0
                shape_e0_red = sand_e0_red_max - sand_e0_red_min

                k_q_0 = (sand_k_q_max + sand_k_q_min) / 2  # y0
                amplitude_k_q = (sand_k_q_max - sand_k_q_min) / 2

                k_q = sigmoida(e0_red, amplitude_k_q, e0_red_0, k_q_0, shape_e0_red)

                # plot_sigmoida(amplitude_k_q, e0_red_0, k_q_0, shape_e0_red,
                # sand_e0_red_min, sand_e0_red_max, e0_red, k_q, 'K_q от e0привед')

            else:  # Глины
                # Заивсимость k_il от sigma3
                clay_s3_0 = (clay_sigma3_max + clay_sigma3_min) / 2  # x_0
                clay_shape_s3 = clay_sigma3_max - clay_sigma3_min  # delta x

                k_il_0 = (clay_k_il_max + clay_k_il_min) / 2  # y_0
                amplitude_k_il = (clay_k_il_max - clay_k_il_min) / 2  # amplitude y

                k_il = sigmoida(sigma3, amplitude_k_il, clay_s3_0, k_il_0, clay_shape_s3)
                il_red = il - k_il

                # plot_sigmoida(amplitude_k_il, clay_s3_0, k_il_0, clay_shape_s3,
                # clay_sigma3_min, clay_sigma3_max, sigma3, k_il, 'K_IL от sigma3')

                # Заивсимость k_q от IL приведенной
                il_red_0 = (clay_il_red_max + clay_il_red_min) / 2  # x0
                shape_il_red = clay_il_red_max - clay_il_red_min

                k_q_0 = (clay_k_q_max + clay_k_q_min) / 2  # y0
                amplitude_k_q = (clay_k_q_max - clay_k_q_min) / 2

                k_q = sigmoida(il_red, amplitude_k_q, il_red_0, k_q_0, shape_il_red)

                # plot_sigmoida(amplitude_k_q, il_red_0, k_q_0, shape_il_red,
                # clay_il_red_min, clay_il_red_max, il_red, k_q, 'K_IL от sigma3')

            return k_q

        def define_OCR_from_xc(xc):
            return 5.5 - 30 * xc

        return np.round((define_dilatancy_from_xc_qres(define_xc_qf_E(qf, E50),
                                                       define_k_q(Il, e,
                                                                  sigma_3)) + define_dilatancy(sigma_1, sigma_3, fi,
                                                                                               define_OCR_from_xc(
                                                                                                   define_xc_qf_E(qf,
                                                                                                                  E50)),
                                                                                               type_ground, rs, e)) / 2,
                        2)

    @staticmethod
    def define_reference_pressure_array_state_standard(e: float, Il: float, type_ground: int) -> list:
        """Функция рассчета обжимающих давлений для кругов мора"""
        e = e if e else 0.65
        Il = Il if Il else 0.5

        if (type_ground == 1) or (type_ground == 2) or (type_ground == 3 and e <= 0.55) or (
                type_ground == 8 and Il <= 0.25):
            return [100, 300, 500]

        elif (type_ground == 3 and (0.7 >= e > 0.55)) or (type_ground == 4 and e <= 0.75) or (
                (type_ground == 6 or type_ground == 7) and Il <= 0.5) or (
                type_ground == 8 and (0.25 < Il <= 0.5)):
            return [100, 200, 300]

        elif (type_ground == 3 and e > 0.7) or (
                type_ground == 4 and e > 0.75) or (type_ground == 5) or (
                (type_ground == 6 or type_ground == 7 or type_ground == 8) and Il > 0.5):
            return [100, 150, 200]

        elif type_ground == 9:
            return [50, 75, 100]

    @staticmethod
    def define_reference_pressure_array_calculated_by_pressure(build_press: float, pit_depth: float, depth: float,
                                                               K0: float) -> list:
        """Функция рассчета обжимающих давлений для кругов мора"""
        if build_press and pit_depth:
            sigma_max = 2 * (depth - pit_depth) * 10 + build_press if (depth - pit_depth) > 0 else 2 * 10 * depth

            sigma_max_1 = MechanicalProperties.round_sigma_3(sigma_max * K0)
            sigma_max_2 = MechanicalProperties.round_sigma_3(sigma_max * K0 * 0.5)
            sigma_max_3 = MechanicalProperties.round_sigma_3(sigma_max * K0 * 0.25)

            return [sigma_max_3, sigma_max_2, sigma_max_1] if sigma_max_3 >= 100 else [100, 200, 400]
        else:
            return None

    @staticmethod
    def define_reference_pressure_array_set_by_user(val) -> list:
        if val is None:
            return None
        else:
            val = list(map(lambda val: int(float(val.replace(",", ".").strip(" ")) * 1000), val.split("/")))
            return val


@dataclass
class RCData(MechanicalProperties):
    """Расширенный класс с дополнительными обработанными свойствами"""
    def __init__(self):
        self.reference_pressure: float = None
        self.G0: float = None
        self.threshold_shear_strain: float = None

    def defineProperties(self, data_frame: pd.DataFrame, string: int, K0_mode: str) -> None:
        super().defineMechanicalProperties(data_frame, string, test_mode="Резонансная колонка", K0_mode=K0_mode,
                                   identification_column=IdentificationColumns["Резонансная колонка"])

        if self.c and self.fi and self.E50:
            self.reference_pressure = float_df(data_frame.iat[string,
                                                          DynamicsPropertyPosition["reference_pressure"][1]])
            self.G0, self.threshold_shear_strain = define_G0_threshold_shear_strain(
                self.reference_pressure, self.E50, self.c, self.fi, self.K0, self.physical_properties.type_ground,
                self.physical_properties.Ip, self.physical_properties.e)

@dataclass
class CyclicData(MechanicalProperties):
    """Расширенный класс с дополнительными обработанными свойствами"""
    def __init__(self):
        self.CSR: float = None
        self.t: float = None
        self.N: float = None
        self.I: float = None
        self.magnitude: float = None
        self.acceleration: float = None
        self.intensity: float = None
        self.cycles_count: int = None
        self.rd: float = None
        self.MSF: float = None
        self.rw: float = None
        self.Hw: float = None
        self.frequency: float = None
        self.Mcsr: float = None
        self.Msf: float = None
        self.n_fail: int = None

    def defineProperties(self, data_frame, string, test_mode, K0_mode) -> None:
        super().defineMechanicalProperties(data_frame, string, test_mode=test_mode, K0_mode=K0_mode,
                                           identification_column=IdentificationColumns[test_mode])
        if self.c and self.fi and self.E50:

            if self.physical_properties.depth <= 9.15:
                self.rd = str(round((1 - (0.00765 * self.physical_properties.depth)), 3))
            elif (self.physical_properties.depth > 9.15) and (self.physical_properties.depth < 23):
                self.rd = str(round((1.174 - (0.0267 * self.physical_properties.depth)), 3))
            else:
                self.rd = str(round((1.174 - (0.0267 * 23)), 3))

            if test_mode == "Сейсморазжижение":
                if self.physical_properties.depth <= self.physical_properties.ground_water_depth:
                    self.sigma_1 = round(2 * 9.81 * self.physical_properties.depth)
                elif self.physical_properties.depth > self.physical_properties.ground_water_depth:
                    self.sigma_1 = round(2 * 9.81 * self.physical_properties.depth - (
                            9.81 * (self.physical_properties.depth - self.physical_properties.ground_water_depth)))

                if self.sigma_1 < 10:
                    self.sigma_1 = 10

                self.sigma_3 = np.round(self.sigma_1 * self.K0)

                self.acceleration = float_df(data_frame.iat[string, DynamicsPropertyPosition["acceleration"][1]]) # В долях g
                if self.acceleration:
                    self.acceleration = np.round(self.acceleration, 3)
                    self.intensity = CyclicData.define_intensity(self.acceleration)
                else:
                    self.intensity = float_df(data_frame.iat[string, DynamicsPropertyPosition["intensity"][1]])
                    self.acceleration = CyclicData.define_acceleration(self.intensity)

                self.magnitude = float_df(data_frame.iat[string, DynamicsPropertyPosition["magnitude"][1]])

                self.t = np.round(0.65 * self.acceleration * self.sigma_1 * float(self.rd))
                self.MSF = np.round((10 ** (2.24) / ((self.magnitude) ** (2.56))), 2)
                self.t *= self.MSF
                if self.t < 1:
                    self.t = 1
                self.t = np.round(self.t)

                self.cycles_count = CyclicData.define_cycles_count(self.magnitude)

                self.frequency = 0.5

            if test_mode == "Штормовое разжижение":
                self.rw = float_df(data_frame.iat[string, DynamicsPropertyPosition["rw"][1]])
                self.Hw = float_df(data_frame.iat[string, DynamicsPropertyPosition["Hw"][1]])

                self.t = np.round((0.5 * self.Hw * self.rw) / 2)

                self.sigma_1 = np.round((2 - (self.rw / 10)) * 9.81 * self.physical_properties.depth)
                if self.sigma_1 < 10:
                    self.sigma_1 = 10

                self.sigma_3 = np.round(self.sigma_1 * self.K0)

                self.cycles_count = int(float_df(data_frame.iat[string, DynamicsPropertyPosition["cycles_count_storm"][1]]))

                self.frequency = float_df(data_frame.iat[string, DynamicsPropertyPosition["frequency_storm"][1]])


            self.n_fail, self.Mcsr = define_fail_cycle(self.cycles_count, self.sigma_1, self.t,
                                                       self.physical_properties.Ip,
                                                       self.physical_properties.Il, self.physical_properties.e)
            if self.n_fail:
                if (self.sigma_1 - self.sigma_3) <= 1.5 * self.t:
                    self.Ms = np.round(np.random.uniform(100, 500), 2)
                else:
                    self.Ms = np.round(np.random.uniform(0.7, 0.9), 2)
            else:
                self.Ms = ModelTriaxialCyclicLoadingSoilTest.define_Ms(
                    self.c, self.fi, self.Mcsr, self.sigma_3, self.sigma_1, self.t, self.cycles_count,
                    self.physical_properties.e, self.physical_properties.Il)

            self.CSR = np.round(self.t / self.sigma_1, 2)

    @staticmethod
    def define_acceleration(intensity: float) -> float:
        y1 = np.array([0, 0.1, 0.16, 0.24, 0.33, 0.82])
        x1 = np.array([0, 6, 7, 8, 9, 10])
        Ainter = interp1d(x1, y1, kind='cubic')
        return Ainter(intensity)

    @staticmethod
    def define_intensity(a: float) -> float:
        amax = a * 9.81
        x1 = np.array([0, 0.1 * 9.81, 0.16 * 9.81, 0.24 * 9.81, 0.33 * 9.81, 0.82 * 9.81])
        y1 = np.array([0, 6, 7, 8, 9, 10])
        return np.round(np.interp(amax, x1, y1), 1)

    @staticmethod
    def define_cycles_count(magnitude: float) -> int:
        if 0 < magnitude <= 12:
            y2 = np.array([0, 3, 5, 10, 15, 26, 90])
            x2 = np.array([0, 5.25, 6, 6.75, 7.5, 8.5, 12])
            Ninter = interp1d(x2, y2, kind='cubic')
            N = int(Ninter(magnitude)) + 1
            if N == 0:
                N = 1
        else:
            N = 5
        return N

@dataclass
class VibrationCreepData(MechanicalProperties):
    """Расширенный класс с дополнительными обработанными свойствами"""
    def __init__(self, for_copy=None):
        self.Kd: List = None
        self.frequency: List = None
        self.n_fail: int = None
        self.Mcsr: float = np.random.uniform(300, 500)
        self.t: float = None
        self.Ms: float = np.random.uniform(300, 500)
        self.cycles_count: int = None

        if for_copy:
            for attr in for_copy.__dict__:
                setattr(self, attr, for_copy.__dict__[attr])

    def defineProperties(self, data_frame, string: int, K0_mode: str) -> None:
        super().defineMechanicalProperties(data_frame, string, test_mode="Виброползучесть", K0_mode=K0_mode,
                                   identification_column=IdentificationColumns["Резонансная колонка"])
        if self.c and self.fi and self.E50:
            frequency = data_frame.iat[string, DynamicsPropertyPosition["frequency_vibration_creep"][1]]
            Kd = data_frame.iat[string, DynamicsPropertyPosition["Kd_vibration_creep"][1]]

            self.t = np.round(
                float_df(data_frame.iat[string, DynamicsPropertyPosition["sigma_d_vibration_creep"][1]]) / 2, 1)

            self.frequency = VibrationCreepData.val_to_list(frequency)
            if str(Kd) == "nan":
                self.Kd = [VibrationCreepData.define_Kd(
                    self.qf, self.t, self.physical_properties.e, self.physical_properties.Il, frequency) for frequency
                    in self.frequency]
            else:
                self.Kd = VibrationCreepData.val_to_list(Kd)

            """self.frequency = [float(frequency)] if str(frequency).isdigit() else list(map(
                lambda frequency: float(frequency.replace(",", ".").strip(" ")), frequency.split(";")))
            self.Kd = [float(Kd)] if str(Kd).isdigit() else list(map(lambda Kd: float(Kd.replace(",", ".").strip(" ")),
                                                                     Kd.split(";")))"""

            self.cycles_count = int(np.random.uniform(2000, 5000))

    @staticmethod
    def val_to_list(val) -> list:
        if val is None:
            return None
        else:
            try:
                val = [float(val)]
            except ValueError:
                val = list(map(lambda val: float(val.replace(",", ".").strip(" ")), val.split(";")))
            return val

    @staticmethod
    def define_Kd(qf: float, t: float, e: float, Il: float, frequency: float) -> float:
        """Функция рассчета Kd"""
        Kd = 1

        e = e if e else np.random.uniform(0.5, 0.6)
        Il = Il if Il else 0.5

        load_dependence = sigmoida(mirrow_element((4*t)/qf, 0.5), 0.5, 0.5, 0.5, 1.2)
        e_dependence = sigmoida(mirrow_element(e, 0.5), 0.2, 0, 0.8, 1.8)
        Il_dependence = sigmoida(mirrow_element(Il, 0.5), 0.1, 0.3, 0.9, 1)
        frequency_dependence = sigmoida(mirrow_element(frequency, 50), 0.1, 40, 0.9, 120)

        Kd *= load_dependence * e_dependence * Il_dependence * frequency_dependence * np.random.uniform(0.98, 1.02)

        return np.round(Kd, 2)



def getMechanicalExcelData(excel: str, test_mode: str, K0_mode: str) -> dict:
    df = createDataFrame(excel)

    identification_column = None

    data = {}
    if df is not None:
        for i in range(len(df["Лаб. № пробы"])):
            m_data = MechanicalProperties()
            m_data.defineMechanicalProperties(data_frame=df, string=i, test_mode=test_mode, K0_mode=K0_mode,
                                              identification_column=identification_column)
            if m_data.E50:
                data[m_data.laboratory_number] = m_data
    return data

def getRCExcelData(excel: str, K0_mode: str) -> dict:
    df = createDataFrame(excel)
    data = {}
    if df is not None:
        for i in range(len(df["Лаб. № пробы"])):
            rc_data = RCData()
            rc_data.defineProperties(df, i, K0_mode)
            if rc_data.E50:
                data[rc_data.laboratory_number] = rc_data
    return data

def getCyclicExcelData(excel: str, test_mode: str, K0_mode: str) -> dict:
    df = createDataFrame(excel)
    data = {}
    if df is not None:
        for i in range(len(df["Лаб. № пробы"])):
            cyclic_data = CyclicData()
            cyclic_data.defineProperties(df, i, test_mode, K0_mode)
            if cyclic_data.E50:
                data[cyclic_data.laboratory_number] = cyclic_data
    return data

def getVibrationCreepExcelData(excel: str, K0_mode: str) -> dict:
    df = createDataFrame(excel)
    data = {}
    if df is not None:
        for i in range(len(df["Лаб. № пробы"])):
            vb_data = VibrationCreepData()
            vb_data.defineProperties(df, i, K0_mode=K0_mode)
            if vb_data.E50:
                data[vb_data.laboratory_number] = vb_data
    return data


def dataToDict(data: dict) -> dict:
    """Функция сохраняет структуру данных как словарь"""
    dict_data = {}
    for key in data:
        dict_data[key] = data[key].getDict()
    return dict_data

def dictToData(dict: dict, data_type) -> object:
    """Функция перегоняет словарь в структуру данных"""
    data = {}
    for key in dict:
        data[key] = data_type()
        data[key].setDict(dict[key])
    return data


if __name__ == '__main__':
    data = getCyclicExcelData("C:/Users/Пользователь/Desktop/Тест/818-20 Атомфлот - мех.xlsx", test_mode="Штормовое разжижение", K0_mode="K0: По ГОСТ-65353")

    print(data['7а-1'].Ms, data['7а-1'].Mcsr)

    #print(data)
    #x = dataToDict(data)
    #print(x)

    #d = dictToData(x, CyclicData)


    #print(getCyclicExcelData("C:/Users/Пользователь/Desktop/Тест/818-20 Атомфлот - мех.xlsx", "Сейсморазжижение", "K0: K0 = 1"))









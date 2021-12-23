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
from loggers.logger import app_logger, log_this

from excel_statment.position_configs import PhysicalPropertyPosition, MechanicalPropertyPosition, c_fi_E_PropertyPosition, \
    DynamicsPropertyPosition, IdentificationColumns
from excel_statment.functions import str_df, float_df, date_df
from descriptors import DataTypeValidation

class PhysicalProperties:
    """Класс, хранящий свойсва грунтов, которые считываются без обработки"""
    laboratory_number = DataTypeValidation(str)
    borehole = DataTypeValidation(str)
    depth = DataTypeValidation(float, int)
    soil_name = DataTypeValidation(str)
    ige = DataTypeValidation(str)
    rs = DataTypeValidation(float, int)
    r = DataTypeValidation(float, int)
    rd = DataTypeValidation(float, int)
    n = DataTypeValidation(float, int)
    e = DataTypeValidation(float, int)
    W = DataTypeValidation(float, int)
    Sr = DataTypeValidation(float, int)
    Wl = DataTypeValidation(float, int)
    Wp = DataTypeValidation(float, int)
    Ip = DataTypeValidation(float, int)
    Il = DataTypeValidation(float, int)
    Ir = DataTypeValidation(float, int)
    stratigraphic_index = DataTypeValidation(str)
    ground_water_depth = DataTypeValidation(float, int)
    granulometric_10 = DataTypeValidation(float, int)
    granulometric_5 = DataTypeValidation(float, int)
    granulometric_2 = DataTypeValidation(float, int)
    granulometric_1 = DataTypeValidation(float, int)
    granulometric_05 = DataTypeValidation(float, int)
    granulometric_025 = DataTypeValidation(float, int)
    granulometric_01 = DataTypeValidation(float, int)
    granulometric_005 = DataTypeValidation(float, int)
    granulometric_001 = DataTypeValidation(float, int)
    granulometric_0002 = DataTypeValidation(float, int)
    granulometric_0000 = DataTypeValidation(float, int)
    complete_flag = DataTypeValidation(bool)
    sample_number = DataTypeValidation(int)
    type_ground = DataTypeValidation(int)
    Rc = DataTypeValidation(float, int)
    date = DataTypeValidation(datetime)
    sample_size = DataTypeValidation(tuple, list)
    new_laboratory_number = DataTypeValidation(str)

    def __init__(self):
        self._setNone()

    def _setNone(self):
        """Поставим изначально везде None"""
        for key in PhysicalProperties.__dict__:
            if isinstance(getattr(PhysicalProperties, key), DataTypeValidation):
                object.__setattr__(self, key, None)

    @log_this(app_logger, "debug")
    def defineProperties(self, data_frame, string, identification_column=None) -> None:
        """Считывание строки свойств"""
        for attr_name in PhysicalPropertyPosition:
            if attr_name in ["laboratory_number", "borehole", "soil_name", "ige", "stratigraphic_index", "new_laboratory_number"]:
                setattr(self, attr_name, str_df(data_frame.iat[string, PhysicalPropertyPosition[attr_name][1]]))
            elif attr_name in ["date"]:
                setattr(self, attr_name, date_df(data_frame.iat[string, PhysicalPropertyPosition[attr_name][1]]))
            else:
                setattr(self, attr_name, float_df(data_frame.iat[string, PhysicalPropertyPosition[attr_name][1]]))

        if identification_column:
            if float_df(data_frame.iat[string, identification_column]):
                self.complete_flag = True
            else:
                self.complete_flag = False

        self.sample_number = string

        self.type_ground = PhysicalProperties.define_type_ground(self._granulometric_to_dict(), self.Ip,
                                                                 self.Ir)

        self.sample_size = PhysicalProperties.define_sample_size(self.granulometric_10, self.granulometric_5)

        if self.laboratory_number.isdigit():
            self.laboratory_number = str(int(self.laboratory_number))

        try:
            borehole = float(self.borehole)

            if borehole % 1 < 0.001:
                self.borehole = str(borehole)
            else:
                self.borehole = str(int(borehole))
        except:
            pass

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

    def __repr__(self):
        return str(self.__dict__)

    @property
    def lab_number(self):
        if self.new_laboratory_number:
            return self.new_laboratory_number
        else:
            return self.laboratory_number

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

class MechanicalProperties:
    """Расширенный класс с дополнительными обработанными свойствами"""
    Cv = DataTypeValidation(float, int)
    Ca = DataTypeValidation(float, int)
    m = DataTypeValidation(float, int)
    u = DataTypeValidation(float, int, np.int32)
    E50 = DataTypeValidation(float, int)
    c = DataTypeValidation(float, int)
    fi = DataTypeValidation(float, int)
    K0 = DataTypeValidation(float, int)
    dilatancy_angle = DataTypeValidation(float, int)
    sigma_3 = DataTypeValidation(float, int, np.int32)
    qf = DataTypeValidation(float, int)
    sigma_1 = DataTypeValidation(float, int, np.int32)
    poisons_ratio = DataTypeValidation(float, int)
    OCR = DataTypeValidation(float, int)
    build_press = DataTypeValidation(float, int)
    pit_depth = DataTypeValidation(float, int)
    Eur = DataTypeValidation(float, int)
    u = DataTypeValidation(list, float, int, np.int32)
    pressure_array: dict = {
        "set_by_user": None,
        "calculated_by_pressure": None,
        "state_standard": None,
        "current": None
    }

    def __init__(self):

        self._setNone()

        self.pressure_array: dict = {
            "set_by_user": None,
            "calculated_by_pressure": None,
            "state_standard": None,
        }

    def _setNone(self):
        """Поставим изначально везде None"""
        for key in MechanicalProperties.__dict__:
            if isinstance(getattr(MechanicalProperties, key), DataTypeValidation):
                object.__setattr__(self, key, None)

    def __repr__(self):
        return str(self.getDict())

    def getDict(self) -> dict:
        data = self.__dict__
        return data

    def setDict(self, data: dict) -> None:
        for attr in data:
            setattr(self, attr, data[attr])

    @log_this(app_logger, "debug")
    def defineProperties(self, physical_properties, data_frame: pd.DataFrame, string: int,
                         test_mode=None, K0_mode=None) -> None:
        """Считывание строки свойств"""
        if test_mode == "Трёхосное сжатие КН":
            self.c, self.fi, self.E50, self.u = MechanicalProperties.define_c_fi_E(data_frame, test_mode, string)
        else:
            self.c, self.fi, self.E50 = MechanicalProperties.define_c_fi_E(data_frame, test_mode, string)

        if self.c and self.fi and self.E50:

            self.E50 *= 1000

            Cv = float_df(data_frame.iat[string, MechanicalPropertyPosition["Cv"][1]])
            Ca = float_df(data_frame.iat[string, MechanicalPropertyPosition["Ca"][1]])

            self.m = MechanicalProperties.define_m(physical_properties.e, physical_properties.Il)
            self.Cv = Cv if Cv else np.round(MechanicalProperties.define_Cv(
                MechanicalProperties.define_kf(physical_properties.type_ground, physical_properties.e)), 3)
            self.Ca = Ca if Ca else np.round(np.random.uniform(0.01, 0.03), 5)

            self.K0 = MechanicalProperties.define_K0(data_frame, K0_mode, string, physical_properties.Il,
                                                     self.fi)

            self.sigma_3 = MechanicalProperties.round_sigma_3(
                MechanicalProperties.define_sigma_3(self.K0, physical_properties.depth))

            if self.sigma_3 < 100:
                self.sigma_3 = 100

            self.qf = np.round(float(MechanicalProperties.define_qf(self.sigma_3, self.c, self.fi) * np.random.uniform(0.95, 1.05)), 1)

            self.sigma_1 = np.round(self.qf + self.sigma_3, 1)

            self.poisons_ratio = MechanicalProperties.define_poissons_ratio(
                physical_properties.Rc,
                physical_properties.Ip,
                physical_properties.Il,
                physical_properties.Ir,
                physical_properties.granulometric_10,
                physical_properties.granulometric_5,
                physical_properties.granulometric_2)

            #self.dilatancy_angle = MechanicalProperties.define_dilatancy(
                #self.sigma_1, self.sigma_3, self.fi, self.qf, self.E50, physical_properties.type_ground,
                #physical_properties.rs, physical_properties.e, physical_properties.Il)

            self.dilatancy_angle = MechanicalProperties.define_dilatancy(
                physical_properties.type_ground, physical_properties.e, physical_properties.Il, physical_properties.Ip) * np.random.uniform(0.9, 1.1)

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
                    self.build_press, self.pit_depth, physical_properties.depth, self.K0),

                "state_standard": MechanicalProperties.define_reference_pressure_array_state_standard(
                    physical_properties.e, physical_properties.Il, physical_properties.type_ground)
            }
            if self.pressure_array["set_by_user"] is not None:
                self.pressure_array["current"] = self.pressure_array["set_by_user"]
            elif self.pressure_array["calculated_by_pressure"] is not None:
                self.pressure_array["current"] = self.pressure_array["calculated_by_pressure"]
            elif self.pressure_array["state_standard"] is not None:
                self.pressure_array["current"] = self.pressure_array["state_standard"]

            if self.pressure_array["calculated_by_pressure"] is None:
                self.pressure_array["calculated_by_pressure"] = \
                    MechanicalProperties.define_reference_pressure_array_calculated_by_referense_pressure(self.sigma_3)

            if test_mode == "Трёхосное сжатие КН":
                self.u = [np.round(self.u * np.random.uniform(0.8, 0.9) * (i / max(self.pressure_array["current"])), 1) for i in self.pressure_array["current"][:-1]] + [self.u]
            elif test_mode == "Трёхосное сжатие НН":
                self.u = [np.round(i * np.random.uniform(0.85, 0.95), 1) for i in self.pressure_array["current"]]

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
            1: kf_sigmoida(e, *e_borders, 10, 50),  # Песок гравелистый
            2: kf_sigmoida(e, *e_borders, 5, 30),  # Песок крупный
            3: kf_sigmoida(e, *e_borders, 1, 20),  # Песок средней крупности
            4: kf_sigmoida(e, *e_borders, 0.5, 2),  # Песок мелкий
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
        elif Cv <= 0.01:
            return np.round(np.random.uniform(0.005, 0.01), 4)

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
        return np.round((2 * (c * 1000 + (np.tan(fi)) * sigma_3)) / (np.cos(fi) - np.tan(fi) + np.sin(fi) * np.tan(fi)),
                        1)

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
    def define_dilatancy_old(sigma_1: float, sigma_3: float, fi: float, qf: float, E50: float, type_ground: int, rs: float,
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
            angle_of_dilatancy = (k_xc + k_qres) / 2
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
    def define_dilatancy(type_ground: int, e: float, Il: float, Ip: float) -> float:
        """ Определение угла дилатснии в зависимости от типа грунта
            :param type_ground: тип грунта
            :param e: коэффициент пористости
            :param Il: показатель текучести
            :param Il: число пластичности
            :return: угол дилатансии [градусы]"""

        def define_dilatancy_for_clay(Il, Ip):
            """Функция расчета параметра угла дилатансии для супесей, суглинков, глин и тофов"""

            default_Ip = [1, 7, 12, 17, 24, 40]  # столбец
            default_Il = [-0.5, -0.25, 0, 0.25, 0.5, 0.75, 1, 1.5]  # строка

            default_angle_of_dilatancy = [7, 4, 3, 2, 2, 0,
                                          6, 4, 3, 2, 2, -1,
                                          3, 2, 1, 0, 1, -2,
                                          2, 2, 1, 0, 0, -3,
                                          1, 1, 0, -2, -3, -4,
                                          -1, -2, -2, -3, -4, -5,
                                          -0.3, -4, -6, -7, -8, -10,
                                          -3, -4, -6, -7, -8, -10]
            if Il is None:
                Il = np.random.uniform(0, 0.75)
            if Ip is None:
                Ip = np.random.uniform(12, 17)

            if Il < default_Il[0]:
                Il = default_Il[0]
            if Il > default_Il[-1]:
                Il = default_Il[-1]
            if Ip < default_Ip[0]:
                Ip = default_Ip[0]
            if Ip > default_Ip[-1]:
                Ip = default_Ip[-1]

            default_Ip_Il = []
            for _Il in default_Il:
                default_Ip_Il.extend(list(map(lambda Ip: [_Il, Ip], default_Ip)))

            angle_of_dilatancy = griddata(default_Ip_Il, default_angle_of_dilatancy, (Il, Ip), method='cubic').item()
            return np.round(angle_of_dilatancy, 2)

        def define_dilatacy_for_sand(angle_of_dilatancy_array, e):
            """Функция расчета угла дилатнсии для песков"""

            e_array = np.array([0.3, 0.5, 0.7, 0.9])
            if e is None:
                e = np.random.uniform(0.5, 0.7)
            if e < e_array[0]:
                e = e_array[0]
            if e > e_array[-1]:
                e = e_array[-1]

            return np.interp(e, e_array, angle_of_dilatancy_array)

        e = e if e else np.random.uniform(0.6, 0.7)
        Ip = Ip if Ip else np.random.uniform(10, 20)
        Il = Il if Il else np.random.uniform(0, 0.3)

        dependence_angle_of_dilatancy_on_type_ground = {
            1: define_dilatacy_for_sand(np.array([23, 18, 13, 11]), e),  # Песок гравелистый
            2: define_dilatacy_for_sand(np.array([14, 10, 6, 5]), e),  # Песок крупный
            3: define_dilatacy_for_sand(np.array([12, 9, 7, 4]), e),  # Песок средней крупности
            4: define_dilatacy_for_sand(np.array([8, 6, 4, 3]), e),  # Песок мелкий
            5: define_dilatacy_for_sand(np.array([5, 4, 3, 2]), e),  # Песок пылеватый
            6: define_dilatancy_for_clay(Il, Ip),  # Супесь
            7: define_dilatancy_for_clay(Il, Ip),  # Суглинок
            8: define_dilatancy_for_clay(Il, Ip),  # Глина
            9: define_dilatancy_for_clay(Il, 40),  # Торф
        }

        return dependence_angle_of_dilatancy_on_type_ground[type_ground]

    @staticmethod
    def define_dilatancy_1(type_ground: int, e: float, Il: float, Ip: float) -> float:

        def type_1():
            return np.random.uniform(15, 25)

        def type_2():
            return np.random.uniform(10, 20)

        def type_3():
            return np.random.uniform(5, 10)

        def type_4():
            return np.random.uniform(3, 7)

        def type_5():
            return np.random.uniform(0, 20)

        def type_6():
            return np.random.uniform(0, 20)

        def type_7():
            return np.random.uniform(0, 20)

        def type_8():
            return np.random.uniform(0, 20)

        def type_9():
            return np.random.uniform(0, 20)

        dict_dilatancy = {
            1: type_1(),
            2: type_2(),
            3: type_3(),
            4: type_4(),
            5: type_5(),
            6: type_6(),
            7: type_7(),
            8: type_8(),
            9: type_9(),
        }

        return dict_dilatancy(type_ground)

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
        if build_press:
            if not pit_depth:
                pit_depth = 0
            sigma_max = 2 * (depth - pit_depth) * 10 + build_press if (depth - pit_depth) > 0 else 2 * 10 * depth

            sigma_max_1 = MechanicalProperties.round_sigma_3(sigma_max * K0)
            sigma_max_2 = MechanicalProperties.round_sigma_3(sigma_max * K0 * 0.5)
            sigma_max_3 = MechanicalProperties.round_sigma_3(sigma_max * K0 * 0.25)

            return [sigma_max_3, sigma_max_2, sigma_max_1] if sigma_max_3 >= 100 else [100, 200, 400]
        else:
            return None

    @staticmethod
    def define_reference_pressure_array_calculated_by_referense_pressure(sigma_3: float) -> list:
        """Функция рассчета обжимающих давлений для кругов мора"""

        sigma_max = sigma_3

        sigma_max_1 = MechanicalProperties.round_sigma_3(sigma_max)
        sigma_max_2 = MechanicalProperties.round_sigma_3(sigma_max * 0.5)
        sigma_max_3 = MechanicalProperties.round_sigma_3(sigma_max * 0.25)

        return [sigma_max_3, sigma_max_2, sigma_max_1] if sigma_max_3 >= 100 else [100, 200, 400]


    @staticmethod
    def define_reference_pressure_array_set_by_user(val) -> list:
        if val is None:
            return None
        else:
            val = list(map(lambda val: int(float(val.replace(",", ".").strip(" ")) * 1000), val.split("/")))
            return val

class ConsolidationProperties:
    Eoed = DataTypeValidation(float, int)
    Cv = DataTypeValidation(float, int)
    Ca = DataTypeValidation(float, int)
    p_max = DataTypeValidation(float, int)
    m = DataTypeValidation(float, int)

    def __init__(self):
        for key in ConsolidationProperties.__dict__:
            if isinstance(getattr(ConsolidationProperties, key), DataTypeValidation):
                object.__setattr__(self, key, None)

    @log_this(app_logger, "debug")
    def defineProperties(self, physical_properties, data_frame: pd.DataFrame, string: int,
                         test_mode=None, K0_mode=None) -> None:
        """Считывание строки свойств"""

        self.Eoed = float_df(data_frame.iat[string, MechanicalPropertyPosition["Eoed"][1]])

        if self.Eoed:
            Cv = float_df(data_frame.iat[string, MechanicalPropertyPosition["Cv"][1]])
            Ca = float_df(data_frame.iat[string, MechanicalPropertyPosition["Ca"][1]])

            self.m = MechanicalProperties.define_m(physical_properties.e, physical_properties.Il)
            self.Cv = Cv if Cv else np.round(MechanicalProperties.define_Cv(
                MechanicalProperties.define_kf(physical_properties.type_ground, physical_properties.e)), 3)
            self.Ca = Ca if Ca else np.round(np.random.uniform(0.001, 0.003), 5)

            if self.Cv > 1.5:
                self.Cv = np.random.uniform(1, 1.5)

            self.p_max = ConsolidationProperties.spec_round(ConsolidationProperties.define_loading_pressure(
                float_df(data_frame.iat[string, MechanicalPropertyPosition["p_max"][1]]),
                build_press=float_df(data_frame.iat[string, MechanicalPropertyPosition["build_press"][1]]),
                pit_depth=float_df(data_frame.iat[string, MechanicalPropertyPosition["pit_depth"][1]]),
                depth=physical_properties.depth), 3)

    @staticmethod
    def define_loading_pressure(pmax, build_press: float, pit_depth: float, depth: float):
        """Функция рассчета максимального давления"""
        if pmax:
            return pmax
        if build_press:
            if not pit_depth:
                pit_depth = 0
            sigma_max = (2 * (depth - pit_depth) * 10) / 1000 + build_press if (depth - pit_depth) > 0 else (2 * 10 * depth) / 1000
            return sigma_max
        else:
            return (2 * 10 * depth) / 1000

    @staticmethod
    def spec_round(x, precision) -> float:
        """Rounds value as this:
            0.16 -> 0.16
            0.14 -> 0.14
            0.143 -> 0.145
            0.146 -> 0.150
        """
        order = 10 ** precision

        condition = round(x % 10 ** (-(precision - 1)) * order, 1)
        '''digit at precision, for 0.146 and precision = 3 condition = 6'''

        if 0 < condition <= 5:
            return round(x // (10 / order) / (order / 10) + 5 / order, precision)
        if condition > 5:
            return round(x // (10 / order) / (order / 10) + 1 / (order / 10), precision)
        return round(x, precision)

class CyclicProperties(MechanicalProperties):
    """Расширенный класс с дополнительными обработанными свойствами"""
    CSR = DataTypeValidation(float, int, np.int32)
    t = DataTypeValidation(float, int, np.int32)
    N = DataTypeValidation(float, int, np.int32)
    I = DataTypeValidation(float, int, np.int32)
    magnitude = DataTypeValidation(float, int, np.int32)
    acceleration = DataTypeValidation(float, int, np.int32)
    intensity = DataTypeValidation(float, int, np.int32)
    cycles_count = DataTypeValidation(float, int, np.int32)
    rd = DataTypeValidation(float, int, np.int32)
    MSF = DataTypeValidation(float, int, np.int32)
    rw = DataTypeValidation(float, int, np.int32)
    Hw = DataTypeValidation(float, int, np.int32)
    frequency = DataTypeValidation(float, int, np.int32)
    Mcsr = DataTypeValidation(float, int, np.int32)
    Msf = DataTypeValidation(float, int, np.int32)
    n_fail = DataTypeValidation(float, int, np.int32)
    damping_ratio = DataTypeValidation(float, int, np.int32)

    def __init__(self):
        self._setNone()

    def _setNone(self):
        """Поставим изначально везде None"""
        for key in CyclicProperties.__dict__:
            if isinstance(getattr(CyclicProperties, key), DataTypeValidation):
                object.__setattr__(self, key, None)

    def defineProperties(self, physical_properties, data_frame, string, test_mode, K0_mode) -> None:
        super().defineProperties(physical_properties, data_frame, string, test_mode=test_mode, K0_mode=K0_mode)
        if self.c and self.fi and self.E50:

            if physical_properties.depth <= 9.15:
                self.rd = round((1 - (0.00765 * physical_properties.depth)), 3)
            elif (physical_properties.depth > 9.15) and (physical_properties.depth < 23):
                self.rd = round((1.174 - (0.0267 * physical_properties.depth)), 3)
            else:
                self.rd = round((1.174 - (0.0267 * 23)), 3)

            if test_mode == "Сейсморазжижение":
                if physical_properties.depth <= physical_properties.ground_water_depth:
                    self.sigma_1 = round(2 * 9.81 * physical_properties.depth)
                elif physical_properties.depth > physical_properties.ground_water_depth:
                    self.sigma_1 = round(2 * 9.81 * physical_properties.depth - (
                            9.81 * (physical_properties.depth - physical_properties.ground_water_depth)))

                if self.sigma_1 < 10:
                    self.sigma_1 = 10

                self.sigma_3 = np.round(self.sigma_1 * self.K0)

                self.acceleration = float_df(data_frame.iat[string, DynamicsPropertyPosition["acceleration"][1]]) # В долях g
                if self.acceleration:
                    self.acceleration = np.round(self.acceleration, 3)
                    self.intensity = CyclicProperties.define_intensity(self.acceleration)
                else:
                    self.intensity = float_df(data_frame.iat[string, DynamicsPropertyPosition["intensity"][1]])
                    self.acceleration = CyclicProperties.define_acceleration(self.intensity)

                self.magnitude = float_df(data_frame.iat[string, DynamicsPropertyPosition["magnitude"][1]])

                self.t = np.round(0.65 * self.acceleration * self.sigma_1 * float(self.rd))
                self.MSF = np.round((10 ** (2.24) / ((self.magnitude) ** (2.56))), 2)
                self.t *= self.MSF
                if self.t < 1:
                    self.t = 1
                self.t = np.round(self.t)

                self.cycles_count = CyclicProperties.define_cycles_count(self.magnitude)

                self.frequency = 0.5

            elif test_mode == "Штормовое разжижение":
                self.rw = float_df(data_frame.iat[string, DynamicsPropertyPosition["rw"][1]])
                self.Hw = float_df(data_frame.iat[string, DynamicsPropertyPosition["Hw"][1]])

                self.t = np.round((0.5 * self.Hw * self.rw) / 2)

                sigma_1 = float_df(data_frame.iat[string,
                                                  DynamicsPropertyPosition["reference_pressure"][1]])
                if sigma_1:
                    self.sigma_1 = np.round(sigma_1 * 1000)
                else:
                    self.sigma_1 = np.round((2 - (self.rw / 10)) * 9.81 * physical_properties.depth)
                if self.sigma_1 < 10:
                    self.sigma_1 = 10

                self.sigma_3 = np.round(self.sigma_1 * self.K0)

                self.cycles_count = int(float_df(data_frame.iat[string, DynamicsPropertyPosition["cycles_count_storm"][1]]))

                self.frequency = float_df(data_frame.iat[string, DynamicsPropertyPosition["frequency_storm"][1]])

            elif test_mode == "Демпфирование":
                physical_properties.ground_water_depth = 0 if not physical_properties.ground_water_depth else physical_properties.ground_water_depth
                if physical_properties.depth <= physical_properties.ground_water_depth:
                    self.sigma_1 = round(2 * 9.81 * physical_properties.depth)
                elif physical_properties.depth > physical_properties.ground_water_depth:
                    self.sigma_1 = round(2 * 9.81 * physical_properties.depth - (
                            9.81 * (physical_properties.depth - physical_properties.ground_water_depth)))

                if self.sigma_1 < 10:
                    self.sigma_1 = 10

                self.sigma_3 = np.round(self.sigma_1 * self.K0)


                self.cycles_count = 5

                self.frequency = np.round(float_df(data_frame.iat[string,
                                                         DynamicsPropertyPosition["frequency_vibration_creep"][1]]), 1)

                self.t = np.round(float_df(data_frame.iat[string,
                                                          DynamicsPropertyPosition["sigma_d_vibration_creep"][1]]) / 2,
                                  1)

            elif test_mode == "По заданным параметрам":

                sigma_1 = float_df(data_frame.iat[string,
                                        DynamicsPropertyPosition["reference_pressure"][1]])
                if sigma_1:
                    self.sigma_1 = np.round(sigma_1 * 1000)
                else:
                    physical_properties.ground_water_depth = 0 if not physical_properties.ground_water_depth else physical_properties.ground_water_depth
                    if physical_properties.depth <= physical_properties.ground_water_depth:
                        self.sigma_1 = round(2 * 9.81 * physical_properties.depth)
                    elif physical_properties.depth > physical_properties.ground_water_depth:
                        self.sigma_1 = round(2 * 9.81 * physical_properties.depth - (
                                9.81 * (physical_properties.depth - physical_properties.ground_water_depth)))

                    if self.sigma_1 < 10:
                        self.sigma_1 = 10

                self.t = np.round(float_df(data_frame.iat[string, DynamicsPropertyPosition["sigma_d_vibration_creep"][1]])/2)

                self.sigma_3 = np.round(self.sigma_1 * self.K0)

                self.cycles_count = int(float_df(data_frame.iat[string, DynamicsPropertyPosition["cycles_count_storm"][1]]))

                self.frequency = np.round(float_df(data_frame.iat[string,
                                                                  DynamicsPropertyPosition["frequency_vibration_creep"][
                                                                      1]]), 1)


            self.n_fail, self.Mcsr = define_fail_cycle(self.cycles_count, self.sigma_1, self.t,
                                                       physical_properties.Ip,
                                                       physical_properties.Il, physical_properties.e)
            if self.n_fail:
                if (self.sigma_1 - self.sigma_3) <= 1.5 * self.t:
                    self.Ms = np.round(np.random.uniform(60, 200), 2)
                else:
                    self.Ms = np.round(np.random.uniform(0.7, 0.9), 2)
            else:
                self.Ms = CyclicProperties.define_Ms(
                    self.c, self.fi, self.Mcsr, self.sigma_3, self.sigma_1, self.t, self.cycles_count,
                    physical_properties.e, physical_properties.Il)

            self.CSR = np.round(self.t / self.sigma_1, 2)

            self.damping_ratio = np.random.uniform(1, 2)
            #np.round(CyclicProperties.define_damping_ratio(), 2)

    @staticmethod
    def define_Ms(c, fi, Mcsr, sigma_3, sigma_1, t, cycles_count, e, Il) -> float:
        """Функция находит зависимость параметра Msf от физических свойств и параметров нагрузки
        Средняя линия отклонения деформации будет определена как 0.05 / Msf"""
        if (sigma_1 - sigma_3) <= 1.5*t:
            return np.round(np.random.uniform(100, 500), 2)

        e = e if e else np.random.uniform(0.6, 0.7)
        Il = Il if Il else np.random.uniform(-0.1, 0.3)

        def define_qf(sigma_3, c, fi):
            """Функция определяет qf через обжимающее давление и c fi"""
            fi = fi * np.pi / 180
            return np.round(
                (2 * (c * 1000 + (np.tan(fi)) * sigma_3)) / (np.cos(fi) - np.tan(fi) + np.sin(fi) * np.tan(fi)), 1)

        qf = define_qf(sigma_3*(1 - 1 / Mcsr), c, fi)

        max_deviator = sigma_1 - sigma_3 + 2*t

        #Ms = ModelTriaxialCyclicLoadingSoilTest.critical_line(
            #c, fi, (1 - 1 / Mcsr) * max_deviator) / max_deviator if Mcsr else 1

        Ms = 0.8 * qf / max_deviator if Mcsr else 1

        CSR_dependence = sigmoida(mirrow_element(t/sigma_1, 0.5), 2, 0.9, 2.1, 1.5)
        e_dependence = sigmoida(mirrow_element(e, 0.5), 0.7, 0.5, 0.9, 1.5)
        Il_dependence = sigmoida(mirrow_element(Il, 0.5), 0.7, 0.5, 1, 1.5)
        if cycles_count <= 10000:
            cycles_count_dependence = sigmoida(mirrow_element(cycles_count, 100), 0.3, 100, 1.1, 250)
        else:
            cycles_count_dependence = 0.5

        Ms *= (CSR_dependence * e_dependence * Il_dependence * cycles_count_dependence)

        if Ms <= 0.7:
            Ms = np.random.uniform(0.6, 0.8)

        return np.round(Ms, 2)

    @staticmethod
    def define_acceleration(intensity: float) -> float:
        y1 = np.array([0, 0.1, 0.16, 0.24, 0.33, 0.82])
        x1 = np.array([0, 6, 7, 8, 9, 10])
        Ainter = interp1d(x1, y1, kind='cubic')
        return float(Ainter(intensity))

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

    @staticmethod
    def define_damping_ratio() -> float:
        return np.random.uniform(5, 15)

class RCProperties(MechanicalProperties):
    """Расширенный класс с дополнительными обработанными свойствами"""
    reference_pressure = DataTypeValidation(float, int, np.int32)
    G0 = DataTypeValidation(float, int, np.int32)
    threshold_shear_strain = DataTypeValidation(float, int, np.int32)

    def __init__(self):
        self._setNone()

    def _setNone(self):
        """Поставим изначально везде None"""
        for key in RCProperties.__dict__:
            if isinstance(getattr(RCProperties, key), DataTypeValidation):
                object.__setattr__(self, key, None)

    def __init__(self):
        self._setNone()

    def defineProperties(self, physical_properties, data_frame, string, test_mode, K0_mode) -> None:
        super().defineProperties(physical_properties, data_frame, string, test_mode=test_mode, K0_mode=K0_mode)
        if self.c and self.fi and self.E50:
            self.reference_pressure = float_df(data_frame.iat[string,
                                                          DynamicsPropertyPosition["reference_pressure"][1]])
            self.G0, self.threshold_shear_strain = define_G0_threshold_shear_strain(
                self.reference_pressure, self.E50, self.c, self.fi, self.K0, physical_properties.type_ground,
                physical_properties.Ip, physical_properties.e)

class VibrationCreepProperties(MechanicalProperties):
    """Расширенный класс с дополнительными обработанными свойствами"""
    Kd = DataTypeValidation(list, float, int)
    frequency = DataTypeValidation(list, float, int)
    n_fail = DataTypeValidation(float, int, np.int32)
    Mcsr = DataTypeValidation(float, int, np.int32)
    t = DataTypeValidation(float, int, np.int32)
    Ms = DataTypeValidation(float, int, np.int32)
    cycles_count = DataTypeValidation(float, int, np.int32)
    damping_ratio = DataTypeValidation(float, int, np.int32)

    def __init__(self):
        self._setNone()

    def _setNone(self):
        """Поставим изначально везде None"""
        for key in VibrationCreepProperties.__dict__:
            if isinstance(getattr(VibrationCreepProperties, key), DataTypeValidation):
                object.__setattr__(self, key, None)

    def defineProperties(self, physical_properties, data_frame, string, test_mode, K0_mode) -> None:
        super().defineProperties(physical_properties, data_frame, string, test_mode=test_mode, K0_mode=K0_mode)
        if self.c and self.fi and self.E50:
            frequency = data_frame.iat[string, DynamicsPropertyPosition["frequency_vibration_creep"][1]]
            Kd = data_frame.iat[string, DynamicsPropertyPosition["Kd_vibration_creep"][1]]

            t = float_df(data_frame.iat[string, DynamicsPropertyPosition["sigma_d_vibration_creep"][1]])
            if not t:
                self.t = np.round(self.E50*5*(10/76000)/2)

                if self.t < 5:
                    self.t = 5

                if self.t > 25:
                    self.t = 25
            else:
                self.t = np.round(t/2)

            self.frequency = VibrationCreepProperties.val_to_list(frequency)
            self.Kd = [VibrationCreepProperties.define_Kd(
                self.qf, self.t, physical_properties.e, physical_properties.Il, frequency) for frequency in self.frequency]


            """self.frequency = [float(frequency)] if str(frequency).isdigit() else list(map(
                lambda frequency: float(frequency.replace(",", ".").strip(" ")), frequency.split(";")))
            self.Kd = [float(Kd)] if str(Kd).isdigit() else list(map(lambda Kd: float(Kd.replace(",", ".").strip(" ")),
                                                                     Kd.split(";")))"""

            self.cycles_count = int(np.random.uniform(2000, 5000))

            self.damping_ratio = np.random.uniform(1, 2)

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

class ShearProperties(MechanicalProperties):
    """Расширенный класс с дополнительными обработанными свойствами"""
    SHEAR_NATURAL = 11
    '''Срез природное'''
    SHEAR_SATURATED = 12
    '''Срез водонасыщенное'''
    SHEAR_DD = 13
    '''Срез плашка по плашке'''
    SHEAR_NN = 14
    '''Срез НН'''
    SHEAR_DILATANCY = 2
    '''Срез дилатансия'''

    pref_warning: bool = False

    tau_max = DataTypeValidation(float, int)
    sigma = DataTypeValidation(float, int, np.int32)

    def __init__(self):
        self._setNone()

    def _setNone(self):
        """Поставим изначально везде None"""
        for key in ShearProperties.__dict__:
            if isinstance(getattr(ShearProperties, key), DataTypeValidation):
                object.__setattr__(self, key, None)

    def defineProperties(self, physical_properties, data_frame, string, test_mode, K0_mode) -> None:

        is_dilatancy = ShearProperties.is_dilatancy_type(test_mode)

        if not is_dilatancy:
            self.c, self.fi = ShearProperties.define_c_fi_E(data_frame, test_mode, string)
        elif is_dilatancy:
            self.c, self.fi, dilatancy_angle = ShearProperties.define_c_fi_E(data_frame, test_mode, string)
            self.dilatancy_angle = dilatancy_angle if dilatancy_angle else MechanicalProperties.define_dilatancy(
                physical_properties.type_ground, physical_properties.e, physical_properties.Il, physical_properties.Ip) * np.random.uniform(0.9, 1.1)

        if self.c and self.fi:
            self.c = self.c

            self.build_press = float_df(data_frame.iat[string, MechanicalPropertyPosition["build_press"][1]])
            if self.build_press:
                self.build_press *= 1000

            self.pit_depth = float_df(data_frame.iat[string, MechanicalPropertyPosition["pit_depth"][1]])

            if is_dilatancy:
                self.sigma = ShearProperties.round_sigma(
                    float_df(data_frame.iat[string, MechanicalPropertyPosition["Pref"][1]]))

                if self.sigma:
                    self.sigma = self.sigma*1000

                if not self.sigma:
                    self.pref_warning = True
                    self.sigma = ShearProperties.round_sigma(ShearProperties.define_sigma(physical_properties.depth))

            else:
                self.sigma = ShearProperties.round_sigma(ShearProperties.define_sigma(physical_properties.depth))


            if self.sigma < 100:
                self.sigma = 100

            self.tau_max = np.round(float(ShearProperties.define_tau_max(self.sigma, self.c * 1000, self.fi)), 1) * np.random.uniform(0.95, 1.05)

            self.E50 = ShearProperties.define_E50(physical_properties.type_ground,
                                                  physical_properties.Ir,
                                                  physical_properties.Ip, physical_properties.e,
                                                  physical_properties.stratigraphic_index, self.tau_max)*0.7

            self.E50 = self.E50 * 1000

            # if self.tau_max <= 40:
            #     _E50 = self.tau_max / 0.15
            #     self.E50 = _E50 * np.random.uniform(2.0, 3.0)

            if ShearProperties.shear_type(test_mode) == ShearProperties.SHEAR_NN:
                self.E50 = self.E50 * np.random.uniform(1.5, 2.0) / 0.7

            # print(f"E50 чтоб его: {self.E50}")

            self.poisons_ratio = ShearProperties.define_poissons_ratio(
                physical_properties.Rc,
                physical_properties.Ip,
                physical_properties.Il,
                physical_properties.Ir,
                physical_properties.granulometric_10,
                physical_properties.granulometric_5,
                physical_properties.granulometric_2)

            self.m = MechanicalProperties.define_m(physical_properties.e, physical_properties.Il)

            if not self.dilatancy_angle:
                self.dilatancy_angle = ShearProperties.define_dilatancy(
                    physical_properties.type_ground, physical_properties.e, physical_properties.Il, physical_properties.Ip) * np.random.uniform(0.9, 1.1)

            self.pressure_array = {
                "set_by_user": ShearProperties.define_reference_pressure_array_set_by_user(
                    float_df(data_frame.iat[string, MechanicalPropertyPosition["pressure_array"][1]])),

                "calculated_by_pressure": ShearProperties.define_reference_pressure_array_calculated_by_pressure(
                    self.build_press, self.pit_depth, physical_properties.depth),

                "state_standard": ShearProperties.define_reference_pressure_array_state_standard(
                    physical_properties.e, physical_properties.Il, physical_properties.type_ground)
            }

            if self.pressure_array["set_by_user"] is not None:
                self.pressure_array["current"] = self.pressure_array["set_by_user"]
            elif self.pressure_array["calculated_by_pressure"] is not None:
                self.pressure_array["current"] = self.pressure_array["calculated_by_pressure"]
            elif self.pressure_array["state_standard"] is not None:
                self.pressure_array["current"] = self.pressure_array["state_standard"]

            if self.pressure_array["calculated_by_pressure"] is None:
                self.pressure_array["calculated_by_pressure"] = \
                    ShearProperties.define_reference_pressure_array_calculated_by_referense_pressure(self.sigma)

    @staticmethod
    def define_sigma(depth: float) -> float:
        """Функция определяет нормальное напряжение"""
        """Функция определяет обжимающее давление"""
        return round((2 * 9.81 * depth), 1)

    @staticmethod
    def define_tau_max(sigma: float, c: float, fi: float) -> float:
        """Функция определяет максимальное касательное напряжение"""
        return sigma * np.tan(np.deg2rad(fi)) + c

    @staticmethod
    def round_sigma(sigma, param=5):
        return sigma

    @staticmethod
    def shear_type(test_mode: str) -> int:
        if test_mode == "Срез природное":
            return ShearProperties.SHEAR_NATURAL
        elif test_mode == "Срез водонасыщенное":
            return ShearProperties.SHEAR_SATURATED
        elif test_mode == "Срез плашка по плашке":
            return ShearProperties.SHEAR_DD
        elif test_mode == "Срез НН":
            return ShearProperties.SHEAR_NN
        elif test_mode == "Срез дилатансия":
            return ShearProperties.SHEAR_DILATANCY
        else:
            return 0

    @staticmethod
    def is_dilatancy_type(test_mode: str) -> bool:
        if ShearProperties.shear_type(test_mode) == ShearProperties.SHEAR_DILATANCY:
            return True
        else:
            return False

    @staticmethod
    def define_E50(type_ground, Ir, Il, e, stratigraphic_index, tau_max):

        def define_E50_for_sand(e50_array, e):
            """Функция расчета угла дилатнсии для песков"""
            if len(e50_array) == 3:
                e_array = np.array([0.45, 0.55, 0.65])
            elif len(e50_array) == 4:
                e_array = np.array([0.45, 0.55, 0.65, 0.75])
            if e is None:
                e = np.random.uniform(0.45, 0.65)
            if e < e_array[0]:
                e = e_array[0]
            if e > e_array[-1]:
                # e = e_array[-1]
                return (tau_max / 0.15) * np.random.uniform(4.0, 5.0)/1000


            return np.interp(e, e_array, e50_array)

        def define_E50_for_clay(Il, e, stratigraphic_index, type_ground):
            """Функция расчета угла дилатнсии для глин"""

            if e is None:
                e = np.random.uniform(0.45, 0.75)

            if Il is None:
                Il = np.random.uniform(0.25, 0.5)

            if e < 0.35:
                e = 0.35
            if e > 1.6:
                e = 1.6

            if stratigraphic_index == "f":

                if Il < 0:
                    Il = 0
                if Il > 0.75:
                    #Il = 0.75
                    return (tau_max / 0.15) * np.random.uniform(4.0, 5.0)/1000

                if type_ground == 6:
                    if 0 <= Il <= 0.75:
                        return np.interp(e, np.array([0.45, 0.55, 0.65, 0.75, 0.85]),
                                         np.array([33, 24, 17, 11, 7]))
                if type_ground == 7:
                    if 0 <= Il <= 0.25:
                        return np.interp(e, np.array([0.45, 0.55, 0.65, 0.75]),
                                         np.array([40, 33, 27, 21]))
                    elif 0.25 < Il <= 0.5:
                        return np.interp(e, np.array([0.45, 0.55, 0.65, 0.75, 0.85, 0.95]),
                                         np.array([35, 28, 22, 17, 14]))
                    elif 0.5 < Il <= 0.75:
                        return np.interp(e, np.array([0.65, 0.75, 0.85, 0.95]),
                                         np.array([15, 12, 9, 7]))
            elif stratigraphic_index == "J":

                if Il < -0.25:
                    Il = -0.25
                if Il > 0.5:
                    #Il = 0.5
                    return (tau_max / 0.15) * np.random.uniform(4.0, 5.0)/1000

                if type_ground == 8:
                    if -0.25 <= Il <= 0:
                        return np.interp(e, np.array([0.95, 1.05, 1.2]),
                                         np.array([27, 25, 22]))
                    elif 0 < Il <= 0.25:
                        return np.interp(e, np.array([0.95, 1.05, 1.2, 1.4]),
                                         np.array([24, 22, 19, 15]))
                    elif 0.25 < Il <= 0.5:
                        return np.interp(e, np.array([1.2, 1.4, 1.6]),
                                         np.array([16, 12, 10]))
            else:  # stratigraphic_index == "a" or stratigraphic_index == "d":

                if Il < 0:
                    Il = 0
                if Il > 0.75:
                    #Il = 0.75
                    return (tau_max / 0.15) * np.random.uniform(4.0, 5.0)/1000

                if type_ground == 6:
                    if 0 <= Il <= 0.75:
                        return np.interp(e, np.array([0.45, 0.55, 0.65, 0.75, 0.85]),
                                         np.array([32, 24, 16, 10, 7]))
                if type_ground == 7:
                    if 0 <= Il <= 0.25:
                        return np.interp(e, np.array([0.45, 0.55, 0.65, 0.75, 0.85, 0.95]),
                                         np.array([34, 27, 22, 17, 14, 11]))
                    elif 0.25 < Il <= 0.5:
                        return np.interp(e, np.array([0.45, 0.55, 0.65, 0.75, 0.85, 0.95]),
                                         np.array([32, 25, 19, 14, 11, 8]))
                    elif 0.5 < Il <= 0.75:
                        return np.interp(e, np.array([0.65, 0.75, 0.85, 0.95, 1.05]),
                                         np.array([17, 12, 8, 6, 5]))
                if type_ground == 8:
                    if 0 <= Il <= 0.25:
                        return np.interp(e, np.array([0.55, 0.65, 0.75, 0.85, 0.95, 1.05]),
                                         np.array([28, 24, 21, 18, 15, 12]))
                    elif 0.25 < Il <= 0.5:
                        return np.interp(e, np.array([0.65, 0.75, 0.85, 0.95, 1.05]),
                                         np.array([21, 18, 15, 14, 12, 9]))
                    elif 0.5 < Il <= 0.75:
                        return np.interp(e, np.array([0.75, 0.85, 0.95, 1.05]),
                                         np.array([15, 12, 9, 7]))

        def define_E50_for_peat(Il, Ir, e):

            if Ir is None:
                return None

            if Ir < 0:
                Ir = 0
            if Ir > 0.25:
                Ir = 0.25

            if e < 0.65:
                e = 0.65
            if e > 1.35:
                e = 1.35

            if Il < 0:
                Il = 0
            if Il > 0.75:
                # Il = 0.75
                return (tau_max / 0.15) * np.random.uniform(3.0, 4.0)/1000

            if 0 <= Il <= 0.25:
                if 0.05 <= Ir <= 0.1:
                    return np.interp(e, np.array([0.65, 0.75, 0.85, 0.95]),
                                     np.array([13, 12, 11, 10]))
                elif 0.1 < Ir <= 0.25:
                    return np.interp(e, np.array([1.05, 1.05, 1.25, 1.35]),
                                     np.array([8.5, 8, 7, 5]))
            elif 0.25 < Il <= 0.5:
                if 0.05 <= Ir <= 0.1:
                    return np.interp(e, np.array([0.65, 0.75, 0.85, 0.95]),
                                     np.array([11, 10, 8.5, 7.5]))
                elif 0.1 < Ir <= 0.25:
                    return np.interp(e, np.array([1.05, 1.05, 1.25, 1.35]),
                                     np.array([7, 6, 5.5, 5]))
            elif 0.5 < Il <= 0.75:
                if 0.05 <= Ir <= 0.1:
                    return np.interp(e, np.array([0.65, 0.75, 0.85, 0.95]),
                                     np.array([8, 7, 6, 5.5]))
                elif 0.1 < Ir <= 0.25:
                    return np.interp(e, np.array([1.05, 1.05, 1.25, 1.35]),
                                     np.array([5, 5, 4.5, 4]))
            elif 0.75 < Il <= 1:
                if 0.05 <= Ir <= 0.1:
                    return np.interp(e, np.array([0.65, 0.75, 0.85, 0.95]),
                                     np.array([6, 5, 4.5, 4]))
                elif 0.1 < Ir <= 0.25:
                    return np.interp(e, np.array([1.05, 1.05, 1.25]),
                                     np.array([3.5, 3, 2.5]))

        dependence_E50_on_type_ground = {
            1: define_E50_for_sand(np.array([50, 40, 30*0.5]), e),  # Песок гравелистый
            2: define_E50_for_sand(np.array([50, 40, 30*0.5]), e),  # Песок крупный
            3: define_E50_for_sand(np.array([50, 30, 30*0.5]), e),  # Песок средней крупности
            4: define_E50_for_sand(np.array([48, 38, 28, 18*0.5]), e),  # Песок мелкий
            5: define_E50_for_sand(np.array([39, 28, 18, 11*0.5]), e),  # Песок пылеватый
            6: define_E50_for_clay(Il, e, stratigraphic_index, type_ground),  # Супесь
            7: define_E50_for_clay(Il, e, stratigraphic_index, type_ground),  # Суглинок
            8: define_E50_for_clay(Il, e, stratigraphic_index, type_ground),  # Глина
            9: define_E50_for_peat(Il, Ir, e),  # Торф
        }

        return dependence_E50_on_type_ground[type_ground]

    @staticmethod
    def define_reference_pressure_array_calculated_by_referense_pressure(sigma: float) -> list:
        """Функция рассчета обжимающих давлений для среза"""

        sigma_max = sigma

        sigma_max_1 = MechanicalProperties.round_sigma_3(sigma_max)
        sigma_max_2 = MechanicalProperties.round_sigma_3(sigma_max * 0.5)
        sigma_max_3 = MechanicalProperties.round_sigma_3(sigma_max * 0.25)

        return [sigma_max_3, sigma_max_2, sigma_max_1] if sigma_max_3 >= 100 else [100, 200, 400]

    @staticmethod
    def define_reference_pressure_array_calculated_by_pressure(build_press: float, pit_depth: float, depth: float) -> list:
        """Функция рассчета обжимающих давлений для кругов мора"""
        if build_press:
            if not pit_depth:
                pit_depth = 0
            sigma_max = 2 * (depth - pit_depth) * 10 + build_press if (depth - pit_depth) > 0 else 2 * 10 * depth

            sigma_max_1 = MechanicalProperties.round_sigma_3(sigma_max)
            sigma_max_2 = MechanicalProperties.round_sigma_3(sigma_max * 0.5)
            sigma_max_3 = MechanicalProperties.round_sigma_3(sigma_max * 0.25)

            return [sigma_max_3, sigma_max_2, sigma_max_1] if sigma_max_3 >= 100 else [100, 200, 400]
        else:
            return None

    @staticmethod
    def define_reference_pressure_array_state_standard(e: float, Il: float, type_ground: int) -> list:
        """Функция рассчета обжимающих давлений для кругов мора"""
        e = e if e else 0.65
        Il = Il if Il else 0.5

        if (type_ground == 1) or (type_ground == 2) or (type_ground == 3) or (
                type_ground == 8 and Il <= 0.25):
            return [100, 300, 500]

        elif (type_ground == 4) or (type_ground == 5) or\
                ((type_ground == 6 or type_ground == 7 or type_ground == 9) and Il <= 0.5) or \
                (type_ground == 8 and Il <= 0.5):
            return [100, 200, 300]

        elif (type_ground == 6 or type_ground == 7 or
              type_ground == 8 or type_ground == 9) and (0.5 < Il <= 1.0):
            return [100, 150, 200]

        elif (type_ground == 6 or type_ground == 7 or
              type_ground == 8 or type_ground == 9) and (Il > 1.0):
            return [25, 75, 125]

PropertiesDict = {
    "PhysicalProperties": PhysicalProperties,
    "MechanicalProperties": MechanicalProperties,
    "CyclicProperties": CyclicProperties,
    "RCProperties": RCProperties,
    "VibrationCreepProperties": VibrationCreepProperties,
    "ShearProperties": ShearProperties
}










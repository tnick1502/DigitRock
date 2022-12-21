"""Модуль математических моделей статического трехосного нагружения. Содержит модели:
    ModelTriaxialStaticLoadTest - модель обработчика данных опыта консолидации.
    Принцип работы:
        Данные подаются в модель методом set_test_file_path(path). Подается путь к файлу, После считывания данные
        передаются в обработчики частей опыта
        Обработка опыта происходит в соответствующих классах частей опыта.
        Метод plotter() позволяет вывести графики обработанного опыта
        Результаты получаются методом get_test_results()

    ModelTriaxialStaticLoadTestSoilTest - модель математического моделирования данных опыта трехосного нагружения.
    Принцип работы:
        Параметры опыта подаются в модель с помощью метода set_test_params().
        Методы get_consolidation_draw_params() и get_deviator_loading_draw_params() служат для считывания рассчитанных
        параметров отрисовки для передачи на слайдеры
        Методы set_consolidation_draw_params() и set_deviator_loading_draw_params() служат установки данных отрисовки
        и перезапуска моделирования опыта
        Метод save_log_file(file_name) принимает имя файла для сохранения и записывает туда словари всех этапов опыта"""
from typing import Tuple

import numpy as np
import matplotlib.pyplot as plt
from numpy.linalg import lstsq
from general.general_functions import exponent
__version__ = 1

def lse(__y):
    A = np.vstack([np.zeros(len(__y)), np.ones(len(__y))]).T
    k, b = lstsq(A, __y, rcond=None)[0]
    return b

def dictionary_without_VFS(sigma_3=100, velocity=49, sample_size: Tuple[int, int] = (76, 38)):
    # Создаем массив набора нагрузки до обжимающего давления консолидации
    # sigma_3 -= effective_stress_after_reconsolidation
    k = sigma_3 / velocity
    if k <= 2:
        velocity = velocity / (2 / k) - 1
    load_stage_time = round(sigma_3 / velocity, 2)
    load_stage_time_array = np.arange(1, load_stage_time, 1)
    time_max = np.random.uniform(20, 30)
    time_array = np.arange(0, time_max, 1)
    # Добавим набор нагрузки к основным массивам
    time = np.hstack((load_stage_time_array, time_array + load_stage_time_array[-1]))

    load_stage_cell_press = np.linspace(0, sigma_3, len(load_stage_time_array) + 1)
    cell_press = np.hstack((load_stage_cell_press[1:], np.full(len(time_array), sigma_3))) + \
                 np.random.uniform(-0.1, 0.1, len(time))

    final_volume_strain = np.random.uniform(0.14, 0.2)
    load_stage_cell_volume_strain = exponent(load_stage_time_array[:-1], final_volume_strain,
                                             np.random.uniform(1, 1))
    # load_stage_cell_volume_strain[0] = 0
    cell_volume_strain = np.hstack((load_stage_cell_volume_strain,
                                    np.full(len(time_array) + 1, final_volume_strain))) * np.pi * (19 ** 2) * sample_size[0] + \
                         np.random.uniform(-0.1, 0.1, len(time))
    cell_volume_strain[0] = 0
    vertical_press = cell_press + np.random.uniform(-0.1, 0.1, len(time))

    # На нэтапе нагружения 'LoadStage', на основном опыте Stabilization
    load_stage = ['LoadStage' for _ in range(len(load_stage_time_array))]
    wait = ['Wait' for _ in range(len(time_array))]
    action = load_stage + wait

    action_changed = ['' for _ in range(len(time))]
    action_changed[len(load_stage_time_array) - 1] = "True"
    action_changed[-1] = 'True'

    # Значения на последнем LoadStage и Первом Wait (следующая точка) - равны
    cell_press[len(load_stage)] = cell_press[len(load_stage) - 1]
    vertical_press[len(load_stage)] = vertical_press[len(load_stage) - 1]
    cell_volume_strain[len(load_stage)] = cell_volume_strain[len(load_stage) - 1]

    trajectory = np.full(len(time), 'ReconsolidationWoDrain')
    trajectory[-1] = "CTC"

    # Подключение запуска опыта
    time_start = [time[0]]
    time = np.hstack((time_start, time))

    action_start = ['Start']
    action = np.hstack((action_start, action))

    action_changed_start = ['True']
    action_changed = np.hstack((action_changed_start, action_changed))

    cell_press_start = [cell_press[0]]
    cell_press = np.hstack((cell_press_start, cell_press))

    cell_volume_strain_start = [cell_volume_strain[0]]
    cell_volume_strain = np.hstack((cell_volume_strain_start, cell_volume_strain))

    vertical_press_start = [vertical_press[0]]
    vertical_press = np.hstack((vertical_press_start, vertical_press))

    trajectory_start = [trajectory[0]]
    trajectory = np.hstack((trajectory_start, trajectory))

    data = {
        "Time": time,
        "Action": action,
        "Action_Changed": action_changed,
        "SampleHeight_mm": np.round(np.full(len(time), sample_size[0])),
        "SampleDiameter_mm": np.round(np.full(len(time), sample_size[1])),
        "Deviator_kPa": np.full(len(time), 0),
        "VerticalDeformation_mm": np.full(len(time), 0),
        "CellPress_kPa": cell_press,
        "CellVolume_mm3": cell_volume_strain,
        "PorePress_kPa": np.full(len(time), 0),
        "PoreVolume_mm3": np.full(len(time), 0),
        "VerticalPress_kPa": vertical_press,
        "Trajectory": trajectory
    }

    return data

import numpy as np
import os
import copy
import matplotlib.pyplot as plt

from static_loading.reconsolidation_model import ModelTriaxialReconsolidation, ModelTriaxialReconsolidationSoilTest
from static_loading.consolidation_model import ModelTriaxialConsolidation, ModelTriaxialConsolidationSoilTest
from static_loading.deviator_loading_model import ModelTriaxialDeviatorLoading, ModelTriaxialDeviatorLoadingSoilTest
from general.general_functions import read_json_file, create_json_file
from loggers.logger import app_logger
from datetime import timedelta
from singletons import E_models, statment
from cvi.cvi_writer import save_cvi_E
from general.general_functions import define_qf

class ModelTriaxialStaticLoad:
    """Класс моделирования опыта трехосного сжатия
    Структура класса представляет объеденение 3х моделей"""
    def __init__(self):
        # Основные модели опыта
        self.reconsolidation = ModelTriaxialReconsolidation()
        self.consolidation = ModelTriaxialConsolidation()
        self.deviator_loading = ModelTriaxialDeviatorLoading()

    def set_test_data(self, test_data):
        """Получение массивов опытов и передача в соответствующий класс"""
        self.reconsolidation.set_test_data(test_data["reconsolidation"])
        self.consolidation.set_test_data(test_data["consolidation"])
        self.deviator_loading.set_test_data(test_data["deviator_loading"])

    def get_processing_parameters(self):
        cons = self.consolidation.get_processing_parameters() if self.consolidation is not None else None
        return {
            "consolidation": cons,
            "deviator_loading": self.deviator_loading.get_processing_parameters()
        }

    def set_processing_parameters(self, params):
        self.consolidation.set_processing_parameters(params["consolidation"])
        self.deviator_loading.set_processing_parameters(params["deviator_loading"])

    def set_test_file_path(self, file_path):
        """Обработка логфайла опыта"""
        test_data = ModelTriaxialStaticLoad.open_geotek_log(file_path)
        self.set_test_data(test_data)
        processing_parameters_path = '/'.join(os.path.split(file_path)[:-1]) + "/processing_parameters.json"
        if os.path.exists(processing_parameters_path):
            self.set_processing_parameters(read_json_file(processing_parameters_path))

    def plotter(self):
        #self.reconsolidation.plotter()
        self.consolidation.plotter()
        #self.deviator_loading.plotter()
        plt.show()

    def get_test_results(self):
        results = {}
        results.update(self.reconsolidation.get_test_results())
        results.update(self.consolidation.get_test_results())
        results.update(self.deviator_loading.get_test_results())
        return results

    @staticmethod
    def open_geotek_log(file_path, camera="A"):
        """Функция открытия файла прибора геотек"""

        def find_current_columns(line, column_keys):
            """Функция находит нужные колонки по ключу и определяет их размерность"""
            columns_dict = {}
            for key in column_keys:
                for column_name in line:
                    if key in column_name:
                        columns_dict[key] = {"index": line.index(column_name),
                                             "scale": 1}
                        break
            return columns_dict

        def define_reconsolidation(read_data):
            """Обработка реконсолидации"""
            reconsolidation = {}
            try:
                end_reconsolidation = read_data['Trajectory'].index("Consolidation")
                reconsolidation["delta_h"] = round(read_data['VerticalDeformation'][end_reconsolidation], 5)
                reconsolidation["pore_pressure"] = read_data['PorePress'][0:end_reconsolidation]
                reconsolidation["cell_pressure"] = read_data['CellPress'][0:end_reconsolidation]
                reconsolidation["action"] = read_data['Action'][0:end_reconsolidation]
                reconsolidation["time"] = read_data['Time'][0:end_reconsolidation]
                reconsolidation["trajectory"] = read_data["Trajectory"][0:end_reconsolidation]

                return reconsolidation
            except (ValueError, IndexError):
                return None

        def define_consolidation(read_data, delta_h):
            """Обработка консолидации"""
            consolidation = {}
            # Найдем начало и конец этапа консолидации
            try:
                begin_consolidation = read_data['Trajectory'].index('Consolidation')
                iload = read_data['Action'][begin_consolidation:].index('Stabilization')
                begin_consolidation += iload - 1
            except ValueError:
                try:
                    begin_consolidation = read_data['Trajectory'].index('Consolidation')
                    iload = read_data['Action'][begin_consolidation:].index('Wait')
                    begin_consolidation += iload
                except ValueError:
                    try:
                        begin_consolidation = read_data['Trajectory'].index('Consolidation')
                    except ValueError:
                        return None
            try:
                end_consolidation = read_data['Action'].index('WaitLimit')
            except ValueError:
                try:
                    end_consolidation = read_data['Trajectory'].index('CTC')
                except ValueError:
                    end_consolidation = len(read_data['Trajectory'])

            try:
                consolidation["delta_h_consolidation"] = read_data['VerticalDeformation'][end_consolidation]
                consolidation["delta_h_reconsolidation"] = round(delta_h, 5)
                consolidation["cell_volume_strain"] = -((read_data['CellVolume'][
                                                         begin_consolidation:end_consolidation]) / (
                                                                np.pi * (19 ** 2) * (76 - consolidation["delta_h_reconsolidation"])))
                consolidation["pore_volume_strain"] = (read_data['PoreVolume'][
                                                       begin_consolidation:end_consolidation] - read_data['PoreVolume'][read_data['Trajectory'].index('Consolidation')]) / (
                                                              np.pi * (19 ** 2) * (76 - consolidation["delta_h_reconsolidation"]))
                consolidation["time"] = read_data['Time'][begin_consolidation:end_consolidation] - \
                                        read_data['Time'][begin_consolidation]

                if camera == "A":
                    rod_accounting = (read_data['VerticalDeformation'][begin_consolidation:end_consolidation] -
                                      read_data['VerticalDeformation'][begin_consolidation]) / (
                                             np.pi * (10 ** 2) * (76 - delta_h))
                    consolidation["cell_volume_strain"] -= rod_accounting

                return consolidation
            except (ValueError, IndexError):
                return None

        def define_deviator_loading(read_data, delta_h):
            """Обработка девиаторного нагружения"""
            deviator_loading = {}

            try:
                begin_deviator_loading = read_data['Trajectory'].index('CTC')
                iload = read_data['Action'][begin_deviator_loading:].index('WaitLimit')
                begin_deviator_loading += iload

                try:
                    end_deviator_loading = read_data['Action'].index('Unload')
                except (ValueError, IndexError):
                    end_deviator_loading = len(read_data['VerticalDeformation'])

                deviator_loading["strain"] = (read_data['VerticalDeformation'][
                                              begin_deviator_loading:end_deviator_loading] - \
                                              read_data['VerticalDeformation'][begin_deviator_loading]) / (76 - delta_h)

                deviator_loading["deviator"] = read_data['Deviator'][begin_deviator_loading:end_deviator_loading] - \
                                               read_data['Deviator'][begin_deviator_loading]

                deviator_loading["cell_volume_strain"] = -((read_data["CellVolume"][
                                                            begin_deviator_loading:end_deviator_loading] - \
                                                            read_data["CellVolume"][begin_deviator_loading]) / (
                                                                   np.pi * (19 ** 2) * (76 - delta_h)))
                deviator_loading["pore_volume_strain"] = (read_data["PoreVolume"][
                                                          begin_deviator_loading:end_deviator_loading] - \
                                                          read_data["PoreVolume"][begin_deviator_loading]) / (
                                                                 np.pi * (19 ** 2) * (76 - delta_h))
                deviator_loading["sigma_3"] = np.mean(read_data["CellPress"][begin_deviator_loading:end_deviator_loading] -
                                                      read_data["PorePress"][begin_deviator_loading:end_deviator_loading])

                deviator_loading["u"] = np.mean(read_data["PorePress"][begin_deviator_loading:end_deviator_loading])

                deviator_loading["pore_pressure"] = read_data["PorePress"][begin_deviator_loading:end_deviator_loading]

                deviator_loading["pore_pressure"] = deviator_loading["pore_pressure"] - deviator_loading["pore_pressure"][0]

                if camera == "A":
                    rod_accounting = (read_data['VerticalDeformation'][begin_deviator_loading:end_deviator_loading] -
                                      read_data['VerticalDeformation'][begin_deviator_loading]) / (
                                             np.pi * (10 ** 2) * (76 - delta_h))
                    deviator_loading["cell_volume_strain"] -= rod_accounting

                # Разгрузка
                try:
                    begin_upload = read_data['Action'].index('CyclicUnloading')
                    deviator_loading["reload_points"] = [begin_upload - begin_deviator_loading,
                                                         read_data['Action'].index('CyclicLoading') -
                                                         begin_deviator_loading,
                                                         read_data['Action'][begin_upload:].index('WaitLimit') +
                                                         begin_upload - begin_deviator_loading]
                except (ValueError, IndexError):
                    deviator_loading["reload_points"] = None

                return deviator_loading

            except (ValueError, IndexError):
                return None

        # Обштй вид результирующей структуры данных
        test_data = {"reconsolidation": {"pore_pressure": None, "cell_pressure": None, "action": None, "delta_h": None},

                     "consolidation": {"time": None, "cell_volume_strain": None, "pore_volume_strain": None,
                                       "delta_h": None},

                     "deviator_loading": {"sigma_3": None, "strain": None, "deviator": None, "cell_volume_strain": None,
                                          "pore_volume_strain": None, "reload_points": None, "delta_h": None, "u": None}
                     }

        column_keys = ['VerticalDeformation', 'Deviator', 'CellVolume', 'PoreVolume', 'Time', 'Action',
                       'Trajectory', 'CellPress', 'PorePress']

        # Считываем файл
        f = open(file_path)
        lines = f.readlines()
        f.close()

        columns_dict = find_current_columns(lines[0].split("\t"), column_keys)

        # Словарь считанных данных по ключам колонок
        read_data = {}

        for key in columns_dict:  # по нужным столбцам
            try:
                read_data[key] = np.array(
                    list(map(lambda x: float(x.split("\t")[columns_dict[key]["index"]].replace(",", ".")), lines[1:])))
            except ValueError:
                read_data[key] = list(
                    map(lambda x: x.split("\t")[columns_dict[key]["index"]].replace(",", "."), lines[1:]))

        # Обработка реконсолидации
        test_data["reconsolidation"] = define_reconsolidation(read_data)

        if test_data["reconsolidation"]:
            delta_h_reconsolidation = test_data["reconsolidation"].get("delta_h", 0)
        else:
            delta_h_reconsolidation = 0

        test_data["consolidation"] = define_consolidation(read_data, delta_h_reconsolidation)

        if test_data["consolidation"]:
            delta_h_consolidation = test_data["consolidation"].get("delta_h_consolidation", 0)
        else:
            delta_h_consolidation = 0

        test_data["deviator_loading"] = define_deviator_loading(read_data, delta_h_consolidation)

        return test_data

class ModelResistanseSoilTest(ModelTriaxialDeviatorLoadingSoilTest):

    def __init__(self):
        super().__init__()
        self._test_params.c_vibration = None
        self._test_params.fi_vibration = None

        self._test_params.frequency = None
        self._test_params.sigma_d = None

    def _test_modeling(self, Ms=None):
        self.set_velocity_delta_h(0.001, 0)

        self._test_params.c_vibration = statment[statment.current_test].mechanical_properties.c *0.5
        self._test_params.fi_vibration = statment[statment.current_test].mechanical_properties.fi * 0.7

        self._test_params.frequency = 10
        self._test_params.sigma_d = 10

        super()._test_modeling()
        time = np.linspace(0, (self._test_data.strain_cut[-1]/0.03)*60, len(self._test_data.strain_cut))

        qf = define_qf(self._test_params.sigma_3, self._test_params.c_vibration, self._test_params.fi_vibration) * np.random.uniform(0.9, 1.1)
        self._test_data.deviator_cut *= (qf/np.max(self._test_data.deviator_cut))

        self._test_data.deviator_cut += self._test_params.sigma_d * np.sin(self._test_params.frequency*2*np.pi*time)
        self._test_data.strain_cut += (self._test_params.sigma_d/(self._test_params.E50 * 3)) * np.sin(self._test_params.frequency*2 * np.pi * time)

        self._test_data.deviator_cut += np.random.uniform(-1, 1, len(self._test_data.deviator_cut))
        self._test_data.strain_cut += np.random.uniform(-0.0001, 0.0001, len(self._test_data.deviator_cut))

        self._test_data.deviator_cut -= self._test_data.deviator_cut[0]
        self._test_data.strain_cut -= self._test_data.strain_cut[0]

        self._test_result.qf = np.round(np.max(self._test_data.deviator_cut)/ 1000, 3)
        self._test_result.max_pore_pressure = 0

    def get_test_results(self):
        """Получение результатов обработки опыта"""
        dict = copy.deepcopy(self._test_result.get_dict())
        dict["sigma_3"] = np.round((self._test_params.sigma_3) / 1000, 3)
        return dict

class ModelTriaxialStaticLoadSoilTest(ModelTriaxialStaticLoad):
    """Класс моделирования опыта трехосного сжатия
    Структура класса представляет объеденение 3х моделей"""
    def __init__(self):
        # Основные модели опыта
        self.reconsolidation = ModelTriaxialReconsolidationSoilTest()
        self.consolidation = ModelTriaxialConsolidationSoilTest()
        self.deviator_loading = ModelTriaxialDeviatorLoadingSoilTest()# ModelResistanseSoilTest()
        self.test_params = None

    def set_test_params(self, reconsolidation=True, consolidation=True, pre_defined_kr_fgs=None):
        """Получение массивов опытов и передача в соответствующий класс"""
        if reconsolidation:
            self.reconsolidation.set_test_params()
            delta_h_reconsolidation = self.reconsolidation.get_test_results()["delta_h_reconsolidation"]
        else:
            self.reconsolidation = None
            delta_h_reconsolidation = 0

        if consolidation:
            velocity = None
            while velocity is None:
                self.consolidation.set_delta_h_reconsolidation(delta_h_reconsolidation)
                self.consolidation.set_test_params()
                velocity = self.consolidation.get_test_results()["velocity"]
                delta_h_consolidation = self.consolidation.get_delta_h_consolidation()
        else:
            self.consolidation = None
            velocity = 1
            delta_h_consolidation = 0

        self.deviator_loading.set_velocity_delta_h(velocity, delta_h_consolidation)

        poisons_ratio = 0
        poisons_ratio_global = statment[statment.current_test].mechanical_properties.poisons_ratio
        iteration = 0

        while (poisons_ratio > poisons_ratio_global + 0.03 or poisons_ratio < poisons_ratio_global - 0.03):
            try:
                self.deviator_loading.set_test_params(pre_defined_kr_fgs=pre_defined_kr_fgs)
            except TypeError:
                self.deviator_loading.set_test_params()
            iteration += 1
            poisons_ratio = self.deviator_loading.get_test_results()["poissons_ratio"]
            if iteration == 5:
                break

        if iteration == 0:
            try:
                self.deviator_loading.set_test_params(pre_defined_kr_fgs=pre_defined_kr_fgs)
            except TypeError:
                self.deviator_loading.set_test_params()

    def get_test_params(self):
        return self.test_params

    def get_consolidation_draw_params(self):
        """Метод считывает параметры отрисованных опытов для передачи на ползунки"""
        return self.consolidation.get_draw_params()

    def get_deviator_loading_draw_params(self):
        """Метод считывает параметры отрисованных опытов для передачи на ползунки"""
        return self.deviator_loading.get_draw_params()

    def get_deviator_loading_draw_params_unload_start_y(self):
        return self.deviator_loading.get_draw_params_unload_start_y()

    def set_consolidation_draw_params(self, params):
        """Передача параметров для перерисовки графиков"""
        self.consolidation.set_draw_params(params)

    def set_deviator_loading_draw_params(self, params):
        """Передача параметров для перерисовки графиков"""
        self.deviator_loading.set_draw_params(params)

    def set_deviator_loading_draw_params_unload_start_y(self, params):
        self.deviator_loading.set_draw_params_unload_start_y(params)

    def save_log_file(self, file_path, sample_size: Tuple[int, int] = (76, 38)):
        """Метод генерирует логфайл прибора"""

        if self.reconsolidation is not None:
            reconsolidation_dict = self.reconsolidation.get_dict(sample_size=sample_size)
            effective_stress_after_reconsolidation = self.reconsolidation.get_effective_stress_after_reconsolidation()
        else:
            reconsolidation_dict = None
            effective_stress_after_reconsolidation = 0

        if self.consolidation is not None:
            consolidation_dict = self.consolidation.get_dict(effective_stress_after_reconsolidation, sample_size=sample_size)
        else:
            consolidation_dict = dictionary_without_VFS(sigma_3=self.deviator_loading._test_params.sigma_3, velocity=49, sample_size=sample_size)

        deviator_loading_dict = self.deviator_loading.get_dict(sample_size=sample_size)
        main_dict = ModelTriaxialStaticLoadSoilTest.triaxial_deviator_loading_dictionary(reconsolidation_dict,
                                                                                         consolidation_dict,
                                                                                         deviator_loading_dict,
                                                                                         sample_size=sample_size)

        ModelTriaxialStaticLoadSoilTest.text_file(file_path, main_dict)
        create_json_file('/'.join(os.path.split(file_path)[:-1]) + "/processing_parameters.json",
                         self.get_processing_parameters())

        try:
            plaxis = self.deviator_loading.get_plaxis_dictionary()
            with open('/'.join(os.path.split(file_path)[:-1]) + "/plaxis_log.txt", "w") as file:
                for i in range(len(plaxis["strain"])):
                    file.write(f"{plaxis['strain'][i]}\t{plaxis['deviator'][i]}\n")
        except Exception as err:
            app_logger.exception(f"Проблема сохранения массива для plaxis {statment.current_test}")


    def save_cvi_file(self, file_path, file_name):
        if statment.general_parameters.equipment == "АСИС ГТ.2.0.5 (150х300)":
            d, h = 150, 300
        else:
            d, h = statment[statment.current_test].physical_properties.sample_size

        sample_aria = round(((d/10) / 2)**2 * 3.14, 1)

        if (d == 38 and h == 76) or (d == 50 and h == 100):
            stock_aria = 3.1
        elif d == 100 and h == 200:
            stock_aria = round((2.5 / 2)**2 * 3.14, 1)
        elif d == 150 and h == 300:
            stock_aria = round((4 / 2) ** 2 * 3.14, 1)

        data = {
            "laboratory_number": statment[statment.current_test].physical_properties.laboratory_number,
            "borehole": statment[statment.current_test].physical_properties.borehole,
            "ige": statment[statment.current_test].physical_properties.ige,
            "depth": statment[statment.current_test].physical_properties.depth,
            "sample_composition": "Н" if statment[statment.current_test].physical_properties.type_ground in [1, 2, 3, 4, 5] else "С",
            "b": np.round(np.random.uniform(0.95, 0.98), 2),
            "sample_aria": sample_aria,
            "stock_aria": stock_aria,
            "test_data": {
            }
        }

        strain, main_stress, volume_strain = self.deviator_loading.get_cvi_data(points=20)

        data["test_data"]["1"] = {
            "main_stress": main_stress,
            "strain": strain,
            "volume_strain": volume_strain,
            "sigma_3": np.round(E_models[statment.current_test].deviator_loading._test_params.sigma_3 / 1000, 3)
        }

        save_cvi_E(file_path=os.path.join(file_path,file_name), data=data)

    def set_pickle_data(self, test):

        if test.reconsolidation is None:
            self.reconsolidation = None
        else:
            self.reconsolidation._test_data = copy.deepcopy(test.reconsolidation._test_data)
            self.reconsolidation._test_result = copy.deepcopy(test.reconsolidation._test_result)
            self.reconsolidation._test_data_all = copy.deepcopy(test.reconsolidation._test_data_all)
            self.reconsolidation.params = copy.deepcopy(test.reconsolidation.params)

        if test.consolidation is None:
            self.consolidation = None
        else:
            self.consolidation._test_data = copy.deepcopy(test.consolidation._test_data)
            self.consolidation._test_cut_position = copy.deepcopy(test.consolidation._test_cut_position)
            self.consolidation.processed_points_sqrt = copy.deepcopy(test.consolidation.processed_points_sqrt)
            self.consolidation.processed_points_log = copy.deepcopy(test.consolidation.processed_points_log)
            self.consolidation._test_result = copy.deepcopy(test.consolidation._test_result)
            self.consolidation._test_params = copy.deepcopy(test.consolidation._test_params)
            self.consolidation._test_result = copy.deepcopy(test.consolidation._test_result)
            self.consolidation._test_params = copy.deepcopy(test.consolidation._test_params)

        self.deviator_loading._test_data = copy.deepcopy(test.deviator_loading._test_data)
        self.deviator_loading._test_params = copy.deepcopy(test.deviator_loading._test_params)
        self.deviator_loading._draw_params = copy.deepcopy(test.deviator_loading._draw_params)
        self.deviator_loading._test_cut_position = copy.deepcopy(test.deviator_loading._test_cut_position)
        self.deviator_loading._test_result = copy.deepcopy(test.deviator_loading._test_result)

        try:
            self.deviator_loading._test_data.time
        except AttributeError:
            self.deviator_loading._test_data.time = self.deviator_loading._test_data.strain/self.deviator_loading._test_params.velocity

        q_c = self.deviator_loading._test_params.sigma_3 * ((1 / self.deviator_loading._test_params.K0) - 1)

        q_c2 = self.deviator_loading._test_params.sigma_3 * ((1.6 / self.deviator_loading._test_params.K0) - 1)

        if self.deviator_loading._test_params.K0 == 1:
            i_start_E = 0
        else:
            i_start_E, = np.where(self.deviator_loading._test_data.deviator_cut >= q_c)
            if len(i_start_E):
                i_start_E = i_start_E[0]
            else:
                i_start_E = 0

        if q_c == 0:
            i_end_E, = np.where(
                self.deviator_loading._test_data.deviator_cut >= np.max(self.deviator_loading._test_data.deviator_cut) * np.random.uniform(0.2, 0.3))
            if len(i_end_E):
                i_end_E = i_end_E[0]
            else:
                i_end_E = len(self.deviator_loading._test_data.deviator_cut) - 1
        else:
            i_end_E, = np.where(self.deviator_loading._test_data.deviator_cut >= q_c2)
            if len(i_end_E):
                i_end_E = i_end_E[0]
            else:
                i_end_E = len(self.deviator_loading._test_data.deviator_cut) - 1

        if i_end_E <= i_start_E:
            i_end_E = i_start_E + 1

        self.deviator_loading._test_params.E_processing_points_index = [i_start_E, i_end_E]



        self.deviator_loading._test_result.E = ModelTriaxialDeviatorLoading.define_E(self.deviator_loading._test_data.strain_cut,
                                                                    self.deviator_loading._test_data.deviator_cut,
                                                                    self.deviator_loading._test_params.E_processing_points_index)

        if self.deviator_loading._test_result.E[0] <= self.deviator_loading._test_result.E50 / 1000:
            i_start_E = 0
            i_end_E, = np.where(
                self.deviator_loading._test_data.deviator_cut >= np.max(self.deviator_loading._test_data.deviator_cut) * np.random.uniform(0.25, 0.35))
            i_end_E = i_end_E[0]
            self.deviator_loading._test_params.E_processing_points_index = [i_start_E, i_end_E]

        #self.deviator_loading._test_processing()

    @property
    def test_duration(self):
        time_in_min = 0
        for test_parts in [self.reconsolidation, self.deviator_loading]:
            if test_parts:
                time_in_min += test_parts.get_duration()

        if self.consolidation:
            time_in_min += self.consolidation.get_duration()
        else:
            time_in_min += (30 + (self.deviator_loading._test_params.sigma_3/49))

        return timedelta(minutes=time_in_min)

    @staticmethod
    def addition_of_dictionaries(data1, data2, initial=True, skip_keys=None):
        if data1 is None and data2 is None:
            return None
        elif data1 is None:
            return copy.deepcopy(data2)
        elif data2 is None:
            return copy.deepcopy(data1)

        dictionary_1 = copy.deepcopy(data1)
        dictionary_2 = copy.deepcopy(data2)
        if skip_keys is None:
            skip_keys = ['']
        keys_d1 = list(dictionary_1.keys())  # массив ключей словаря 1
        len_d1_elem = len(dictionary_1[keys_d1[0]])  # длина массива под произвольным ключем словаря 1
        keys_d2 = list(dictionary_2.keys())  # массив ключей словаря 2
        len_d2_elem = len(dictionary_2[keys_d2[0]])  # длина массива под произвольным ключем словаря 2

        for key in dictionary_1:
            if key in dictionary_2:  # если ключ есть в словаре 2
                if initial and (str(type(dictionary_1[key][0])) not in ["<class 'str'>", "<class 'numpy.str_'>"]) and (
                        key not in skip_keys):  # если initial=True и элементы под ключем не строки
                    # к эламентам словаря 2 прибавляется последний элемент словаря 1 под одним ключем
                    for val in range(len(dictionary_2[key])):
                        dictionary_2[key][val] += dictionary_1[key][-1]
                dictionary_1[key] = np.append(dictionary_1[key], dictionary_2[key])
            else:  # если ключа нет в словаре 2
                dictionary_1[key] = np.append(dictionary_1[key], np.full(len_d2_elem, ''))

        for key in dictionary_2:  # если ключа нет в словаре 1
            if key not in dictionary_1:
                dictionary_1[key] = np.append(np.full(len_d1_elem, ''), dictionary_2[key])

        return dictionary_1

    @staticmethod
    def text_file(file_path, data):
        """Сохранение текстового файла формата Willie.
                    Передается папка, массивы"""
        p = os.path.join(file_path, "Тест.log")

        def make_string(data, i):
            s = ""
            for key in data:
                s += str(data[key][i]) + '\t'
            s += '\n'
            return (s)

        with open(file_path, "w") as file:
            file.write(
                "Time" + '\t' + "Action" + '\t' + "Action_Changed" + '\t' + "SampleHeight_mm" + '\t' + "SampleDiameter_mm" + '\t' +
                "Deviator_kPa" + '\t' + "VerticalDeformation_mm" + '\t' + "CellPress_kPa" + '\t' + "CellVolume_mm3" + '\t' +
                "PorePress_kPa" + '\t' + "PoreVolume_mm3" + '\t' + "VerticalPress_kPa" + '\t' +
                "Trajectory" + '\n')
            for i in range(len(data["Time"])):
                file.write(make_string(data, i))

    @staticmethod
    def text_file_new(file_path, data):
        """Сохранение текстового файла формата Willie.
                    Передается папка, массивы"""
        p = os.path.join(file_path, "Тест.log")

        def make_string(data, i):
            s = ""
            for key in data:
                s += str(data[key][i]) + '\t'
            s += '\n'
            return (s)

        with open(file_path, "w") as file:
            file.write(
                "Time" + '\t' + "Action" + '\t' + "Action_Changed" + '\t' + "SampleHeight_mm" + '\t' + "SampleDiameter_mm" + '\t' +
                "Deviator_kPa" + '\t' + "VerticalDeformation_mm" + '\t' + "CellPress_kPa" + '\t' + "CellVolume_mm3" + '\t' +
                "PorePress_kPa" + '\t' + "PoreVolume_mm3" + '\t' + "VerticalPress_kPa" + '\t' +
                "Trajectory" + '\n')
            for i in range(len(data["Time"])):
                file.write(make_string(data, i))

    @staticmethod
    def number_format(x, characters_number=0, split=".", change_negatives=True):
        """Функция возвращает число с заданным количеством знаков после запятой
        :param characters_number: количество знаков после запятой
        :param format: строка или число
        :param split: кразделитель дробной части. точка или запятая
        :param change_negatives: удаление начального знака минус"""

        if str(type(x)) in ["<class 'numpy.float64'>", "<class 'numpy.int32'>", "<class 'int'>", "<class 'float'>"]:
            # установим нужный формат
            _format = "{:." + str(characters_number) + "f}"
            round_x = np.round(x, characters_number)
            x = _format.format(round_x)

            # Уберем начальный минус  (появляется, например, когда округляем -0.0003 до 1 знака)
            if change_negatives:
                if x[0] == "-":
                    x = x[1:len(x)]

            if split == ".":
                return x
            elif split == ",":
                return x.replace(".", ",")


        else:
            _format = "{:." + str(characters_number) + "f}"

            if str(type(x)) == "<class 'numpy.ndarray'>":
                x = list(x)

            for i in range(len(x)):
                # Уберем начальный минус  (появляется, например, когда округляем -0.0003 до 1 знака)
                x[i] = _format.format(x[i])
                if change_negatives:
                    if x[i][0] == "-":
                        x[i] = x[i][1:len(x)]

                if split == ".":
                    pass
                elif split == ",":
                    x[i].replace(".", ",")

            return x

    @staticmethod
    def current_value_array(array, number, change_negatives=True):
        s = []
        for i in range(len(array)):
            num = ModelTriaxialStaticLoadSoilTest.number_format(array[i], number, change_negatives=change_negatives).replace(".", ",")
            if num in ["0,0", "0,00", "0,000", "0,0000", "0,00000","0,000000"]:
                num = "0"
            s.append(num)
        return s

    @staticmethod
    def triaxial_deviator_loading_dictionary(b_test, consolidation, deviator_loading,
                                             sample_size: Tuple[int, int] = (76, 38)):

        start = np.random.uniform(0.5, 0.8)
        dict = {
            'Time': [0, 0, np.round(start, 3), np.round(start + 0.1, 3), np.round(start + 2, 3)],
            'Action': ["", "", "Start", "Start", "Start"],
            'Action_Changed': ["", "True", "", "", "True"],
            'SampleHeight_mm': np.full(5, sample_size[0]),
            'SampleDiameter_mm': np.full(5, sample_size[1]),
            'Deviator_kPa': np.full(5, 0),
            'VerticalDeformation_mm': np.full(5, 0),
            'CellPress_kPa': np.full(5, 0),
            'CellVolume_mm3': np.full(5, 0),
            'PorePress_kPa': np.full(5, 0),
            'PoreVolume_mm3': np.full(5, 0),
            'VerticalPress_kPa': np.full(5, 0),
            'Trajectory': np.full(5, "HC")

            # 'skempton': skempton_step,
            # 'step_pressure': sigma_steps
        }

        data_start = ModelTriaxialStaticLoadSoilTest.addition_of_dictionaries(dict, b_test, initial=True,
                                                                        skip_keys=["SampleHeight_mm",
                                                                                   "SampleDiameter_mm"])

        data = ModelTriaxialStaticLoadSoilTest.addition_of_dictionaries(copy.deepcopy(data_start), consolidation, initial=True,
                                                                        skip_keys=["SampleHeight_mm",
                                                                                   "SampleDiameter_mm"])

        dictionary = ModelTriaxialStaticLoadSoilTest.addition_of_dictionaries(copy.deepcopy(data), deviator_loading, initial=True,
                                              skip_keys=["SampleHeight_mm", "SampleDiameter_mm", "Action_Changed"])


        dictionary["Time"] = ModelTriaxialStaticLoadSoilTest.current_value_array(dictionary["Time"], 3)
        dictionary["Deviator_kPa"] = ModelTriaxialStaticLoadSoilTest.current_value_array(dictionary["Deviator_kPa"], 3)
        # dictionary["VerticalDeformation_mm"] = current_value_array(dictionary["VerticalDeformation_mm"], 5)

        # Для части девиаторного нагружения вертикальная деформация хода штока должна писаться со знаком "-"
        CTC_index, = np.where(dictionary["Trajectory"] == 'CTC')
        str = ModelTriaxialStaticLoadSoilTest.current_value_array(dictionary["VerticalDeformation_mm"][:CTC_index[0]], 5)
        str.extend(ModelTriaxialStaticLoadSoilTest.current_value_array(dictionary["VerticalDeformation_mm"][CTC_index[0]:], 5, change_negatives=False))
        dictionary["VerticalDeformation_mm"] = str

        dictionary["CellPress_kPa"] = ModelTriaxialStaticLoadSoilTest.current_value_array(dictionary["CellPress_kPa"], 5)
        dictionary['CellVolume_mm3'] = ModelTriaxialStaticLoadSoilTest.current_value_array(dictionary["CellVolume_mm3"],
                                                                                          5)
        dictionary['PoreVolume_mm3'] = ModelTriaxialStaticLoadSoilTest.current_value_array(dictionary["PoreVolume_mm3"],
                                                                                           5)
        #dictionary["CellVolume_mm3"] = dictionary["CellVolume_mm3"]
        dictionary["PorePress_kPa"] = ModelTriaxialStaticLoadSoilTest.current_value_array(dictionary["PorePress_kPa"], 5)
        #dictionary["PoreVolume_mm3"] = dictionary["PoreVolume_mm3"]
        dictionary["VerticalPress_kPa"] = ModelTriaxialStaticLoadSoilTest.current_value_array(dictionary["VerticalPress_kPa"], 5)


        return dictionary


if __name__ == '__main__':

    file = r"C:\Users\Пользователь\PycharmProjects\Willie\Test.1.log"
    file = r"Z:\МДГТ - Механика\3. Трехосные испытания\1365\Test\Test.1.log"
    #file = r"C:\Users\Пользователь\Desktop\Девиаторное нагружение\Архив\7а-1\Test sigma3=186.4.log"
    #a = ModelTriaxialStaticLoading()
    #a.set_test_data(openfile(file)["DeviatorLoading"])
    #a.plotter()



    #file = r"Z:\МДГТ - Механика\3. Трехосные испытания\1375\Test\Test.1.log"

    #a = ModelTriaxialConsolidationSoilTest()
    #a.set_test_params({"Cv": 0.178,
                       #"Ca": 0.0001,
                      # "E": 50000,
                      # "sigma_3": 100,
                      # "K0": 1})
    #a.plotter()
    #a = ModelTriaxialReconsolidation()
    #a.open_file(file)
    #open_geotek_log(file)

    #a = ModelTriaxialStaticLoadSoilTest()
    param = { "ee": {'physical_properties': {'laboratory_number': '89-3', 'borehole': 89.0, 'depth': 6.0,
                                     'soil_name': 'Суглинок полутвёрдый', 'ige': None, 'rs': 2.71, 'r': 2.16,
                                     'rd': 1.89, 'n': 30.1, 'e': 0.43, 'W': 21.9, 'Sr': 0.88, 'Wl': 21.9, 'Wp': 12.8,
                                     'Ip': 9.1, 'Il': 0.13, 'Ir': None, 'stratigraphic_index': None,
                                     'ground_water_depth': None, 'granulometric_10': None, 'granulometric_5': None,
                                     'granulometric_2': None, 'granulometric_1': None, 'granulometric_05': None,
                                     'granulometric_025': None, 'granulometric_01': None, 'granulometric_005': None,
                                     'granulometric_001': None, 'granulometric_0002': None, 'granulometric_0000': None,
                                     'complete_flag': False, 'sample_number': 53, 'type_ground': 7, 'Rc': None},
             'Cv': 0.128, 'Ca': 0.01126, 'm': 0.6, 'E50': 29600.0, 'c': 0.06, 'fi': 24.6, 'K0': 0.7,
             'dilatancy_angle': 17.05, 'sigma_3': 100, 'qf': 329.5, 'sigma_1': 429.5, 'poisons_ratio': 0.34, 'OCR': 1,
             'build_press': 150.0, 'pit_depth': 4.0, 'Eur': None}}

    param = dictToData(param, MechanicalProperties)

    test = "soil_test"

    if test == "soil_test":
        a = ModelTriaxialStaticLoadSoilTest()
        a.set_test_params(param["ee"])
        a.save_log_file("C:/Users/Пользователь/Desktop/Test.1.log")
        a.plotter()
    else:
        a = ModelTriaxialStaticLoad()
        #a.set_test_file_path("C:/Users/Пользователь/Desktop/Тест/Девиаторное нагружение/Архив/7а-3/Test.1.log")
        a.set_test_file_path("C:/Users/Пользователь/Desktop/Test.1.log")
        a.plotter()




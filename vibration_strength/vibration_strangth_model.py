from static_loading.deviator_loading_model import ModelTriaxialDeviatorLoadingSoilTest
from static_loading.triaxial_static_loading_test_model import ModelTriaxialStaticLoadSoilTest, \
    ModelTriaxialConsolidationSoilTest, ModelTriaxialReconsolidationSoilTest
from cyclic_loading.cyclic_loading_model import ModelTriaxialCyclicLoadingSoilTest
import numpy as np
from static_loading.mohr_circles_test_model import ModelMohrCirclesSoilTest
from typing import List
from static_loading.deviator_loading_functions import curve
from singletons import statment
import os

class CyclicVibrationStrangth(ModelTriaxialDeviatorLoadingSoilTest):
    def set_test_params(self):
        self._test_params.frequency = statment[statment.current_test].mechanical_properties.frequency
        self._test_params.sigma_d = statment[statment.current_test].mechanical_properties.sigma_d
        self._test_params.step = statment[statment.current_test].mechanical_properties.step
        self._test_params.u = statment[statment.current_test].mechanical_properties.u
        ModelTriaxialDeviatorLoadingSoilTest.set_test_params(self)

    def _test_modeling(self):
        """Функция моделирования опыта"""
        # Время проведения опыта
        self._test_params.velocity = 0.1

        max_time = int((0.15 * (76)) / self._test_params.velocity)
        if max_time <= 500:
            max_time = 500

        dilatancy = np.rad2deg(np.arctan(2 * np.sin(np.deg2rad(self._draw_params.dilatancy)) /
                                         (1 - np.sin(np.deg2rad(self._draw_params.dilatancy)))))

        self._test_data.strain, self._test_data.deviator, self._test_data.pore_volume_strain, \
        self._test_data.cell_volume_strain, self._test_data.reload_points, begin = curve(
            self._test_params.qf, self._test_params.E50, xc=self._draw_params.fail_strain,
            x2=self._draw_params.residual_strength_param,
            qf2=self._draw_params.residual_strength,
            qocr=self._draw_params.qocr,
            m_given=self._draw_params.poisson,
            amount_points=max_time,
            angle_of_dilatacy=dilatancy,
            v_d_xc=-self._draw_params.volumetric_strain_xc,
            U=self._test_params.u)

        i_end = ModelTriaxialDeviatorLoadingSoilTest.define_final_loading_point(self._test_data.deviator,
                                                                                0.08 + np.random.uniform(0.01, 0.03))
        self._test_data.strain = self._test_data.strain[:i_end]
        self._test_data.deviator = self._test_data.deviator[:i_end]
        self._test_data.pore_volume_strain = self._test_data.pore_volume_strain[:i_end]
        self._test_data.cell_volume_strain = self._test_data.cell_volume_strain[:i_end]

        if self._test_params.u:
            self._test_data.pore_pressure = ModelTriaxialDeviatorLoadingSoilTest.define_pore_pressure_array(
                self._test_data.strain, begin, self._test_params.u,
                self._test_data.deviator[begin] * np.random.uniform(1, 2))
        else:
            self._test_data.pore_pressure = np.random.uniform(-1, 1, len(self._test_data.strain))

        # plt.plot(self._test_data.strain, self._test_data.pore_pressure)
        # plt.plot(self._test_data.strain, self._test_data.deviator)
        # plt.show()

        # Действия для того, чтобы полученный массив данных записывался в словарь для последующей обработки
        k = np.max(
            np.round(self._test_data.deviator[begin:] - self._test_data.deviator[begin], 3)) / self._test_params.qf
        self._test_data.deviator = np.round(self._test_data.deviator / k, 3)

        self._test_data.strain = np.round(
            self._test_data.strain * (76 - self._test_params.delta_h_consolidation) / (
                    76 - self._test_params.delta_h_consolidation), 6)

        self._test_data.pore_volume_strain = np.round((self._test_data.pore_volume_strain * np.pi * 19 ** 2 * (
                76 - self._test_params.delta_h_consolidation)) / (np.pi * 19 ** 2 * (
                76 - self._test_params.delta_h_consolidation)), 6)
        self._test_data.cell_volume_strain = np.round((self._test_data.cell_volume_strain * np.pi * 19 ** 2 * (
                76 - self._test_params.delta_h_consolidation)) / (np.pi * 19 ** 2 * (
                76 - self._test_params.delta_h_consolidation)), 6)

        self._test_data.volume_strain = self._test_data.pore_volume_strain
        # i_end, = np.where(self._test_data.strain > self._draw_params.fail_strain + np.random.uniform(0.03, 0.04))
        # if len(i_end):
        # self.change_borders(begin, i_end[0])
        # else:
        self._test_cut_position.left = begin
        self._test_cut_position.right = len(self._test_data.volume_strain)
        self._cut()

        si_start_E = 0
        i_end_E, = np.where(
            self._test_data.deviator_cut >= np.max(self._test_data.deviator_cut) * np.random.uniform(0.25, 0.35))
        i_end_E = i_end_E[0]
        self._test_params.E_processing_points_index = [0, i_end_E]

        self._test_processing()

        strain, deviator, pore_volume_strain, \
        cell_volume_strain, reload_points, begin = curve(
            self._test_params.qf, self._test_params.E50 * np.random.uniform(0.7, 0.8), xc=self._draw_params.fail_strain,
            x2=self._draw_params.residual_strength_param,
            qf2=self._draw_params.residual_strength,
            qocr=self._draw_params.qocr,
            m_given=self._draw_params.poisson,
            amount_points=max_time,
            angle_of_dilatacy=dilatancy,
            v_d_xc=-self._draw_params.volumetric_strain_xc,
            U=self._test_params.u)

        strain_cut = strain[begin:len(deviator)] - strain[begin]
        deviator_cut = deviator[begin:len(deviator)] - deviator[begin]

        cycles = np.linspace(0, 500, 20 * 500 + 1)
        split = CyclicVibrationStrangth.splitter(self._test_data.strain_cut, self._test_data.deviator_cut,
                                                 pore_pressure_1=self._test_data.pore_pressure,
                                                 time_1=np.linspace(0, int((self._test_data.strain_cut[-1] * 76) / self._test_params.velocity), len(self._test_data.strain_cut)),
                                                 step=self._test_params.step)
        offset = CyclicVibrationStrangth.strain_offset(strain_cut, deviator_cut, self._test_data.strain_cut,
                                                       self._test_data.deviator_cut, self._test_params.step)
        # s, d = CyclicVibrationStrangth.cyclic_step(np.linspace(0, 500, 20 * 500 + 1), self._test_params.sigma_d, 0.02,
        # self._test_params.E50)

        strain = np.array([0])
        deviator = np.array([0])
        pore_pressure = np.array([0])
        time = np.array([0])

        for key in split:
            deviator = np.hstack((deviator, split[key]["deviator"] - split[key]["deviator"][0] + deviator[-1]))
            strain = np.hstack((strain, split[key]["strain"] - split[key]["strain"][0] + strain[-1]))
            pore_pressure = np.hstack(
                (pore_pressure, split[key]["pore_pressure"] - split[key]["pore_pressure"][0] + pore_pressure[-1]))
            time = np.hstack((time, split[key]["time"] - split[key]["time"][0] + time[-1]))

            if (key != list(split.keys())[-1]):
                s, d, p, t = CyclicVibrationStrangth.cyclic_step(cycles, self._test_params.sigma_d,
                                                           offset[key]["offset"],
                                                           self._test_params.E50, self._test_params.frequency)
                if np.max(deviator[-1] + 2 * self._test_params.sigma_d) <= np.max(self._test_data.deviator_cut):
                    deviator = np.hstack((deviator, d + deviator[-1]))
                    strain = np.hstack((strain, s + strain[-1]))
                    pore_pressure = np.hstack((pore_pressure, p + pore_pressure[-1]))
                    time = np.hstack((time, t + time[-1]))

        self._test_data.strain_cut = strain
        self._test_data.deviator_cut = deviator
        self._test_data.time = time * 60
        self._test_data.pore_pressure = pore_pressure * (self._test_params.u / np.max(pore_pressure))

        self._test_result.max_pore_pressure = np.max(self._test_data.pore_pressure)

        # print(statment[statment.current_test].physical_properties.laboratory_number, self._test_result["E50"])
        # print(self._test_params.__dict__)

    @staticmethod
    def cyclic_step(cycles, deviator_amplitude, max_strain, E50, frequency):
        deviator = deviator_amplitude * np.sin(cycles * 2 * np.pi) + np.random.uniform(-1, 1, len(cycles))

        strain_amplitude = deviator_amplitude / np.linspace(E50 * 5, E50 * np.random.uniform(3, 4), len(deviator))
        max_strain = max_strain - strain_amplitude[0] if (max_strain - strain_amplitude[0]) >= 0 else 0
        strain = strain_amplitude * np.sin(cycles * 2 * np.pi + np.random.uniform(0.05, 0.08) * np.pi) \
                 + CyclicVibrationStrangth.exponent(cycles, max_strain, np.random.uniform(4, 7))

        pore_pressure = deviator_amplitude * np.random.uniform(0.2, 0.4)*np.sin(cycles * 2 * np.pi) + np.random.uniform(-1, 1, len(cycles))

        time = np.round((np.arange(0, (500 / frequency) + 1 / (20 * frequency),
                                   1 / (20 * frequency))), 4)
        time /= 60

        return strain, deviator, pore_pressure, time

    @staticmethod
    def exponent(x, amplitude, slant):
        """Функция построения экспоненты
            Входные параметры: x - значение или массив абсцисс,
                               amplitude - значение верхней асимптоты,
                               slant - приведенный угол наклона (пологая - 1...3, резкая - 10...20 )"""
        k = slant / (max(x))
        return amplitude * (-np.e ** (-k * x) + 1)

    @staticmethod
    def splitter(strain_1: 'np.ndarray', deviator_1: 'np.ndarray', pore_pressure_1: 'np.ndarray'=None, time_1: 'np.ndarray'=None, step: float = 20, eps=0.5):
        result = {}
        ''' {`1`:{ `strain`: np.array, `deviator`: np.array}} '''

        if pore_pressure_1 is None:
            pore_pressure_1 = np.zeros(len(strain_1))

        if time_1 is None:
            pore_pressure_1 = np.zeros(len(strain_1))

        def split_array(__x) -> List[List[int]]:

            assert abs(
                __x[1] - __x[0]) < step, "Разница между первыми двумя значениями больше шага, возможна потеря точек"

            __index_max = np.argmax(__x)
            if __index_max == len(__x) - 1:
                __stop_point = 0
            else:
                __stop_point = len(__x) - __index_max

            __cond_result = []
            __last_true = 0

            for i in range(len(__x) - __stop_point):
                if abs(__x[i] - __last_true) > step + eps:
                    __cond_result.append(True)
                    __last_true = __last_true + step
                else:
                    __cond_result.append(False)

            __search = np.where(__cond_result)[0]

            __result = []
            __start = 0
            for index in __search:
                __result.append([i for i in range(__start, index)])
                __start = index
            __result.append([i for i in range(__start, len(__x))])
            return __result

        count = 1
        for item in split_array(deviator_1):
            result[count] = {"strain": np.asarray([strain_1[int(i)] for i in item]),
                             "deviator": np.asarray([deviator_1[int(i)] for i in item]),
                             "pore_pressure": np.asarray([pore_pressure_1[int(i)] for i in item]),
                             "time": np.asarray([pore_pressure_1[int(i)] for i in item])}
            count = count + 1
        return result

    @staticmethod
    def strain_offset(strain_1: 'np.ndarray', deviator_1: 'np.ndarray',
                      strain_2: 'np.ndarray', deviator_2: 'np.ndarray', step: float, eps=0.5):
        result = {}
        '''“1”: { “offset”: float}'''
        split_1 = CyclicVibrationStrangth.splitter(strain_1, deviator_1, step=step, eps=eps)
        split_2 = CyclicVibrationStrangth.splitter(strain_2, deviator_2, step=step, eps=eps)

        for key1 in split_1:
            if key1 in split_2:
                result[key1] = {"offset": split_1[key1]["strain"][-1] - split_2[key1]["strain"][-1]}

        return result

class ModelCyclicVibrationStrangthSoilTest(ModelTriaxialStaticLoadSoilTest):
    """Класс моделирования опыта трехосного сжатия
    Структура класса представляет объеденение 3х моделей"""

    def __init__(self):
        # Основные модели опыта
        self.reconsolidation = ModelTriaxialReconsolidationSoilTest()
        self.consolidation = ModelTriaxialConsolidationSoilTest()
        self.deviator_loading = CyclicVibrationStrangth()
        self.test_params = None

    def save_log_file(self, file_path):
        reconsolidation_time = (((0.848 * 3.8 * 3.8) /
          (4 * statment[statment.current_test].mechanical_properties.Cv))) * \
        np.random.uniform(5, 7) * 60 + np.random.uniform(3000, 5000)

        ModelTriaxialCyclicLoadingSoilTest.generate_willie_log_file(
            file_path,
            deviator=self.deviator_loading._test_data.deviator_cut,
            PPR=self.deviator_loading._test_data.pore_pressure / self.deviator_loading._test_params.sigma_3,
            strain=self.deviator_loading._test_data.strain_cut,
            frequency=self.deviator_loading._test_params.frequency,
            N=1,
            points_in_cycle=20,
            setpoint=self.deviator_loading._test_data.deviator_cut,
            cell_pressure=np.full(len(self.deviator_loading._test_data.deviator_cut), self.deviator_loading._test_params.sigma_3) + np.random.uniform(-0.5, 0.5, len(self.deviator_loading._test_data.deviator_cut)),
            reconsolidation_time=0,
            post_name=statment.current_test,
            time=self.deviator_loading._test_data.time)

class CyclicVibrationStrangthMohr(ModelMohrCirclesSoilTest):
    def add_test_st(self):
        """Добавление опытов"""
        test = ModelCyclicVibrationStrangthSoilTest()
        test.set_test_params(statment.general_parameters.reconsolidation)
        if self._check_clone(test):
            self._tests.append(test)
            self.sort_tests()

    def _test_modeling(self):
        c = statment[statment.current_test].mechanical_properties.c
        fi = statment[statment.current_test].mechanical_properties.fi

        statment[statment.current_test].mechanical_properties.c *= np.random.uniform(0.6, 0.8)
        statment[statment.current_test].mechanical_properties.fi *= np.random.uniform(0.6, 0.8)

        statment[statment.current_test].mechanical_properties.frequency = 5
        statment[statment.current_test].mechanical_properties.sigma_d = 5
        statment[statment.current_test].mechanical_properties.step = 30


        """u = max(statment[statment.current_test].mechanical_properties.pressure_array["current"]) * np.random.uniform(
            0.3, 0.5)

        statment[statment.current_test].mechanical_properties.u = [np.round(u * np.random.uniform(0.8, 0.9) * (
                i / max(statment[statment.current_test].mechanical_properties.pressure_array["current"])), 1) for i in
                                                                   statment[
                                                                       statment.current_test].mechanical_properties.pressure_array[
                                                                       "current"][:-1]] + [u]"""

        super()._test_modeling()

        statment[statment.current_test].mechanical_properties.c = c
        statment[statment.current_test].mechanical_properties.fi = fi

    def save_log_files(self, directory, name):
        """Метод генерирует файлы испытания для всех кругов"""

        if len(self._tests) >= 3:
            for test in self._tests:
                results = test.deviator_loading.get_test_results()
                print("Сейчас сохраняется с давлением ", str(results["sigma_3"]))
                path = os.path.join(directory, str(results["sigma_3"]))
                if not os.path.isdir(path):
                    os.mkdir(path)
                test.save_log_file(path)







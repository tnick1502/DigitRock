"""Модуль математических моделей реконсолидации. Содержит модели:
    ModelTriaxialReconsolidation - модель обработчика данных опыта консолидации.
    Принцип работы:
        Данные подаются в модель методом set_test_data(test_data) с определенными ключами. Функция открытия файла
        прибора openfile() находится в модуле text_file_functions
        Обработка опыта происходит с помощью метода _sqrt_processing() для метода квадратного корня и _log_processing
        для метода логарифма. Метод change_borders() служит для обработки границ массивов
        Метод _interpolate_volume_strain интерполирует/аппроксимирует объемную деформацию для обработки
        Метод plotter() позволяет вывести графики обработанного опыта
        Результаты получаются методом get_test_results()

    ModelTriaxialReconsolidationSoilTest - модель математического моделирования данных опыта консолидации.
    Наследует методы  _test_processing(), get_test_results(), plotter(), а также структуру данных из
    ModelTriaxialReconsolidation
    Принцип работы:
        Параметры опыта подаются в модель с помощью метода set_test_params().
        Метод get_params() Возвращает основные параметры отрисовки для последующей передачи на слайдеры
        Метод set_draw_params() устанавливает позьзовательские значения параметров отрисовки.
        Метод_test_modeling моделируют соотвествующие массивы опытных данных. Вызыванется при передачи пользовательских
         параметров отрисовки.."""

__version__ = 1

import numpy as np
import os
import sys
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

from general.general_functions import sigmoida, make_increas, line_approximate, line, define_poissons_ratio, mirrow_element, \
    define_dilatancy, define_type_ground, AttrDict, find_line_area, interpolated_intercept, Point, point_to_xy, \
    array_discreate_noise, create_stabil_exponent, discrete_array, create_deviation_curve, define_qf, define_E50
from configs.plot_params import plotter_params
from singletons import statment


class ModelTriaxialReconsolidation:
    """Определение коэффициента скемптона на конце этапа впд (или вфс, если впд отсутствует)
    Способы запуска:
    object.set_test_data(dict) - запускает расчет, если в наличие уже подготовленный словарь экспериментальных данных,
    odject.open_file(path) - запускает расчет по экспериментальным данным ГеоТек, находящимся по адресу path

    Получение результата - коэффициента скемптона:
    object.get_test_results()

    Коэффициент Скемптона:
     найденный по двум точкам: self._intermediate_data.scempton['two_point'],
     угловой коэффициент лин. участка активного нагружения: self._intermediate_data.scempton['approx'],
     средний (он же в get_test_results()), найденных по двум точкам (начальная и точек на участке,
     где поровое давлие стабилизировалось): self._intermediate_data.scempton['mean']
      """

    def __init__(self):
        # Основные массивы опыта
        self._reset_data()

    def _reset_data(self):
        """Обнуление входных параметров и результатов для обработки нового опыта"""
        self._test_data = AttrDict({"time": None,
                                    "action": None,
                                    "cell_pressure": None,
                                    "pore_pressure": None,
                                    "trajectory": None,

                                    'flag_reconsolidation': None,
                                    'index_list': None})
        # Промежуточные данные
        # flag_reconsolidation: впд - проводился этап впд, вфс - проводился этап вфс, п - не проводился ни впд, ни вфс

        # index_list - массив, в котором хранятся отрицательные индексы (по порядку): начало вфс, конец вфс (и возможно
        # начало впд), конец впд, если данный этап проводился. Если проводился только этап вфс - длина спика 2 элемента,
        # если не проводился ни вфс, ни впд, то длина 0

        # Результаты опыта
        # Средний Коэффициент скемптона, найденный 3 способами (см.описание к класса)
        self._test_result = AttrDict({'scempton': None, "delta_h_reconsolidation": None})

    def set_test_data(self, test_data):
        """Функция принимает словарь, считанный с файла прибора или поднный напрямую, записывает в self._test_data,
        и запускает процесс определения коэффициента Скемптона"""
        self._reset_data()
        self._test_data.action = test_data["action"]
        self._test_data.pore_pressure = test_data["pore_pressure"]
        self._test_data.cell_pressure = test_data["cell_pressure"]
        self._test_data.time = test_data["time"]
        self._test_data.trajectory = test_data["trajectory"]

        self._test_result.scempton = None
        self._test_processing()

    def get_test_results(self):
        """
        Возвращает Коэффициент Скемптона на последнем этапе нагружения
        :return: Коэффициент Скемптона на последнем этапе нагружения
        """
        return self._test_result.get_dict()

    def get_plot_data(self):
        """Получение данных для построения графиков"""
        if self._test_result.scempton:
            return {"pore_pressure": self._test_data.pore_pressure,
                    "cell_pressure": self._test_data.cell_pressure
                    }
        else:
            return None

    def plotter(self, save_path=None):
        """Построитель опыта"""
        from matplotlib import rcParams
        rcParams['font.family'] = 'Times New Roman'
        rcParams['font.size'] = '10'
        rcParams['axes.edgecolor'] = 'black'

        plots = self.get_plot_data()
        res = self.get_test_results()

        if plots:

            figure = plt.figure(figsize=[6, 6])
            figure.subplots_adjust(right=0.98, top=0.98, bottom=0.1, wspace=0.25, hspace=0.25, left=0.1)

            ax = figure.add_subplot(1, 1, 1)
            ax.grid(axis='both')
            ax.set_xlabel("Давление в камере, кПа")
            ax.set_ylabel("Поровое давление, кПа")

            ax.plot(plots["cell_pressure"], plots["pore_pressure"], **plotter_params["main_line"])

            ax.plot([], [], label="Scempton ratio = " + str(res["scempton"]),
                    color="#eeeeee")
            ax.legend()

            if save_path:
                try:
                    plt.savefig(save_path, format="png")
                except:
                    pass

    def process_dict(self):
        """Определение flag_reconsolidation и index_list"""
        self._test_data.flag_reconsolidation = None
        self._test_data.index_list = []
        for index_begin_vfs in range(len(self._test_data.time)):
            if self._test_data.trajectory[index_begin_vfs] in ['RPSReconsolidation', 'ReconsolidationWoDrain']:
                self._test_data.index_list.append(index_begin_vfs)
                break
        if index_begin_vfs != len(self._test_data.time) - 1:
            for index_end_vfs in range(index_begin_vfs + 1, len(self._test_data.time)):
                if self._test_data.trajectory[index_end_vfs] not in ['RPSReconsolidation',
                                                                     'ReconsolidationWoDrain']:
                    self._test_data.index_list.append(index_end_vfs)
                    break
            else:
                self._test_data.index_list.append(index_end_vfs)

            if index_end_vfs != len(self._test_data.time) - 1 and \
                    self._test_data.trajectory[index_end_vfs] == 'MoisturingBackPressure':
                for index_end_vpd in range(index_end_vfs + 1, len(self._test_data.time)):
                    if self._test_data.trajectory[index_end_vpd] != 'MoisturingBackPressure':
                        self._test_data.flag_reconsolidation = 'впд'
                        self._test_data.index_list.append(index_end_vpd - 1)
                        break
                else:
                    self._test_data.flag_reconsolidation = 'впд'
                    self._test_data.index_list.append(index_end_vpd)
            else:
                self._test_data.flag_reconsolidation = 'вфс'
        else:
            self._test_data.flag_reconsolidation = 'п'
        if self._test_data.flag_reconsolidation == 'впд':
            if self._test_data.cell_pressure[index_end_vpd] - self._test_data.cell_pressure[index_end_vfs] < 25:
                self._test_data.flag_reconsolidation = 'вфс'
        if self._test_data.flag_reconsolidation == 'вфс':
            if self._test_data.cell_pressure[index_end_vfs] - self._test_data.cell_pressure[
                index_begin_vfs] < 25:
                self._test_data.flag_reconsolidation = 'п'

    def _test_processing(self):
        """Обработка результатов опыта"""
        # В данном методе пределяется, проводился ли этап вфс и/или впд (flag_reconsolidation и index_list)
        self.process_dict()
        if (self._test_data.flag_reconsolidation in ['впд', 'вфс']) and (np.mean(self._test_data.pore_pressure) >= 5):
            # Расчет коэффициента Скемптона
            scempton = ModelTriaxialReconsolidation.define_skemton_end(
                self._test_data.cell_pressure,
                self._test_data.pore_pressure,
                self._test_data.action)

            self._test_result.scempton = scempton['mean']
        else:
            print('Этап реконсолидации не проводился')

    @staticmethod
    def define_skemton_end(cell_press, pore_press, action):
        """ Универсальный модуль определения коэффициента Скемптона на последнем шаге нагружения.
         Универсальность достигается за счет следующих допущений:
         шагом нагружения считается последний шаг увеличения давления в камере - cell_press, этап противодавления
            таковым не является и будет пропущен.
         Этап с малым приращением давления в камере будет пропущен (малость определяется параметром delta_sigma)
         Участок последнего шага нагружения, на котором происходит убывание порового давления из рассмотрения
            исключается, так как считается не показательным или ошибочным

        Использует модуль curve_fit из бибилиотеки scipy.optimize
        :param cell_press:
        :param pore_press:
        :param action:
        :return: словарь из трех коэффициентов Скемптона, найденных различными способами:
            ['approx'] - угловой коэффициент лин. участка активного нагружения: self._intermediate_data.scempton,
            ['mean'] - средний (если определен, считаем наиболее точным), найденных по двум точкам (начальная и точек
                на участке,  где поровое давлие стабилизировалось)
            ['two_point'] - по двум точкам (начальной и конечно),
        и списка из трех справочных индексов (полезных для отображения на графике):
            index_begin_load - индекс с конца (отрицательный) начала увеличения давления в камере,
            index_end_load - индекс с конца (отрицательный) окончания увеличения давления в камере и начала стабилизации,
            index_end - индекс с конца (отрицательный) окончания шага нагружения
            ПРИМЕЧНАНИЕ. Если коэф.Скемптона определить не удалось, ему присваивается значение 0
        """
        # Доля от шага увеличения порового давления, при кот. считаем его стабилизировавшимся
        procent = 0.95
        # При каком увеличении давления в камере будем считать полноценным шагом
        delta_sigma = 15  # (меньше 5 не ставить! из-за этапа противодавления)
        # Сколько цифр после запятой сохранять в коэф.Скемптона
        num_round = 2

        def line_approximate(x, y):
            def func(x, k, b):
                return k * x + b

            popt, pcov = curve_fit(func, x, y, method="dogbox")
            return popt[0]

        # Определение индексов начала (index_begin_load<0) и конца (index_end<0) шага нагружения (со стабилизацией)

        index_end = -1
        for index_begin_load in range(-1, -len(action), -1):
            if action[index_begin_load] == 'LoadStage' and action[index_begin_load - 1] in ['Wait', 'Stabilization']:
                break
        while abs(cell_press[index_end] - cell_press[index_begin_load]) < delta_sigma:
            index_end = index_begin_load
            if index_end != -len(action) + 1:
                for index_begin_load in range(index_end - 1, -len(action), -1):
                    if action[index_begin_load] == 'LoadStage' and action[index_begin_load - 1] in ['Wait',
                                                                                                    'Stabilization']:
                        break
            else:
                break

        # Определение индекса (index_end_load<0) конца этапа активного нагружения на выбранном шаге

        for index_end_load in range(index_begin_load, index_end, 1):
            if action[index_end_load] == 'LoadStage' and action[index_end_load + 1] in ['Wait', 'Stabilization']:
                break
        else:
            index_end_load = index_begin_load

        # Определение индекса (index_proc<0) при котором значение порового давления стабилизировалось
        for index_proc in range(index_end_load, index_end, 1):
            if pore_press[index_proc] - pore_press[index_begin_load] > \
                    procent * (pore_press[index_end] - pore_press[index_begin_load]):
                break
        else:
            index_proc = index_end_load

        # Предотвращение учета падения порового давления (т.к. как правило это недостоверные или непоказательные данные)

        index_reduce_pore_press = index_end - 1
        while index_reduce_pore_press > index_end_load:
            index_reduce_pore_press = index_reduce_pore_press - 1
            if pore_press[index_end] - pore_press[index_reduce_pore_press] < -5:
                index_end = index_reduce_pore_press

        # Линейная аппроксимация этапа активного нагружения на выбранном шаге

        list_for_approxim_cell = [cell_press[index_begin_load]]
        list_for_approxim_pore = [pore_press[index_begin_load]]

        for index in range(index_begin_load + 1, index_end_load + 1):
            list_for_approxim_cell.append(cell_press[index])
            list_for_approxim_pore.append(pore_press[index])
        if len(list_for_approxim_cell) > 2:
            try:
                skempton_approxim = line_approximate(list_for_approxim_cell, list_for_approxim_pore)
            except ValueError:
                skempton_approxim = 0
        else:
            skempton_approxim = 0

        # Средний Скемптон по урезанному диапазону

        list_skempton = []
        for index_current in range(index_proc, index_end + 1):
            try:
                list_skempton.append((pore_press[index_current] - pore_press[index_begin_load]) /
                                     (cell_press[index_current] - cell_press[index_begin_load]))
            except ZeroDivisionError:
                pass
        try:
            skempton_mean = sum(list_skempton) / len(list_skempton)
        except ZeroDivisionError:
            skempton_mean = 0

        # По двум крайним точкам

        try:
            skempton_twopoints = (pore_press[index_end] - pore_press[index_begin_load]) / \
                                 (cell_press[index_end] - cell_press[index_begin_load])
        except ZeroDivisionError:
            skempton_twopoints = 0

        # Запись итогового словаря

        skempton_dict = {'approx': min(round(skempton_approxim, num_round), 0.99),
                         'mean': min(round(skempton_mean, num_round), 0.99),
                         'two_point': min(round(skempton_twopoints, num_round), 0.99),
                         'index': [index_begin_load, index_end_load, index_end]}

        return skempton_dict


class ModelTriaxialReconsolidationSoilTest(ModelTriaxialReconsolidation):
    """
    Модель реконсолидации с определением коэффициента Скемтона на последнем этапе
    Способ запуска:
    object.set_test_params(sigma_ref) - запускает моделирование и расчет по бытовому давлению sigma_ref

    Получение результата - коэффициента скемптона:
    object.get_test_results()

    Получение результата - словаря с результатами реконсолидации:
    object.get_dict()

    Коэффициент Скемптона:
     найденный по двум точкам: self._intermediate_data.scempton['two_point'],
     угловой коэффициент лин. участка активного нагружения: self._intermediate_data.scempton['approx'],
     средний (он же в get_test_results()), найденных по двум точкам (начальная и точек на участке,
     где поровое давлие стабилизировалось): self._intermediate_data.scempton['mean']
    """

    def __init__(self):
        ModelTriaxialReconsolidation.__init__(self)

        self.params = AttrDict({"sigma_ref": None,
                                "param_for_b_test": None,
                                "skempton_initial": None,
                                "skempton_end": None})

    def set_test_params(self):
        """Записываются параметры для моделирования реконсолидации, запускается процессов моделирования эксперимента и
        нахождения коэффициента кемптона"""

        self.params.sigma_ref = statment[statment.current_test].mechanical_properties.sigma_3
        self.params.skempton_initial = statment[statment.current_test].physical_properties.skempton_initial
        self.params.skempton_end = np.random.uniform(0.96, 0.98)
        self.physical_properties = statment[statment.current_test].physical_properties

        if self.params.sigma_ref < 50:
            self.params.sigma_ref = 50

        if self.params.skempton_initial <= 0:
            self.params.skempton_initial = 0.4
        if self.params.skempton_initial >= 1:
            self.params.skempton_initial = 0.6

        if self.params.skempton_end <= 0.96:
            self.params.skempton_end = 0.96
        if self.params.skempton_end >= 1:
            self.params.skempton_end = 0.98

        # Получаешь self.params входные данные для моделирования входных данных эксперимента
        self._test_modeling()
        self._test_processing()

    def _test_modeling(self):
        """Получение модели результатов опыта"""
        self.params.param_for_b_test = ModelTriaxialReconsolidationSoilTest.define_input(self.params.sigma_ref,
                                                                                         self.params.skempton_initial,
                                                                                         self.params.skempton_end, u_vfs_end=75)

        self._test_data_all = ModelTriaxialReconsolidationSoilTest.create_b_test(self.params.param_for_b_test)
        self._test_data.pore_pressure = self._test_data_all['PorePress_kPa']
        self._test_data.cell_pressure = self._test_data_all['CellPress_kPa']
        self._test_data.action = self._test_data_all['Action']
        self._test_data.time = self._test_data_all['Time']
        self._test_data.trajectory = self._test_data_all["Trajectory"]

        # self._test_data_all['PorePress_kPa'][-1] = self._test_data_all['CellPress_kPa'][-1]

        self._test_result.delta_h_reconsolidation = self._test_data_all["VerticalDeformation_mm"][-1]

    def get_dict(self):
        """Выводит словарь (эксземпляр класса AttrDict) смоделированного этапа реконсолидации (вфс и впд) с заданным
        бытовым давлением"""
        return self._test_data_all

    def get_effective_stress_after_reconsolidation(self):
        return self._test_data_all['CellPress_kPa'][-1] - self._test_data_all['PorePress_kPa'][-1]

    def get_duration(self):
        return self._test_data.time[-1]

    @staticmethod
    def define_input(sigma_ref, skempton_initial=np.random.uniform(0.4, 0.6),
                     skempton_end=np.random.uniform(0.95, 0.98), u_vfs_end=0, flag_define_deformation=False):
        """
        Определяет входные параметры для моделирования реконсолидации create_b_test(input_dict)
        :param sigma_ref: Бытовое давление (устанавливаемое давление в камере в конце вфс) в кПа
        :param skempton_initial: Значение коэффициента Скемптона на первом шаге нагружения
        :param skempton_end: Значение коэффициента Скемптона на последнем шаге нагружения
        :param u_vfs_end: Поровое давление при бытовом давлении в конце этапа вфс в кПа
        :param flag_define_deformation: заданы ли начальная и конечная вертикальная деформация

        :return: input_dict - словарь, в котором записаны все необходимые для моделирования реконсолидации параметры
        """
        # Начальная и конечная вертикальная деформация
        initial_vertical_deformation = 0
        end_vertical_deformation = -0.2
        # Изменение объема в камере на последнем шаге
        cell_volume_end_step = 1000

        # Построение рисунков
        flag_plot = 0
        # время стаблизации каждого шага нагружения (увеличения давления в камере) в минутах
        t_stabil = 15
        # Диапазон времени стабилизации в минутах при противодавлении
        t_add_u = [2, 5]
        # шаг в секундах записи в файл
        time_step = 2
        # Шаг поднятия давления при этапе ВФС:   25 для грунтов мягкопластичной и текучей консистенции,
        #                                        50 для грунтов тугопластичной и пластичной консистеции
        #                                        от 100 до 200 для грунтов полутвердой и твердой консистенции
        sigma_VFS_step = 50
        # Шаг поднятия давления при этапе ВПД:   50 всегда
        sigma_VPD_step = 50

        # Шаг диксретизации датчика деформаций б/р
        discrete_step_deformation = 0.005
        # Шаг диксретизации датчик давления в камере в кПа
        discrete_step_press = 0.5
        # Шаг диксретизации датчика порового давления в кПа
        discrete_step_u = 0.5
        # Шаг диксретизации датчика изменения объема мм^3
        discrete_step_volume = 5
        # объемная деформация в конце этапа вфс
        epsilon_volume = 0.01
        # Плавность экспоненциального роста коэффициента Скемптона на этапе (пологая - 1...3, резкая - 10...20 )
        slant_skempton = np.random.uniform(1, 3)
        # Масимальное давление, которое выдерживает камера испытательной машины
        max_press_exp = 900
        # Доля от sigma_VFS_step и sigma_VPD_step, при которой происходит слияние промежуточной точки и финальной
        tolerance_merge_sigma = 0.25

        # В будущем возможно понадобиться
        # Диаметр образца 38 или 50 мм
        # sample_diameter = 38
        # Диаметр штока в мм
        # rod_diameter = 20
        # Высота образца
        # sample_height = 2 * sample_diameter
        # Площадь поперечного сечения образца в мм^2
        # sample_area = (np.pi * sample_diameter) ** 2 / 4
        # Площадь поперечного сечения штока в мм^2
        # rod_area = (np.pi * rod_diameter) ** 2 / 4

        # Определение, какое максимальное количество шагов впд возможно при заданном бытовом давлении
        max_count_step_vpd = int((max_press_exp - np.random.randint(1, 5) *
                                  sigma_VPD_step - sigma_ref) / sigma_VPD_step)

        if max_count_step_vpd > 1:
            if max_count_step_vpd == 2:
                # Этап впд может как проводиться, так и не провдиться
                # Давление в конце реконсолидации
                sigma_VPD_end = sigma_ref + np.random.randint(0, 2) * 2 * sigma_VPD_step
                # Скемптон при давлении залегания (бытовом давлении)
                skempton_ref = skempton_end - (sigma_VPD_end - sigma_ref) / sigma_VPD_step / 2 * np.random.uniform(0.1,
                                                                                                                   0.2)
            else:
                # Этап впд проводится
                sigma_VPD_end = sigma_ref + np.random.randint(2, max_count_step_vpd + 1) * sigma_VPD_step
                skempton_ref = skempton_initial + (
                        skempton_end - skempton_initial) * sigma_ref / sigma_VPD_end * np.random.uniform(0.8, 0.9)
        else:
            # Этап впд не проводится
            sigma_VPD_end = sigma_ref
            skempton_ref = skempton_end

        # Запись списков давления в камере и коэффициента скемтона на этапе ВФС

        sigma_steps = [x for x in range(0, int(sigma_ref), int(sigma_VFS_step))]
        if sigma_ref - sigma_steps[-1] <= tolerance_merge_sigma * sigma_VFS_step:
            sigma_steps[-1] = sigma_ref
        else:
            sigma_steps.append(sigma_ref)

        count_step_vfs = len(sigma_steps) - 1

        if u_vfs_end > 0:
            try:
                ratio_increase_skempton_vfs = 1.2
                skempton_ref = (u_vfs_end / sigma_VFS_step * (1 - ratio_increase_skempton_vfs) /
                                (1 - ratio_increase_skempton_vfs ** count_step_vfs))
                skempton_step = [skempton_ref * (ratio_increase_skempton_vfs ** x) for x in range(0, count_step_vfs)]
            except ZeroDivisionError:
                skempton_ref = u_vfs_end / sigma_ref
                skempton_step = [skempton_ref]
        else:
            skempton_step = list(create_stabil_exponent(np.array(sigma_steps[:-1]),
                                                        skempton_ref - skempton_initial, slant_skempton,
                                                        skempton_initial))

        # Запись списков давления в камере и коэффициента скемтона на этапе ВПД

        if sigma_ref < sigma_VPD_end < 300:
            sigma_VPD_end = 300

        if sigma_VPD_end > sigma_ref:
            sigma_steps_VPD = [x for x in
                               range(int(sigma_ref + sigma_VPD_step), int(sigma_VPD_end), int(sigma_VPD_step))]
            if len(sigma_steps_VPD) == 0:
                sigma_steps_VPD = [int(sigma_VPD_end)]

            if sigma_VPD_end - sigma_steps_VPD[-1] <= tolerance_merge_sigma * sigma_VPD_step:
                sigma_steps_VPD[-1] = sigma_VPD_end
            else:
                sigma_steps_VPD.append(sigma_VPD_end)

            sigma_steps.extend(sigma_steps_VPD)

            skempton_step_vpd = create_stabil_exponent(
                np.array(sigma_steps[count_step_vfs + 1:]) - sigma_steps[count_step_vfs],
                skempton_end - skempton_step[-1], slant_skempton,
                skempton_step[-1])
            skempton_step.extend(skempton_step_vpd)

        # _______________________Этап отладки
        if flag_plot == 1:
            pass
            """plot_any(sigma_steps[1:], skempton_step, name_x = "sigma", name_y = "pore_press",
                      name_file = 'skempton.jpg', path = os.getcwd())"""
        # _______________________

        if not flag_define_deformation:
            initial_vertical_deformation = - np.random.uniform(0.005, 0.3)
            end_vertical_deformation = - (
                    np.random.uniform(0, 3 * discrete_step_deformation) + initial_vertical_deformation)

        pore_press_slant = np.random.uniform(1, 5)

        input_dict = {
            'sigma_steps': sigma_steps,
            'skempton_step': skempton_step,
            't_stabil': t_stabil,
            't_add_u': t_add_u,
            'time_step': time_step,
            'sigma_ref': sigma_ref,
            'discrete_step_deformation': discrete_step_deformation,
            'discrete_step_press': discrete_step_press,
            'discrete_step_u': discrete_step_u,
            'discrete_step_volume': discrete_step_volume,
            'epsilon_volume': epsilon_volume,
            'cell_volume_end_step': cell_volume_end_step,
            'initial_vertical_deformation': initial_vertical_deformation,
            'end_vertical_deformation': end_vertical_deformation,
            'pore_press_slant': pore_press_slant
        }

        return input_dict

    @staticmethod
    def create_b_test(input_dict):
        """
        Функция строит зависимость порового давления от обжимающего при ВФС и ВПД
        ВФС - восстановление фазового состава (до бытового давления)
        ВПД - водонасыщение противодавлением
        Использует функции:
         create_stabil_exponent(x, amplituda, slant, y0=0), которая в свою очередь использует exponent(x, amplitude, slant),
         create_linear_step(x, amplituda, k, y0)
         array_discreate_noise(array, discreate_step, num_format), который использует discrete_array(array, n_step)

        Входные параметры, определяемые в функции define_input(sigma_ref)
        :param input_dict:
        ['sigma_ref'] - бытовое давление
        ['t_stabil'] - время стабилизации в минутах (при увеличении давления в камере), обычно 15
        ['t_add_u'] - Диапазон времени в минутах стабилизации при противодавлении
        ['time_step'] - шаг в секундах записи в файл
        ['sigma_steps'] - список шагов нагружения (давления в камере) размерности Nx1
        ['skempton_step'] - список изменения коэффициента Скемптона, соотв. спику шагов нагружения размерности N-1x1
        ['cell_volume_end_step'] - величина изменения объема в камере на последнем шаге нагружения
        ['initial_vertical_deformation'] - начальная осевая деформация
        ['end_vertical_deformation'] - конечная осевая деформация
        ['epsilon_volume'] - объемная деформация в конце этапа вфс
        ['discrete_step_deformation'] - шаг диксретизации датчика деформаций
        ['discrete_step_press'] - шаг диксретизации датчик давления в камере
        ['discrete_step_u'] - шаг диксретизации датчика порового давления
        ['discrete_step_volume'] - шаг диксретизации датчика изменения объема

        :return: dict  - словарь, в котором с заданным шагом по времени смоделирован этап реконсолидации для таких величин,
         как давление в камере, поровое давление, измененеие объема в камере и образце, вертикальная деформация,
         объемная деформация, диаметр и высота образца
        """

        fix_value = 0

        sigma_ref = input_dict['sigma_ref']
        t_stabil = input_dict['t_stabil']
        t_add_u = input_dict['t_add_u']
        time_step = input_dict['time_step']
        sigma_steps = input_dict['sigma_steps']
        skempton_step = input_dict['skempton_step']
        skempton_end = skempton_step[-1]
        cell_volume_end_step = input_dict['cell_volume_end_step']
        initial_vertical_deformation = input_dict['initial_vertical_deformation']
        end_vertical_deformation = input_dict['end_vertical_deformation']
        epsilon_volume = input_dict['epsilon_volume']
        pore_press_slant = input_dict['pore_press_slant']

        discrete_step_deformation = input_dict['discrete_step_deformation']
        discrete_step_press = input_dict['discrete_step_press']
        discrete_step_u = input_dict['discrete_step_u']
        discrete_step_volume = input_dict['discrete_step_volume']

        dict_accum = {'time': list([float(0.1)]),
                      'action_accum': ['Start'],
                      'action_changed_accum': ['True'],
                      'u_accum': list([0]),
                      'sigma_accum': list([0]),
                      'cell_volume_accum': list([0]),
                      'pore_volume_accum': list([0]),
                      'index_end_step': [[0]]}

        def step_reconsolidation(_delta_initial, _dict_accum,
                                 t_step=time_step, sigma_VFS_end_=sigma_ref, fix_value_=fix_value,
                                 _pore_press_slant=pore_press_slant):

            k_sigma = np.random.uniform(0.5, 0.7)
            pore_volume_slant = np.random.uniform(5, 6)
            cell_volume_slant = np.random.uniform(10, 20)

            n_time = int(((_delta_initial['time']) * 60) // (t_step - 1))
            time_current = np.array([i * t_step for i in range(0, n_time)]).astype('float64')

            sigma_current = ModelTriaxialReconsolidationSoilTest.create_linear_step(time_current,
                                                                                    _delta_initial['press']['delta'],
                                                                                    k_sigma,
                                                                                    _delta_initial['press']['initial'])

            action_changed = ['' for __ in range(len(time_current))]
            action_changed[-1] = 'True'
            action = ['' for __ in range(len(time_current))]
            index_load = 0

            if _delta_initial['press']['delta'] == fix_value_:
                u_current = ModelTriaxialReconsolidationSoilTest.create_linear_step(time_current,
                                                                                    _delta_initial['u']['delta'][0],
                                                                                    _pore_press_slant,
                                                                                    _delta_initial['u']['initial'])

                while index_load + 1 < len(sigma_current) and\
                        time_current[index_load] < _delta_initial['press']['delta'] / _pore_press_slant:

                    action[index_load] = 'LoadStage'
                    index_load += 1
                else:
                    action_changed[index_load - 1] = 'True'
                    action[index_load:] = ['Stabilization' if sigma_current[-1] < sigma_VFS_end_ else
                                           'Wait' for x in range(index_load, len(action))]

            else:
                time_load = _delta_initial['press']['delta'] / k_sigma

                _pore_press_slant = _delta_initial['u']['delta'][0] / time_load

                for index_time_liner_u in range(len(time_current)):
                    if time_current[index_time_liner_u] > time_load:
                        break

                max_time = max(time_current[index_time_liner_u:] - time_load)
                slant_u = _pore_press_slant * max_time / (_delta_initial['u']['delta'][1] - _pore_press_slant * time_load)

                u_current = ModelTriaxialReconsolidationSoilTest.create_linear_step(time_current[:index_time_liner_u],
                                                                                    _pore_press_slant * time_load, _pore_press_slant,
                                                                                    _delta_initial['u']['initial'])

                u_current_add = create_stabil_exponent(time_current[index_time_liner_u:] - time_load,
                                                       _delta_initial['u']['delta'][1] - _pore_press_slant * time_load, slant_u,
                                                       u_current[-1])

                u_current.extend(u_current_add)

                while index_load + 1 < len(u_current) and time_current[index_load] < time_load:
                    action[index_load] = 'LoadStage'
                    index_load += 1
                else:
                    action_changed[index_load - 1] = 'True'
                    action[index_load:] = ['Wait' for __ in range(index_load, len(action))]

            pore_volume_current = create_stabil_exponent(time_current, _delta_initial['v_pore']['delta'],
                                                         pore_volume_slant, 0)

            cell_volume_current = create_stabil_exponent(time_current, _delta_initial['v_cell']['delta'],
                                                         cell_volume_slant, _delta_initial['v_cell']['initial'])
            cell_volume_current = cell_volume_current - pore_volume_current

            pore_volume_current += _delta_initial['v_pore']['initial']
            time_current += _dict_accum['time'][-1]

            dict_current = {'time': time_current,
                            'action_accum': action,
                            'action_changed_accum': action_changed,
                            'u_accum': u_current,
                            'sigma_accum': sigma_current,
                            'cell_volume_accum': cell_volume_current,
                            'pore_volume_accum': pore_volume_current,
                            'index_end_step': [[len(time_current) + _dict_accum['index_end_step'][-1][0]]]}

            for key_ in _dict_accum:
                _dict_accum[key_].extend(dict_current[key_])
                # new_dict[key] = _dict_accum[key].extend(dict_current[key])

            return _dict_accum

        # Основной цикл по всем этапам нагружения
        for i_sigma, press_current in enumerate(sigma_steps[1:]):

            sigma_previous = dict_accum['sigma_accum'][-1]
            u_previos = dict_accum['u_accum'][-1]
            delta_sigma = press_current - sigma_previous
            # slant_sigma = np.random.uniform(10, 20)

            delta_initial = {'time': t_stabil + np.random.uniform(0, 1),
                             'press': {'delta': press_current - sigma_previous,
                                       'initial': sigma_previous},
                             'u': {'delta': [(delta_sigma) * skempton_step[i_sigma] ** 2 / skempton_end - 0.001,
                                             (delta_sigma) * skempton_step[i_sigma]],
                                   'initial': u_previos},
                             'v_pore': {'delta': fix_value,
                                        'initial': dict_accum['pore_volume_accum'][-1]},
                             'v_cell': {'delta': cell_volume_end_step / skempton_step[i_sigma],
                                        'initial': dict_accum['cell_volume_accum'][-1]}}

            dict_accum = step_reconsolidation(delta_initial, dict_accum)

            if press_current <= sigma_ref:
                dict_accum['index_end_step'][-1].append('вфс')
            else:
                dict_accum['index_end_step'][-1].append('впд_камера')

            if press_current > sigma_ref and skempton_step[i_sigma] < 0.99 * skempton_end:

                delta_initial = {'time': np.random.uniform(t_add_u[0], t_add_u[1]),
                                 'press': {'delta': fix_value,
                                           'initial': dict_accum['sigma_accum'][-1]},
                                 'u': {'delta': [u_previos + delta_sigma - dict_accum['u_accum'][-1], 0],
                                       'initial': dict_accum['u_accum'][-1]},
                                 'v_pore': {'delta': cell_volume_end_step / skempton_step[i_sigma] / 10,
                                            'initial': dict_accum['pore_volume_accum'][-1] -
                                                       cell_volume_end_step / skempton_step[i_sigma] / 40},
                                 'v_cell': {'delta': fix_value,
                                            'initial': dict_accum['cell_volume_accum'][-1]}}
                dict_accum = step_reconsolidation(delta_initial, dict_accum)
                dict_accum['index_end_step'][-1].append('впд_образец')


        for index_j_step_end_vfs, indexes_step in enumerate(dict_accum['index_end_step'][1:]):
            if indexes_step[1] == 'впд_камера':
                index_step_end_vfs = dict_accum['index_end_step'][index_j_step_end_vfs - 1][0] - 1
                break
        else:
            index_step_end_vfs = len(dict_accum['time'])

        trajectory_accum = ['RPSReconsolidation' if x <= index_step_end_vfs else 'MoisturingBackPressure' \
                            for x in range(0, len(dict_accum['time']))]

        # trajectory_accum = ['RPSReconsolidation' if dict_accum['sigma_accum'][x] < sigma_ref else 'MoisturingBackPressure'\
        #                    for x in range(0, len(dict_accum['time']))]
        trajectory_accum[0] = 'HC'

        try:
            index_start_vfs = trajectory_accum.index('MoisturingBackPressure')

            vertical_deformation = create_stabil_exponent(np.array(dict_accum['time'][0:index_start_vfs]),
                                                          end_vertical_deformation - initial_vertical_deformation,
                                                          10) + initial_vertical_deformation

            vertical_deformation_vfs = create_stabil_exponent(np.array(dict_accum['time'][index_start_vfs:]),
                                                              -epsilon_volume / 3, 1) + vertical_deformation[-1]

            vertical_deformation = np.hstack((vertical_deformation, vertical_deformation_vfs))

        except ValueError:
            vertical_deformation = create_stabil_exponent(np.array(dict_accum['time']),
                                                          end_vertical_deformation - initial_vertical_deformation,
                                                          10) + initial_vertical_deformation

        dict = {
            'Time': [float("{:.3f}".format(x / 60)) for x in
                     (dict_accum['time'] + np.random.uniform(-0.1, 0.1, len(dict_accum['time'])))],
            'Action': dict_accum['action_accum'],
            'Action_Changed': dict_accum['action_changed_accum'],
            'SampleHeight_mm': np.full(len(dict_accum['time']), 76),
            'SampleDiameter_mm': np.full(len(dict_accum['time']), 38),
            'Deviator_kPa': [int("{:.0f}".format(x)) for x in np.zeros(len(dict_accum['time']))],
            'VerticalDeformation_mm': array_discreate_noise(vertical_deformation, discrete_step_deformation, 8),
            'CellPress_kPa': array_discreate_noise(dict_accum['sigma_accum'], discrete_step_press, 5,
                                                   koef_noise_before=0.1),
            'CellVolume_mm3': array_discreate_noise(dict_accum['cell_volume_accum'], discrete_step_volume, 2),
            'PorePress_kPa': array_discreate_noise(dict_accum['u_accum'], discrete_step_u, 5, koef_noise_before=0.1),
            'PoreVolume_mm3': array_discreate_noise(dict_accum['pore_volume_accum'], discrete_step_volume, 3,
                                                    koef_noise_before=0.5),
            'VerticalPress_kPa': array_discreate_noise(dict_accum['sigma_accum'], discrete_step_press, 5),
            'Trajectory': trajectory_accum

            # 'skempton': skempton_step,
            # 'step_pressure': sigma_steps
        }

        for index in range(len(dict["Action_Changed"]) - 1):
            if dict["Action_Changed"][index] == 'True':
                for key in ['Time', 'CellPress_kPa', 'PorePress_kPa', 'VerticalPress_kPa', 'VerticalDeformation_mm',
                            'CellVolume_mm3', 'PoreVolume_mm3']:
                    dict[key][index + 1] = dict[key][index]

        return dict

    @staticmethod
    def create_linear_step(x, amplituda, k, y0):
        ''' Функция построение кусочно-линейной функции:
        наклонный участок, смещенный по оси Y на y0 с угловым коэффициентом k и растущим до значения y0+amplituda по оси Y,
        горизонтальный участок на всем остальном протяжении x

        :param x: Одномерный массив от нуля
        :param amplituda: Величина, на которую изменится искомая величина по закону прямой пропорциональности
        :param k: Угловой коэффициент прямой на первом участке
        :param y0: Начальное значение искомой величины

        :return: Одномерный нампаевский массив значений, изменяющихся от значения y0 на amplituda сначала по линейному
        закону с угловым коэффициентом k, а при достижении значения y0+amplituda перестающих изменяться (гориз.участок)
        '''
        x = np.array(x)
        if x[0] != 0:
            x -= x[0]
        try:
            i, = np.where(x * k >= amplituda)
            index_x = i[0]
            y = list(x[:index_x] * k)
            y_add = [amplituda for index in range(index_x, len(x))]
            y.extend(y_add)
            y2 = np.array(y) + y0

        except IndexError:
            y2 = list(x * k + y0)
        return y2


def time_series(x: np.ndarray) -> np.ndarray:
    """
    Возвращает массив целых чисел по размеру `x`: [0,1,2,...,len(`x`)-1]:
    """
    time = np.linspace(0, len(x) - 1, len(x))
    return time

if __name__ == '__main__':
    a = ModelTriaxialReconsolidationSoilTest()
    a.set_test_params(120, skempton_initial=0.87, skempton_end=0.97)
    a.plotter()
    plt.show()

    # data = a.get_plot_data()
    # plt.figure()
    # plt.plot(time_series(data["pore_pressure"]), data["pore_pressure"])
    # plt.show()


    # x = np.linspace(0, 100, 1000)
    # y = create_stabil_exponent(x, 10, 1, 0)
    # plt.figure()
    # plt.plot(x, y)
    # plt.show()

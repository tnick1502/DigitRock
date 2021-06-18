"""Модуль математических моделей девиаторного нагружения. Содержит модели:

    ModelTriaxialDeviatorLoading - модель обработчика данных опыта девиаторного нагружения.
    Принцип работы:
        Данные подаются в модель методом set_test_data(test_data) с определенными ключами. Функция открытия файла
        прибора openfile() находится в кдассе обработки triaxial_statick_loading
        Обработка опыта происходит с помощью метода _test_processing(). Метод change_borders() служит для обработки
        границ массивов, причем обрезанные части все равно записываются в файл прибора
        Метод plotter() позволяет вывести графики обработанного опыта
        Результаты получаются методом get_test_results()

    ModelTriaxialDeviatorLoadingSoilTest - модель математического моделирования данных опыта девиаторного нагружения.
    Наследует методы  _test_processing(), get_test_results(), plotter(), а также структуру данных из
    Принцип работы:
        Параметры опыта подаются в модель с помощью метода set_test_params().
        Метод get_params() Возвращает основные параметры отрисовки для последующей передачи на слайдеры
        Метод set_draw_params() устанавливает позьзовательские значения параметров отрисовки.
        Метод_test_modeling моделируют соотвествующие массивы опытных данных. Вызыванется при передачи пользовательских
         параметров отрисовки.."""

__version__ = 1

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline

from general.general_functions import sigmoida, make_increas, line_approximate, line, define_poissons_ratio, mirrow_element, \
    define_dilatancy, define_type_ground, AttrDict, find_line_area, interpolated_intercept, Point, point_to_xy, \
    array_discreate_noise, create_stabil_exponent, discrete_array, create_deviation_curve, define_qf, define_E50
from static_loading.deviator_loading_functions import curve
from configs.plot_params import plotter_params


class ModelTriaxialDeviatorLoading:
    """Модель обработки девиаторного нагружения

    Логика работы:
        - Данные принимаются в set_test_data(). значально все данные обнуляются методом _reset_data()

        - Производится выбор рабочей кривой объемной деформации. Если кривая Поровой отжатой жидкости писалась, то она
        становится рабочей, иначе кривая отжатой жидкости из камеры

        - Производится определение точки мертвого хода штока функцией cls.find_friction_step(). После чего позиция
        мертвого хода подается в метод change_borders(left, right). Далее метод _cut() обрезает массивы по левой и
        правой границе. Обработка производится для обрезанной части. Объемная деформация аппроксимируется методом
        self._approximate_volume_strain() полиномом 15 степени

        - Обработка опыта производится методом _test_processing. qf и E50 проводится функцией cls.define_E50_qf().
        Eur брабатывается функцией cls.define_Eur(). Коэффициент пуассона и дилатансия определяется функцией
        cls.define_poissons_dilatancy(). Угол дилатансии определяется как наклон в точке пика

        - Метод get_plot_data подготавливает данные для построения. Метод plotter позволяет построить графики с помощью
        matplotlib"""
    def __init__(self):
        self._reset_data()
        # Для передачи на радиобаттон значений ненулевых датчиков
        self.current_volume_strain = {"current": "pore_volume", "pore_volume": True, "cell_volume": True}
        self.plotter_params = {"main_line": {"width": 2.5, "color": None, "style": "-"},
                               "scatter_line": {"width": 20, "color": "sandybrown", "style": None},
                               "help_line": {"width": 1.5, "color": "red", "style": "-"},
                               "dotted_line": {"width": 1.5, "color": "red", "style": "--"}}

    def _reset_data(self):
        """Обнуление входных параметров и результатов для обработки нового опыта"""
        self._test_data = AttrDict({"strain": None,
                                    "deviator": None,

                                    "reload_points": None,

                                    "volume_strain": None,
                                    "volume_strain_approximate": None,

                                    "pore_volume_strain": None,
                                    "cell_volume_strain": None,

                                    "strain_cut": None,
                                    "volume_strain_cut": None,
                                    "deviator_cut": None,
                                    "reload_points_cut": None})

        self._test_params = AttrDict({"sigma_3": None, "u": None})

        # Положение для выделения опыта из общего массива
        self._test_cut_position = AttrDict({"left": None,
                                            "right": None})

        # Результаты опыта
        self._test_result = AttrDict({"E50": None,
                                      "Eur": None,
                                      "qf": None,
                                      "poissons_ratio": None,
                                      "dilatancy_angle": None})

    def set_test_data(self, test_data):
        """Получение и обработка массивов данных, считанных с файла прибора"""
        self._reset_data()
        if test_data:
            self._test_data.strain = test_data["strain"]
            self._test_data.deviator = test_data["deviator"]
            self._test_data.pore_volume_strain = test_data["pore_volume_strain"]
            self._test_data.cell_volume_strain = test_data["cell_volume_strain"]
            self._test_data.reload_points = test_data["reload_points"]

            self._test_params.sigma_3 = round((test_data["sigma_3"]), 3)
            self._test_params.u = round((test_data["u"]), 2)

            if np.mean(self._test_data.pore_volume_strain) != 0:
                self._test_data.volume_strain = self._test_data.pore_volume_strain
                self.current_volume_strain = {"current": "pore_volume", "pore_volume": True, "cell_volume": True}
            else:
                self._test_data.volume_strain = self._test_data.cell_volume_strain
                self.current_volume_strain = {"current": "cell_volume", "pore_volume": False, "cell_volume": True}

            step = ModelTriaxialDeviatorLoading.find_friction_step(self._test_data.strain, self._test_data.deviator)
            self.change_borders(step, len(self._test_data.strain))
        else:
            print("Этап девиаторноо нагружения не проводился")

    def choise_volume_strain(self, volume_strain):
        """Выбор данных с порового валюмометра или волюмометра с камеры для последующей обработки"""
        if self._test_data.strain is not None:
            if volume_strain == "pore_volume":
                self._test_data.volume_strain = self._test_data.pore_volume_strain
                step = ModelTriaxialDeviatorLoading.find_friction_step(self._test_data.strain, self._test_data.deviator)
                self.change_borders(step, len(self._test_data.strain))
            else:
                self._test_data.volume_strain = self._test_data.cell_volume_strain
                step = ModelTriaxialDeviatorLoading.find_friction_step(self._test_data.strain, self._test_data.deviator)
                self.change_borders(step, len(self._test_data.strain))

    def get_current_volume_strain(self):
        """Метод возвращает действующий волюмометр
        При получении данных проверяется, какие волюмометры были активны. Приоритетный волюмометр выбирается как
         поровый, если в нем нет данных, то выберется камеры"""
        return self.current_volume_strain

    def change_borders(self, left, right):
        """Выделение границ для обрезки значений всего опыта"""
        self._test_cut_position.left = left
        self._test_cut_position.right = right
        self._cut()
        self._approximate_volume_strain()
        self._test_processing()

    def get_borders(self):
        """Метод вернет грацицы массивов после обработки"""
        return self._test_cut_position.get_dict()

    def get_test_results(self):
        """Получение результатов обработки опыта"""
        dict = self._test_result.get_dict()
        dict["sigma_3"] = round(self._test_params.get_dict()["sigma_3"]/1000, 2)
        dict["u"] = round(self._test_params.get_dict()["u"]/1000, 2)
        return dict

    def get_plot_data(self):
        """Получение данных для построения графиков"""
        if self._test_result.E50:
            E50 = point_to_xy(Point(x=0, y=0), Point(
                    x=0.9 * self._test_result.qf * 1000/ (self._test_result.E50*1000),
                    y=0.9 * self._test_result.qf * 1000))
        else:
            E50 = None

        if self._test_result.Eur:
            i_min = np.argmin(self._test_data.deviator_cut[self._test_data.reload_points_cut[0]:
                                                           self._test_data.reload_points_cut[1]]) +\
                    self._test_data.reload_points_cut[0]
            Eur = point_to_xy(Point(x=self._test_data.strain_cut[self._test_data.reload_points_cut[0]],
                                    y=self._test_data.deviator_cut[self._test_data.reload_points_cut[0]]),
                              Point(x=self._test_data.strain_cut[i_min],
                                    y=self._test_data.deviator_cut[i_min]))
        else:
            Eur = None

        if self._test_result.dilatancy_angle:
            dilatancy = {"x": self._test_result.dilatancy_angle[1],
                               "y": self._test_result.dilatancy_angle[2]}
        else:
            dilatancy = None

        return {"strain": self._test_data.strain_cut,
                "deviator": self._test_data.deviator_cut,
                "strain_cut": self._test_data.strain[0:self._test_cut_position.left] -
                              self._test_data.strain[self._test_cut_position.left],
                "deviator_cut": self._test_data.deviator[0:self._test_cut_position.left] -
                                self._test_data.deviator[self._test_cut_position.left],
                "volume_strain": self._test_data.volume_strain_cut,
                "volume_strain_approximate": self._test_data.volume_strain_approximate,
                "E50": E50,
                "Eur": Eur,
                "dilatancy": dilatancy}

    def check_none(self):
        if self._test_data.strain is None:
            return False
        else: return True

    def plotter(self, save_path=None):
        """Построитель опыта"""
        from matplotlib import rcParams
        rcParams['font.family'] = 'Times New Roman'
        rcParams['font.size'] = '12'
        rcParams['axes.edgecolor'] = 'black'

        figure = plt.figure(figsize = [9.3, 6])
        figure.subplots_adjust(right=0.98, top=0.98, bottom=0.1, wspace=0.25, hspace=0.25, left=0.1)

        ax_deviator = figure.add_subplot(2, 1, 1)
        ax_deviator.grid(axis='both')
        ax_deviator.set_xlabel("Относительная деформация $ε_1$, д.е.")
        ax_deviator.set_ylabel("Девиатор q, кПА")

        ax_volume_strain = figure.add_subplot(2, 1, 2)
        ax_volume_strain.grid(axis='both')
        ax_volume_strain.set_xlabel("Относительная деформация $ε_1$, д.е.")
        ax_volume_strain.set_ylabel("Объемная деформация $ε_v$, д.е.")

        plots = self.get_plot_data()
        res = self.get_test_results()

        if plots["strain"] is not None:
            ax_deviator.plot(plots["strain"], plots["deviator"], **plotter_params["main_line"])
            ax_deviator.plot(plots["strain_cut"], plots["deviator_cut"], **plotter_params["main_line"])
            if plots["E50"]:
                ax_deviator.plot(*plots["E50"], **plotter_params["sandybrown_dotted_line"])
            if plots["Eur"]:
                ax_deviator.plot(*plots["Eur"], **plotter_params["sandybrown_dotted_line"])

            ax_deviator.plot([], [], label="$E_{50}$" + ", MПа = " + str(res["E50"]), color="#eeeeee")
            ax_deviator.plot([], [], label="$q_{f}$" + ", MПа = " + str(res["qf"]), color="#eeeeee")
            if res["Eur"]:
                ax_deviator.plot([], [], label="$E_{ur}$" + ", MПа = " + str(res["Eur"]), color="#eeeeee")


            ax_volume_strain.plot(plots["strain"], plots["volume_strain"], **plotter_params["main_line"])
            ax_volume_strain.plot(plots["strain"], plots["volume_strain_approximate"], **plotter_params["dotted_line"])
            if plots["dilatancy"]:
                ax_volume_strain.plot(plots["dilatancy"]["x"], plots["dilatancy"]["y"], **plotter_params["dotted_line"])


            ax_volume_strain.plot([], [], label="Poissons ratio" + ", д.е. = " + str(res["poissons_ratio"]),
                                  color="#eeeeee")
            if res["dilatancy_angle"] is not None:
                ax_volume_strain.plot([], [], label="Dilatancy angle" + ", град. = " + str(res["dilatancy_angle"][0]),
                                      color="#eeeeee")

            ax_volume_strain.set_xlim(ax_deviator.get_xlim())

            ax_deviator.legend()
            ax_volume_strain.legend()

        if save_path:
            try:
                plt.savefig(save_path, format="png")
            except:
                pass

    def _approximate_volume_strain(self):
        """Аппроксимация объемной деформации для удобства обработки"""
        while True:
            try:
                self._test_data.volume_strain_approximate = np.polyval(
                    np.polyfit(self._test_data.strain_cut,
                               self._test_data.volume_strain_cut, 15),
                    self._test_data.strain_cut)
                break
            except:
                continue

    def _cut(self):
        """Создание новых обрезанных массивов"""
        self._test_data.strain_cut = self._test_data.strain[
                                     self._test_cut_position.left:self._test_cut_position.right] - \
                                     self._test_data.strain[self._test_cut_position.left]
        self._test_data.volume_strain_cut = self._test_data.volume_strain[
                                            self._test_cut_position.left:self._test_cut_position.right] - \
                                            self._test_data.volume_strain[self._test_cut_position.left]
        self._test_data.deviator_cut = self._test_data.deviator[
                                       self._test_cut_position.left:self._test_cut_position.right] - \
                                       self._test_data.deviator[self._test_cut_position.left]
        if self._test_data.reload_points:
            self._test_data.reload_points_cut = [self._test_data.reload_points[0] - self._test_cut_position.left,
                                                 self._test_data.reload_points[1] - self._test_cut_position.left]

    def _test_processing(self):
        """Обработка опыта девиаторного нагружения"""
        self._test_result.E50, self._test_result.qf = \
            ModelTriaxialDeviatorLoading.define_E50_qf(self._test_data.strain_cut, self._test_data.deviator_cut)

        self._test_result.Eur = \
            ModelTriaxialDeviatorLoading.define_Eur(self._test_data.strain_cut,
                                  self._test_data.deviator_cut, self._test_data.reload_points_cut)

        self._test_result.poissons_ratio,\
        self._test_result.dilatancy_angle =\
            ModelTriaxialDeviatorLoading.define_poissons_dilatancy(self._test_data.strain_cut,
                                  self._test_data.deviator_cut,
                                    self._test_data.volume_strain_approximate)

    @staticmethod
    def find_friction_step(strain, deviator):
        """Функция поиска начального хода штока"""
        try:
            i_less_then_5, = np.where(deviator<=5)
            strain0 = np.array(strain)
            strain, deviator = np.array(strain), np.array(deviator)

            strain, deviator = make_increas(np.array(strain), np.array(deviator))
            deviator, strain = make_increas(np.array(deviator), np.array(strain))

            if np.max(deviator)>200:
                i, = np.where(deviator>=70)
            else:
                i, = np.where(deviator >= np.max(deviator)*0.3)
            strain, deviator = strain[:i[0]], deviator[:i[0]]

            xxx = np.delete(np.hstack((strain, [strain[-1]])), [0])
            i, = np.where(strain0 >= strain[np.argmax(xxx-strain)+1] - 0.0003)

            if strain0[i[0]] >= 0.2:
                return 0
            else:
                return i[0] + 6
        except:
            return 0

    @staticmethod
    def define_E50_qf(strain, deviator):
        """Определение параметров qf и E50"""
        qf = np.max(deviator)
        # Найдем область E50
        imax, = np.where(deviator[:np.argmax(deviator)] > qf / 2)
        imin, = np.where(deviator[:np.argmax(deviator)] < qf / 2)
        imax = imax[0]
        imin = imin[-1]

        E50 = (qf / 2) / (
            np.interp(qf / 2, np.array([deviator[imin], deviator[imax]]), np.array([strain[imin], strain[imax]])))

        return round(E50 / 1000, 2), round(qf / 1000, 3)

    @staticmethod
    def define_Eur(strain, deviator, reload):
        """Поиск Eur"""
        # Проверяем, есть ли разгрзка и не отрезали ли ее
        if reload is not None:
            if len(reload) == 2 and reload[0] > 0 and reload != [0, 0]:
                try:
                    point1 = np.argmin(deviator[reload[0]: reload[1]]) + reload[0]  # минимум на разгрузке
                    point2 = reload[0]  # максимум на разгрузке

                    if (strain[point2] - strain[point1]) < 0.000001:
                        Eur = None
                    else:
                        Eur = round(((deviator[point2] - deviator[point1]) / (strain[point2] - strain[point1])) / 1000, 2)

                except ValueError:
                    Eur = None
            else:
                Eur = None

            return Eur
        else:
            return None

    @staticmethod
    def define_poissons_dilatancy(strain, deviator, volume_strain):
        # Коэффициент Пуассона и дилатансия
        qf = np.max(deviator)

        # Найдкм коэффициент пуассона
        strain25 = (np.interp(qf / 4, deviator, strain))
        index_02qf, = np.where(deviator >= 0.25 * qf)

        puasson = abs(((np.interp(strain25, strain, volume_strain)) + strain25) / (2 * - strain25))

        # Найдкм угол дилатансии
        i_top = np.argmax(deviator)

        if strain[i_top] >= 0.14:
            dilatancy = None
        else:

            scale = (max(volume_strain) - min(volume_strain)) / 5
            x_area = 0.003
            try:
                if x_area <= (strain[i_top + 1] - strain[i_top - 1]):
                    x_area = (strain[i_top + 2] - strain[i_top - 2])

                i_begin, = np.where(strain >= strain[i_top] - x_area)
                i_end, = np.where(strain >= strain[i_top] + x_area)
                x_dilatancy = strain[i_begin[0]:i_end[0]]
                y_dilatancy = volume_strain[i_begin[0]:i_end[0]]

                # p = np.polyfit(x_dilatancy, y_dilatancy, 1)
                # approx = np.polyval(p, x_dilatancy)
                # A1 = (approx[-1] - approx[0]) / (x_dilatancy[-1] - x_dilatancy[0])
                # B1 = np.polyval(p, 0)

                A1, B1 = line_approximate(x_dilatancy, y_dilatancy)
                B1 = volume_strain[i_top] - A1 * strain[i_top]

                dilatancy_begin, = np.where(line(A1, B1, strain) >= volume_strain[i_top] - scale)
                dilatancy_end, = np.where(line(A1, B1, strain) >= volume_strain[i_top] + scale)

                dilatancy = (
                    round(A1 * (180 / np.pi), 2), [strain[dilatancy_begin[0]], strain[dilatancy_end[0]]],
                    [line(A1, B1, strain[dilatancy_begin[0]]), line(A1, B1, strain[dilatancy_end[0]])])

            except IndexError:
                dilatancy = None

        return round(puasson, 2), dilatancy

class ModelTriaxialDeviatorLoadingSoilTest(ModelTriaxialDeviatorLoading):
    """Модель моделирования девиаторного нагружения
    Наследует обработчик и структуру данных из ModelTriaxialDeviatorLoading

    Логика работы:
        - Параметры опыта передаются в set_test_params(). Автоматически подпираются данные для отрисовки -
        self.draw_params. После чего параметры отрисовки можно считать методом get_draw_params()  передать на ползунки

        - Параметры опыта и данные отрисовки передаются в метод _test_modeling(), который моделирует кривые.

        - Метод set_draw_params(params) установливает параметры, считанные с позунков и производит отрисовку новых
         данных опыта"""
    def __init__(self):
        super().__init__()
        self._test_params = AttrDict({"qf": None,
                                      "sigma_3": None,
                                      "E50": None,
                                      "c": None,
                                      "fi": None,
                                      "data_phiz": None,
                                      "u": 0,
                                      "delta_h_consolidation": 0,
                                      "velocity": 1})

        self._draw_params = AttrDict({"fail_strain": None,
                                      "residual_strength_param": None,
                                      "residual_strength": None,
                                      "qocr": None,
                                      "poisson": None,
                                      "dilatancy": None})

    def set_test_params(self, test_params):
        """Установка основных параметров опыта"""
        self._test_params.qf = test_params.get("qf", None)
        self._test_params.sigma_3 = test_params.get("sigma_3", None)
        self._test_params.E50 = test_params.get("E", None)
        self._test_params.c = test_params.get("c", None)
        self._test_params.fi = test_params.get("fi", None)
        self._test_params.data_physical = test_params.get("data_phiz", None)

        xc, residual_strength = ModelTriaxialDeviatorLoadingSoilTest.define_xc_value_residual_strength(
            test_params["data_phiz"], test_params["sigma_3"],
            test_params["qf"], test_params["E"])

        self._draw_params.fail_strain = xc
        self._draw_params.residual_strength_param = \
            ModelTriaxialDeviatorLoadingSoilTest.residual_strength_param_from_xc(xc)
        self._draw_params.residual_strength = test_params["qf"]*residual_strength
        self._draw_params.qocr = 0

        self._draw_params.poisson = test_params.get("poisson")#,
                                                    #define_poissons_ratio("-", self._test_params.data_physical["Ip"],
                                                                          #self._test_params.data_physical["Il"],
                                                                          #self._test_params.data_physical["Ir"],
                                                                          #self._test_params.data_physical["10"],
                                                                          #self._test_params.data_physical["5"],
                                                                          #self._test_params.data_physical["2"]))
        self._draw_params.dilatancy = test_params.get("dilatancy")#, round((
                                                    #ModelTriaxialDeviatorLoadingSoilTest.define_dilatancy_from_xc_qres(
                                                    #xc,residual_strength) + define_dilatancy(
                                                    #self._test_params.data_physical,
                                                    #self._test_params.data_physical["rs"],
                                                    #self._test_params.data_physical["e"],
                                                    #round(self._test_params.qf + self._test_params.sigma_3, 1),
                                                    #self._test_params.sigma_3, self._test_params.fi,
                                                    #ModelTriaxialDeviatorLoadingSoilTest.define_OCR_from_xc(xc),
                                                                                 #self._test_params.data_physical["Ip"],
                                                                                # self._test_params.data_physical[
                                                                                     #"Ir"])) / 2, 2))
        self._test_modeling()

    def set_velocity_delta_h(self, velocity, delta_h_consolidation):
        """Передача в модель скорости нагружения и уменьшения образца на предыдущих этапах
        Скорость отвечает за количество точек на кривой девиатора и за время при сохранении словаря
        Перемещение отвечает за пересчет деформации для корретной обработки опыта после сохранения"""
        self._test_params.velocity = velocity
        self._test_params.delta_h_consolidation = delta_h_consolidation

    def get_dict(self):
        return ModelTriaxialDeviatorLoadingSoilTest.dictionary_deviator_loading(self._test_data.strain,
                                                                                self._test_data.deviator,
                                    self._test_data.pore_volume_strain, self._test_data.cell_volume_strain,
                                    self._test_data.reload_points, velocity=self._test_params.velocity,
                                    delta_h_consolidation = self._test_params.delta_h_consolidation)

    def get_draw_params(self):
        """Возвращает параметры отрисовки для установки на ползунки"""
        params = {"fail_strain": {"value": self._draw_params.fail_strain, "borders": [0.03, 0.15]},
                  "residual_strength_param": {"value": self._draw_params.residual_strength_param, "borders": [0.05, 0.6]},
                  "residual_strength": {"value": self._draw_params.residual_strength,
                                        "borders": [self._test_params.qf*0.5, self._test_params.qf]},
                  "qocr": {"value": self._draw_params.qocr, "borders": [0, self._test_params.qf]},
                  "poisson": {"value": self._draw_params.poisson, "borders": [0.25, 0.45]},
                  "dilatancy": {"value": self._draw_params.dilatancy, "borders": [0, 40]}}
        return params

    def set_draw_params(self, params):
        """Устанавливает переданные параметры отрисовки, считанные с ползунков, на модель"""
        self._draw_params.fail_strain = params["fail_strain"]
        self._draw_params.residual_strength_param = params["residual_strength_param"]
        self._draw_params.residual_strength = params["residual_strength"]
        self._draw_params.qocr = params["qocr"]
        self._draw_params.poisson = params["poisson"]
        self._draw_params.dilatancy = params["dilatancy"]

        self._test_modeling()

    def _test_modeling(self):
        """Функция моделирования опыта"""
        try:
            # Время проведения опыта
            max_time = int((0.15 * (76 - self._test_params.delta_h_consolidation))/self._test_params.velocity)

            if max_time<=500:
                max_time = 500


            if self._test_params.qf >= 150:
                self._test_data.strain, self._test_data.deviator, self._test_data.pore_volume_strain, \
                self._test_data.cell_volume_strain, self._test_data.reload_points, begin = curve(self._test_params.qf, self._test_params.E50, xc=self._draw_params.fail_strain,
                                                                    x2=self._draw_params.residual_strength_param,
                                                                    qf2=self._draw_params.residual_strength,
                                                                    qocr=self._draw_params.qocr,
                                                                    m_given=self._draw_params.poisson,
                                                                    amount_points=max_time,
                                                                    angle_of_dilatacy=self._draw_params.dilatancy)

                self._test_data.deviator = np.round(self._test_data.deviator, 3)
                self._test_data.strain = np.round(
                    self._test_data.strain * (76 - self._test_params.delta_h_consolidation)/ (
                                                     76 - self._test_params.delta_h_consolidation), 6)

                self._test_data.pore_volume_strain = np.round((self._test_data.pore_volume_strain * np.pi * 19 ** 2 * (
                            76 - self._test_params.delta_h_consolidation)) / (np.pi * 19 ** 2 * (
                            76 - self._test_params.delta_h_consolidation)), 6)
                self._test_data.cell_volume_strain = np.round((self._test_data.cell_volume_strain * np.pi * 19 ** 2 * (
                            76 - self._test_params.delta_h_consolidation)) / (np.pi * 19 ** 2 * (
                            76 - self._test_params.delta_h_consolidation)), 6)


            else:
                k = 250/self._test_params.qf
                self._test_data.strain, self._test_data.deviator, self._test_data.pore_volume_strain, \
                self._test_data.cell_volume_strain, self._test_data.reload_points, begin = curve(self._test_params.qf*k,
                                                self._test_params.E50*k,
                                                xc=self._draw_params.fail_strain,
                                                x2=self._draw_params.residual_strength_param,
                                                qf2=self._draw_params.residual_strength*k,
                                                qocr=self._draw_params.qocr,
                                                m_given=self._draw_params.poisson,
                                                amount_points=max_time,
                                                angle_of_dilatacy=self._draw_params.dilatancy)
                self._test_data.deviator /= 5

            # Действия для того, чтобы полученный массив данных записывался в словарь для последующей обработки
            k = np.max(np.round(self._test_data.deviator[begin:] - self._test_data.deviator[begin], 3)) / self._test_params.qf
            self._test_data.deviator = np.round(self._test_data.deviator/k, 3)

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

            #i_end, = np.where(self._test_data.strain > self._draw_params.fail_strain + np.random.uniform(0.03, 0.04))
            #if len(i_end):
                #self.change_borders(begin, i_end[0])
            #else:
            self.change_borders(begin, len(self._test_data.volume_strain))
        except (ValueError, IndexError, TypeError, RuntimeError) as err:
            print(err)

    @staticmethod
    def define_k_q(il, e0, sigma3):
        """ Функция определяет насколько выраженный пик на диаграмме
        :param il: показатель текучести
        :param e0: пористость
        :param sigma3: обжимающее напряжение в кПа
        :return: отношение qr к qf
        """
        # Параметры, определяющие распределения
        # Для песков:

        if e0 == "-":
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

        if il == 0 or il == '-':  # Пески

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

    @staticmethod
    def xc_from_qf_e_if_is(data, sigma3mor, qf_, e50_):
        """Функция находит деформацию пика девиаорного нагружения в зависимости от qf и E50, если по параметрам материала
        пик есть, если нет, возвращает xc = 0.15. Обжимающее напряжение должно быть в кПа"""

        def f_zero(a):
            return 0 if a == '-' else a

        gran_struct = ['10', '5', '2', '1', '05', '025', '01', '005', '001', '0002', '0000']  # гран состав
        accumulate_gran = [f_zero(data[gran_struct[0]])]  # Накоплено процентное содержание
        for i in range(10):
            accumulate_gran.append(accumulate_gran[i] + f_zero(data[gran_struct[i + 1]]))

        # Определяем тип грунта
        type_ground = define_type_ground(data, data["Ip"], data["Ir"])

        # определяем степень плотности песка (если type_ground = 1...5)
        e0 = f_zero(data['e'])  # пористость
        if e0 == 0:
            dens_sand = 2  # средней плотности
        elif type_ground <= 3:
            if e0 <= 0.55:
                dens_sand = 1  # плотный
            elif e0 <= 0.7:
                dens_sand = 2  # средней плотности
            else:  # e0 > 0.7
                dens_sand = 3  # рыхлый
        elif type_ground == 4:
            if e0 <= 0.6:
                dens_sand = 1  # плотный
            elif e0 <= 0.75:
                dens_sand = 2  # средней плотности
            else:  # e0 > 0.75
                dens_sand = 3  # рыхлый
        elif type_ground == 5:
            if e0 <= 0.6:
                dens_sand = 1  # плотный
            elif e0 <= 0.8:
                dens_sand = 2  # средней плотности
            else:  # e0 > 0.8
                dens_sand = 3  # рыхлый
        else:
            dens_sand = 0

        sigma3mor = sigma3mor / 1000  # так как дается в КПа, а необходимо в МПа
        if accumulate_gran[1] > 50:  # Процентное содержание гранул размером 10 и 5 мм больше половины
            kr_fgs = 1
        elif f_zero(data['Ip']) == 0:  # число пластичности. Пески (и торф?)
            if dens_sand == 1 or type_ground == 1:  # любой плотный или гравелистый песок
                kr_fgs = 1
            elif type_ground == 2:  # крупный песок
                if sigma3mor <= 0.1:
                    kr_fgs = round(np.random.uniform(0, 1))
                else:
                    kr_fgs = 1
            elif type_ground == 3:  # песок средней групности
                if sigma3mor <= 0.15 and dens_sand == 3:  # песок средней крупности рыхлый
                    kr_fgs = 0
                elif sigma3mor <= 0.15 and dens_sand == 2:  # песок средней крупности средней плотности
                    kr_fgs = round(np.random.uniform(0, 1))
                else:  # песок средней групности и sigma3>0.15
                    kr_fgs = 1
            elif type_ground == 4:  # мелкий песок
                if sigma3mor < 0.1 and dens_sand == 3:  # мелкий песок рыхлый s3<0.1
                    kr_fgs = 0
                elif (0.1 <= sigma3mor <= 0.2 and dens_sand == 3) or (sigma3mor <= 0.15 and dens_sand == 2):
                    kr_fgs = round(np.random.uniform(0, 1))  # мелкий песок рыхлый s3<=0.2 и средней плотности s3<=0.15
                else:  # мелкий песок рыхлый s3>=0.2 и средней плотности s3>=0.15 (плотный закрыт раньше)
                    kr_fgs = 1
            elif type_ground == 5:  # песок пылеватый
                if sigma3mor < 0.1 and dens_sand == 3:  # песок пылеватый рыхлый s3<0.1
                    kr_fgs = 0
                elif (0.1 <= sigma3mor <= 0.2 and dens_sand == 3) or (
                        sigma3mor <= 0.1 and dens_sand == 2):  # песок пылева-
                    kr_fgs = round(
                        np.random.uniform(0, 1))  # тый рыхлый 0.1<=s3<=0.2 и пылеватый средней плотности s3<=0.1
                else:  # песок пылеватый рыхлый s3>0.2 и пылеватый средней плотности s3>0.1 (плотный закрыт раньше)
                    kr_fgs = 1
            elif type_ground == 9:  # Торф
                kr_fgs = 0
            else:
                kr_fgs = 0

        elif data['Ip'] <= 7:  # число пластичности. Супесь

            if f_zero(data['Il']) > 1:  # показатель текучести. больше 1 - текучий
                kr_fgs = 0
            elif 0 < f_zero(data['Il']) <= 1:  # показатель текучести. от 0 до 1 - пластичный (для супеси)
                kr_fgs = round(np.random.uniform(0, 1))
            else:  # <=0 твердый
                kr_fgs = 1

        elif data['Ip'] > 7:  # суглинок и глина
            if f_zero(
                    data[
                        'Il']) > 0.5:  # показатель текучести.от 0.5 мягко- и текучепласт., текучий (для суглинков и глины)
                kr_fgs = 0
            elif 0.25 < f_zero(data['Il']) <= 0.5:  # от 0.25 до 0.5 тугопластичный (для суглинков и глины)
                kr_fgs = round(np.random.uniform(0, 1))
            else:  # меньше 0.25 твердый и полутвердый (для суглинков и глины)
                kr_fgs = 1
        else:
            kr_fgs = 0

        return kr_fgs

    @staticmethod
    def define_xc_qf_E(qf, E50):
        """Функция определяет координату пика в зависимости от максимального девиатора и модуля"""
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

    @staticmethod
    def residual_strength_param_from_xc(xc):
        """Функция находит параметр падения остатичной прочности в зависимости от пика"""

        param = 0.33 - 1.9 * (0.15 - xc)

        return param

    @staticmethod
    def define_xc_value_residual_strength(data_phiz, sigma_3, qf, E):
        xc = ModelTriaxialDeviatorLoadingSoilTest.xc_from_qf_e_if_is(data_phiz, sigma_3, qf, E)
        if xc:
            xc = ModelTriaxialDeviatorLoadingSoilTest.define_xc_qf_E(qf, E)
        else:
            xc = 0.15

        if xc != 0.15:
            residual_strength = ModelTriaxialDeviatorLoadingSoilTest.define_k_q(data_phiz["Il"], data_phiz["e"], sigma_3)
        else:
            residual_strength = 0.95

        return xc, residual_strength

    @staticmethod
    def define_dilatancy_from_xc_qres(xc, qres):
        """Определяет угол дилатансии"""
        k_xc = sigmoida(mirrow_element(xc, 0.075), 5, 0.075, 5, 0.15)
        k_qres = sigmoida(mirrow_element(qres, 0.75), 5, 0.75, 5, 0.5)
        angle_of_dilatancy = k_xc + k_qres

        return round(angle_of_dilatancy, 1)

    @staticmethod
    def define_OCR_from_xc(xc):
        return 5.5 - 30 * xc

    @staticmethod
    def dictionary_deviator_loading(strain, deviator, pore_volume_strain, cell_volume_strain, indexs_loop, velocity=1,
                                    delta_h_consolidation=0):
        """Формирует словарь девиаторного нагружения"""

        index_unload, = np.where(strain >= strain[-1] * 0.92)  # индекс абциссы конца разгрузки
        x_unload_p = strain[index_unload[0]]  # деформация на конце разгрузки
        y_unload_p = - 0.05 * max(deviator)  # девиатор на конце разгрузки

        x_unload = np.linspace(strain[-1], x_unload_p, 8 + 1)  # массив деформаций разгрузки с другим шагом
        spl = make_interp_spline([x_unload_p, strain[-1]],
                                             [y_unload_p, deviator[-1]], k=3,
                                             bc_type=([(1, 0)], [(1, deviator[-1] * 200)]))
        y_unload = spl(x_unload)  # массив значений девиатора при разгрузке
        z_unload_p = min(pore_volume_strain) * 1.05  # обьемная деформация на конце разгрузки
        spl = make_interp_spline([x_unload_p, strain[-1]],
                                             [z_unload_p, pore_volume_strain[-1]], k=3,
                                             bc_type=([(1, 0)], [(1, abs(pore_volume_strain[-1] - z_unload_p) * 200)]))
        unload_pore_volume_strain = spl(x_unload)  # массив обьемных деформаций при разгрузке

        y_unload = y_unload + np.random.uniform(-1, 1, len(y_unload))  # наложение  шума на разгрузку
        y_unload = discrete_array(y_unload, 1)  # наложение ступенатого шума на разгрузку

        z_unload_p = min(cell_volume_strain) * 1.05
        spl = make_interp_spline([x_unload_p, strain[-1]],
                                             [z_unload_p, cell_volume_strain[-1]], k=3,
                                             bc_type=([(1, 0)], [(1, abs(cell_volume_strain[-1] - z_unload_p) * 200)]))
        unload_cell_volume_strain = spl(x_unload)

        # Расширяем массивы на разгрузку
        cell_volume_strain = np.hstack((cell_volume_strain, unload_cell_volume_strain[1:]))
        strain = np.hstack((strain, x_unload[1:]))
        deviator = np.hstack((deviator, y_unload[1:]))
        pore_volume_strain = np.hstack((pore_volume_strain, unload_pore_volume_strain[1:]))

        end_unload = len(strain) - len(x_unload) + 1  # индекс конца разгрузки в масииве

        # запись девиаторного нагружения в файл

        time = np.linspace(0, int((strain[-1] * (76 - delta_h_consolidation)) / velocity), len(strain))

        action = np.full(len(time), 'WaitLimit')

        if indexs_loop[0] != 0:
            for i in range(len(action)):
                if i >= indexs_loop[0] and i < indexs_loop[1]:
                    action[i] = 'CyclicUnloading'
                elif i >= indexs_loop[1] and i <= indexs_loop[2]:
                    action[i] = 'CyclicLoading'
                elif i >= end_unload:
                    action[i] = 'Unload'
        else:
            for i in range(len(action)):
                if i >= end_unload:
                    action[i] = 'Unload'

        action_changed = []
        Last_WaitLimit_flag = 1
        for i in range(len(action) - 1):
            if action[i] == "WaitLimit" and action[i + 1] == "Unload" and Last_WaitLimit_flag:
                action_changed.append('True' + '')
                Last_WaitLimit_flag = 0
            else:
                action_changed.append('')
        action_changed.append('')

        data = {
            "Time": time,
            "Action": action,
            "Action_Changed": action_changed,
            "SampleHeight_mm": np.round(np.full(len(time), 76)),
            "SampleDiameter_mm": np.round(np.full(len(time), 38)),
            "Deviator_kPa": np.round(deviator, 4),
            "VerticalDeformation_mm": strain * (76 - delta_h_consolidation),
            "CellPress_kPa": np.full(len(time), 0) + np.random.uniform(-0.1, 0.1, len(time)),
            "CellVolume_mm3": (cell_volume_strain * np.pi * 19 ** 2 * (76 - delta_h_consolidation)),
            "PorePress_kPa": np.full(len(time), 0) + np.random.uniform(-0.1, 0.1, len(time)),
            "PoreVolume_mm3": pore_volume_strain * np.pi * 19 ** 2 * (76 - delta_h_consolidation),
            "VerticalPress_kPa": deviator + np.random.uniform(-0.1, 0.1, len(time)),
            "Trajectory": np.full(len(time), 'CTC')}

        return data


if __name__ == '__main__':

    file = r"C:\Users\Пользователь\PycharmProjects\Willie\Test.1.log"
    file = r"Z:\МДГТ - Механика\3. Трехосные испытания\1365\Test\Test.1.log"
    param = {'E': 30495, 'sigma_3': 170, 'sigma_1': 800, 'c': 0.025, 'fi': 45, 'qf': 700, 'K0': 0.5,
             'Cv': 0.013, 'Ca': 0.001, 'poisson': 0.32, 'build_press': 500.0, 'pit_depth': 7.0, 'Eur': '-',
             'dilatancy': 4.95, 'OCR': 1, 'm': 0.61, 'lab_number': '7а-1', 'data_phiz': {'borehole': '7а',
                                                                                         'depth': 19.0,
                                                                                         'name': 'Песок крупный неоднородный',
                                                                                         'ige': '-', 'rs': 2.73,
                                                                                         'r': '-', 'rd': '-', 'n': '-',
                                                                                         'e': '-', 'W': 12.8, 'Sr': '-',
                                                                                         'Wl': '-', 'Wp': '-',
                                                                                         'Ip': '-', 'Il': '-',
                                                                                         'Ir': '-', 'str_index': '-',
                                                                                         'gw_depth': '-',
                                                                                         'build_press': 500.0,
                                                                                         'pit_depth': 7.0, '10': '-',
                                                                                         '5': '-', '2': 6.8, '1': 39.2,
                                                                                         '05': 28.0, '025': 9.2,
                                                                                         '01': 6.1, '005': 10.7,
                                                                                         '001': '-', '0002': '-',
                                                                                         '0000': '-', 'Nop': 7,
                                                                                         'flag': False},
             'test_type': 'Трёхосное сжатие (E)'}

    a = ModelTriaxialDeviatorLoadingSoilTest()
    a.set_test_params(param)
    a.plotter()
    plt.show()
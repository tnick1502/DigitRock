"""Модуль математических моделей резонансной колонки. Содержит модели:
    ModelRezonantColumn - модель обработчика данных опыта.
        Данные подаются в модель методом set_test_data(test_data) с определенными ключами.
        Обработка опыта происходит с помощью метода _test_processing()
        Метод plotter() позволяет вывести графики обработанного опыта
        Результаты получаются методом get_test_results()

    ModelTriaxialDynamicLoadingSoilTest - модель математического моделирования данных опыта. Наследует методы
    _test_processing(), get_test_results(), plotter(), а также структуру данных из ModelTriaxialCyclicLoading
        Параметры опыта подаются в модель с помощью метода set_test_params().
        Метод _define_draw_params() определяет основные характеристики отрисовки опыта.
        Метод get_params() Возвращает основные параметры отрисовки для последующей передачи на слайдеры
        Метод set_strain_params() и set_PPR_params() устанавливает позьзовательские значения параметров отрисовки.
        Методы _modeling_deviator(), _modeling_strain(), _modeling_PPR() моделируют соотвествующие массивы опытных
        данных. Вызываются при передачи пользовательских параметров отрисовки.
        Метод _test_modeling() содержит _modeling_deviator(), _modeling_strain(), _modeling_PPR(). Вызывается один раз
        для нахождения начальных параметров в методе set_test_params()."""

__version__ = 1

import numpy as np
import os
import warnings
import sys
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.optimize import differential_evolution

from general.general_functions import AttrDict
from cyclic_loading.cyclic_stress_ratio_function import define_fail_cycle
from configs.plot_params import plotter_params
from general.general_functions import read_json_file

plt.rcParams.update(read_json_file(os.getcwd()[:-15] + "/configs/rcParams.json"))
plt.style.use('bmh')

class ModelRezonantColumn:
    """Модель обработки циклического нагружения

    Логика работы:
        - Данные принимаются в set_test_data(). значально все данные обнуляются методом _reset_data()

        - Обработка опыта производится методом _test_processing.


        - Метод get_plot_data подготавливает данные для построения. Метод plotter позволяет построить графики с помощью
        matplotlib"""

    def __init__(self):
        """Определяем основную структуру данных"""
        # Структура дынных
        self._test_data = AttrDict({
            "shear_strain": None,
            "G_array": None,
            "frequency": None,
            "resonant_curves": None})

        # Положение для выделения опыта из общего массива
        self._test_cut_position = AttrDict({"left": None,
                                            "right": None})

        # Результаты опыта
        self._test_result = AttrDict({"G0": None, "threshold_shear_strain": None})

    def set_test_data(self, test_data):
        """Получение и обработка массивов данных, считанных с файла прибора"""
        self._test_data.shear_strain = test_data["shear_strain"]
        self._test_data.G_array = test_data["G0_array"]
        self._test_data.frequency = test_data["frequency"]
        self._test_data.resonant_curves = test_data["resonant_curves"]

        self._test_cut_position.left = 0
        self._test_cut_position.right = len(self._test_data.G_array)

        self._test_processing()

    def get_test_results(self):
        """Получение результатов обработки опыта"""
        return self._test_result.get_dict()

    def open_path(self, path):
        data = {}
        for dirpath, dirs, files in os.walk(path):
            for filename in files:
                if filename == "RCCT.txt":
                    data.update(
                        ModelRezonantColumn.open_resonant_curves_log(os.path.join(os.path.join(dirpath, filename))))
                elif filename == "RCCT_ModulusTable.txt":
                    data.update(ModelRezonantColumn.open_G0_log(os.path.join(os.path.join(dirpath, filename))))
        self.set_test_data(data)

    def get_plot_data(self):
        """Возвращает данные для построения"""
        if self._test_data.G_array is None:
            return None
        else:
            shear_strain_approximate = np.linspace(self._test_data.shear_strain[0],
                                                   self._test_data.shear_strain[-1], 300)

            G_approximate = ModelRezonantColumn.Hardin_Drnevick(shear_strain_approximate,
                                                                0.278/(0.722 *
                                                                       (self._test_result.threshold_shear_strain/10000)),
                                                                self._test_result.G0)
            return {
                "G": self._test_data.G_array,
                "shear_strain": self._test_data.shear_strain,
                "G_approximate": G_approximate,
                "shear_strain_approximate": shear_strain_approximate,
                "frequency": self._test_data.frequency,
                "resonant_curves": self._test_data.resonant_curves
            }

    def plotter(self, save_path=None):
        """Построение графиков опыта. Если передать параметр save_path, то графики сохраняться туда"""
        plot_data = self.get_plot_data()

        if plot_data:
            figure = plt.figure(figsize=[12, 5])
            figure.subplots_adjust(right=0.98, top=0.98, bottom=0.1, wspace=0.2, hspace=0.2, left=0.08)

            ax_G = figure.add_subplot(1, 2, 2)
            ax_G.set_xlabel("Деформация сдвига γ, д.е.")
            ax_G.set_xscale("log")
            ax_G.set_ylabel("Модуль сдвига G, МПа")

            ax_rezonant = figure.add_subplot(1, 2, 1)
            ax_rezonant.set_xlabel("Частота f, Гц")
            ax_rezonant.set_ylabel("Деформация сдвига γ, д.е.")

            ax_G.scatter(plot_data["shear_strain"], plot_data["G"], label="test data", color="tomato")
            ax_G.plot(plot_data["shear_strain_approximate"], plot_data["G_approximate"], label="approximate data")
            ax_G.legend()

            for i in range(len(plot_data["frequency"])):
                ax_rezonant.plot(plot_data["frequency"][i], plot_data["resonant_curves"][i])

            if save_path:
                try:
                    plt.savefig(save_path, format="png")
                except:
                    pass

            plt.show()

    def _test_processing(self):
        """Обработка опыта"""
        self._test_result.G0, self._test_result.threshold_shear_strain = \
            ModelRezonantColumn.approximate_Hardin_Drnevick(self._test_data.shear_strain[self._test_cut_position.left : self._test_cut_position.right],
                                                            self._test_data.G_array[self._test_cut_position.left : self._test_cut_position.right])

    @staticmethod
    def open_G0_log(file_path):

        test_data = {"shear_strain": np.array([]), "G0_array": np.array([])}

        columns_key = ['ShearStrain1[]', 'G1[MPa]']

        # Считываем файл
        f = open(file_path)
        lines = f.readlines()
        f.close()

        # Словарь считанных данных по ключам колонок
        read_data = {}

        for key in columns_key:  # по нужным столбцам
            index = (lines[0].split("; ").index(key))  #
            read_data[key] = np.array(list(map(lambda x: float(x.split("; ")[index]), lines[1:])))

        test_data["shear_strain"] = read_data['ShearStrain1[]']
        test_data["G0_array"] = read_data['G1[MPa]']

        return test_data

    @staticmethod
    def open_resonant_curves_log(file_path):

        test_data = {"frequency": np.array([]), "resonant_curves": np.array([])}

        columns_key = ['ShearStrain1[]', 'Freq', 'STEP_ID']

        # Считываем файл
        f = open(file_path)
        lines = f.readlines()
        f.close()

        # Словарь считанных данных по ключам колонок
        read_data = {}

        for key in columns_key:  # по нужным столбцам
            index = (lines[0].split("; ").index(key))  #
            read_data[key] = np.array(list(map(lambda x: float(x.split("; ")[index]), lines[1:])))

        id = len(set(read_data['STEP_ID']))
        test_data["resonant_curves"] = [list() for _ in range(id)]
        test_data["frequency"] = [list() for _ in range(id)]

        for i in range(id):
            if i == id - 1:
                i_1, = np.where(read_data['STEP_ID'] == i)
                test_data["resonant_curves"][i] = np.array(read_data['ShearStrain1[]'][i_1[0]:])
                test_data["frequency"][i] = np.array(read_data['Freq'][i_1[0]:])
            else:
                i_1, = np.where(read_data['STEP_ID'] == i)
                i_2, = np.where(read_data['STEP_ID'] == i + 1)
                test_data["resonant_curves"][i] = np.array(read_data['ShearStrain1[]'][i_1[0]:i_2[0]])
                test_data["frequency"][i] = np.array(read_data['Freq'][i_1[0]:i_2[0]])

        return test_data

    @staticmethod
    def Hardin_Drnevick(gam, a, G0):
        """Кривая Гардина - Дрневича"""
        return G0 / (1 + a * gam)

    @staticmethod
    def approximate_Hardin_Drnevick(x, y):

        def sumOfSquaredError(parameterTuple):
            warnings.filterwarnings("ignore")  # do not print warnings by genetic algorithm
            val = ModelRezonantColumn.Hardin_Drnevick(x, *parameterTuple)
            return np.sum((x - val) ** 2.0)

        def generate_Initial_Parameters():
            # min and max used for bounds
            maxX = np.max(x)
            minX = np.min(x)
            maxY = np.max(y)
            minY = np.min(y)

            parameterBounds = []
            parameterBounds.append([minX, maxX])  # search bounds for h
            parameterBounds.append([minY, maxY])
            result = differential_evolution(sumOfSquaredError, parameterBounds, seed=3)
            return result.x

        geneticParameters = generate_Initial_Parameters()

        popt, pcov = curve_fit(ModelRezonantColumn.Hardin_Drnevick, x, y, geneticParameters)

        aa, G = popt
        threshold_shear_strain = 0.278 / (aa * 0.722)

        return np.round(G, 2), np.round(threshold_shear_strain*10000, 2)




if __name__ == '__main__':

    #file = "C:/Users/Пользователь/Desktop/Тест/Циклическое трехосное нагружение/Архив/19-1/Косинусное значение напряжения.txt"
    file = "Z:/МДГТ - (Заказчики)/Инженерная Геология ООО (Аверин)/2021/332-21 Раменки/G0/Для отправки заказчику/1Х-1/RCCT.txt"
    m = ModelRezonantColumn()
    m.open_path(
        "Z:/МДГТ - (Заказчики)/Инженерная Геология ООО (Аверин)/2021/332-21 Раменки/G0/Для отправки заказчику/1Х-1")
    m.plotter()
    plt.show()
    #ModelRezonantColumn.open_resonant_curves_log(file)
    #file = "Z:/МДГТ - (Заказчики)/Инженерная Геология ООО (Аверин)/2021/332-21 Раменки/G0/Для отправки заказчику/1Х-1/RCCT_ModulusTable.txt"
    #ModelRezonantColumn.open_G0_log(file)
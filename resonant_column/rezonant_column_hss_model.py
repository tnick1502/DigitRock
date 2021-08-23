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
from resonant_column.rezonant_column_function import define_G0_threshold_shear_strain
from general.general_functions import read_json_file

try:
    plt.rcParams.update(read_json_file(os.getcwd() + "/configs/rcParams.json"))
except FileNotFoundError:
    plt.rcParams.update(read_json_file(os.getcwd()[:-15] + "/configs/rcParams.json"))

plt.style.use('bmh')

class ModelRezonantColumn:
    """Модель обработки резонансной колонки
    Логика работы:
        - Данные принимаются в set_test_data()

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

    def set_borders(self, left, right):
        """Выделение границ для обрезки значений всего опыта"""
        if (right - left) >= 3:
            self._test_cut_position.left = left
            self._test_cut_position.right = right
            self._test_processing()

    def get_plot_data(self):
        """Возвращает данные для построения"""
        if self._test_data.G_array is None:
            return None
        else:
            shear_strain_approximate = np.linspace(self._test_data.shear_strain[self._test_cut_position.left:
                                                                                self._test_cut_position.right][0],
                                                   self._test_data.shear_strain[self._test_cut_position.left
                                                                                :self._test_cut_position.right][-1],
                                                   300)

            G_approximate = ModelRezonantColumn.Hardin_Drnevick(shear_strain_approximate,
                                                                0.278/(0.722 *
                                                                       (self._test_result.threshold_shear_strain/10000)),
                                                                self._test_result.G0)
            return {
                "G": self._test_data.G_array[self._test_cut_position.left : self._test_cut_position.right],
                "shear_strain": self._test_data.shear_strain[self._test_cut_position.left : self._test_cut_position.right],
                "G_approximate": G_approximate,
                "shear_strain_approximate": shear_strain_approximate,
                "frequency": self._test_data.frequency[self._test_cut_position.left:
                                                                                self._test_cut_position.right],
                "resonant_curves": self._test_data.resonant_curves[self._test_cut_position.left:
                                                                                self._test_cut_position.right]
            }

    def plotter(self, save_path=None):
        """Построение графиков опыта. Если передать параметр save_path, то графики сохраняться туда"""
        plot_data = self.get_plot_data()
        res = self.get_test_results()

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

            ax_G.scatter([], [], label="$G_{0}$" + " = " + str(res["G0"]), color="#eeeeee")
            ax_G.scatter([], [], label="$γ_{0.7}$" + " = " + str(res["threshold_shear_strain"]) + " " +
                                       "$⋅10^{-4}$", color="#eeeeee")
            ax_G.legend()

            for i in range(len(plot_data["frequency"])):
                ax_rezonant.plot(plot_data["frequency"][i], plot_data["resonant_curves"][i])
                ax_rezonant.scatter(plot_data["frequency"][i], plot_data["resonant_curves"][i], s=10)

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

class ModelRezonantColumnSoilTest(ModelRezonantColumn):
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
        self._test_params = AttrDict({"p_ref": None,
                                      "K0": None,
                                      "E": None,
                                      "c": None,
                                      "fi": None,
                                      "physical": None,
                                      "G0": None,
                                      "threshold_shear_strain": None})
        self._getted_params = None

        # Коэффициенты отвечают за значение смоделированных результатов
        self._draw_params = AttrDict({"G0_ratio": 1,
                                      "threshold_shear_strain_ratio": 1,
                                      "frequency_step": 5})

    def set_test_params(self, params):
        """Функция принимает параметры опыта для дальнейших построений"""
        self._getted_params = params

        self._test_params.p_ref = params.reference_pressure
        self._test_params.c = params.c
        self._test_params.fi = params.fi
        self._test_params.E = params.E50
        self._test_params.K0 = params.K0
        self._test_params.physical = params.physical_properties
        self._test_params.G0 = params.G0
        self._test_params.threshold_shear_strain = params.threshold_shear_strain

        self._test_modeling()

    def get_test_params(self):
        return self._getted_params

    def set_draw_params(self, params):
        """Считывание параметров отрисовки(для передачи на слайдеры)"""
        self._draw_params.G0_ratio = params["G0_ratio"]
        self._draw_params.threshold_shear_strain_ratio = params["threshold_shear_strain_ratio"]
        self._draw_params.frequency_step = int(params["frequency_step"])
        self._test_modeling()

    def _test_modeling(self):
        """Моделирование данных опыта"""
        #G0, threshold_shear_strain = define_G0_threshold_shear_strain(self._test_params.p_ref,
                                                                      #self._test_params.physical,
                                                                      #self._test_params.E, self._test_params.c,
                                                                      #self._test_params.fi, self._test_params.K0)
        self._test_params.G0 *= self._draw_params.G0_ratio
        self._test_params.threshold_shear_strain *= self._draw_params.threshold_shear_strain_ratio

        self._test_data.G_array, self._test_data.shear_strain = \
            ModelRezonantColumnSoilTest.generate_G_array(self._test_params.G0, self._test_params.threshold_shear_strain)


        self._test_data.frequency, self._test_data.resonant_curves = \
            ModelRezonantColumnSoilTest.generate_resonant_curves(self._test_data.shear_strain, self._test_data.G_array,
                                                                 frequency_step=self._draw_params.frequency_step,
                                                                 ro=self._test_params.physical.r * 1000)
        self._test_processing()
        #self.plotter()
        #plt.plot(self._test_data.frequency[0], self._test_data.resonant_curves[0])

    def save_log_file(self, director):
        G = self._test_data.G_array
        points = self._test_data.shear_strain
        Chastota = self._test_data.frequency[0]
        A = self._test_data.resonant_curves

        p = os.path.join(director, "RCCT_ModulusTable.txt")
        p2 = os.path.join(director, "RCCT.txt")

        step = range(len(G))

        q = 1.586093674105024
        acur = [5]
        for i in range(100):
            x = acur[i]
            acur.append(x * q)

        with open(p, "w") as file:
            file.write(
                "STEP_ID; Frequency1; CURRENT[A]; ShearStrain1[]; G1[MPa]; Frequency2; CURRENT[A]; ShearStrain2[]; G2[MPa];" + '\n')
            for i in range(len(G)):
                file.write(str(step[i]) + '; ' + str(int(Chastota[i])) + '; ' + str(points[i] * 302) + '; ' + str(
                    points[i]) + '; ' + str(G[i]) + '; ' + str(int(Chastota[i])) + '; ' + str(
                    points[i] * 302) + '; ' + str(
                    (points[i] * (1 + np.random.uniform(0, 0.01)))) + '; ' + str(
                    (G[i] * (1 + np.random.uniform(0, 0.01)))) + '; ' + '\n')
        file.close()

        with open(p2, "w") as file:
            file.write(
                "STEP_ID; Freq; Acur_target; Adac; ACCELERATION1[m/s^2]; ACCELERATION2[m/s^2]; CURRENT[A]; Velocity1[m/s]; Displacement1[m]; ShearStrain1[]; Velocity2[m/s]; Displacement2[m]; ShearStrain2[]; ")
            for i in range(len(G)):
                for j in range(len(A[0])):
                    file.write(str(step[i]) + '; ' + str(int(Chastota[j])) + '; ' + str(acur[i]) + '; ' + str(
                        acur[i]) + '; ' + str((A[i][j] * 1300000 * (1 + np.random.uniform(0, 0.01)))) + '; ' + str(
                        A[i][j] * 1300000) + '; ' + str(points[i] * 302) + '; ' + str(A[i][j] * 200) + '; ' + str(
                        A[i][j] * 0.3) + '; ' + str(A[i][j]) + '; ' + str(
                        (A[i][j] * 200 * (1 + np.random.uniform(0, 0.01)))) + '; ' + str(
                        (A[i][j] * 0.3 * (1 + np.random.uniform(0, 0.01)))) + '; ' + str(
                        (A[i][j] * (1 + np.random.uniform(0, 0.01)))) + '; ' + '\n')

            file.close()

    @staticmethod
    def generate_G_array(G0, threshold_shear_strain, point_count=int(np.random.uniform(10, 15))):
        """Функция генерирует массив G0"""

        # Моделирование сдвиговых деформаций
        first_point = np.log((6 + 5 * np.random.uniform(0, 1)) * 10e-8)
        last_point = np.log(np.random.uniform(0.7 * 10e-4, 1.1 * 10e-4))
        shear_strain = np.linspace(first_point, last_point, point_count)
        shear_strain = np.e**(shear_strain)

        # Моделирование модуля
        G = ModelRezonantColumn.Hardin_Drnevick(shear_strain, 0.278 / (0.722 * threshold_shear_strain/10000), G0) \
            + np.random.uniform(-0.03 * G0, 0.03 * G0, np.size(shear_strain))

        # Значение не может быть больше предыдущего
        for k in range(len(G) - 1):
            if G[k + 1] > G[k]:
                G[k + 1] = G[k]

        return G, shear_strain

    @staticmethod
    def generate_resonant_curves(shear_strain, G, frequency_step=5, ro=2000):
        """Функция генерирует массив G0"""
        H = 0.1
        Io = 0.001374

        # Массив скоростей поперечных волн
        Vs_array = np.sqrt(G / ro)

        # Массив резонансных частот
        resonant_frequency_array = np.round((Vs_array / (H * (ro * H / (Vs_array * Io)) ** (-0.5))) / (4 * np.pi))

        # Массив частот испытания
        min_test_frequency = np.round(0.8 * np.min(resonant_frequency_array))
        max_test_frequency = np.round(1.1 * np.max(resonant_frequency_array)) + frequency_step
        frequency_array = np.arange(min_test_frequency - min_test_frequency % frequency_step,
                                    max_test_frequency - min_test_frequency % frequency_step, frequency_step)

        len_array = len(resonant_frequency_array)
        resonant_curves = [list() for _ in range(len_array)]
        frequency = [list() for _ in range(len_array)]

        for i in range(len_array):
            resonant_curves[i] = ModelRezonantColumnSoilTest.generate_resonant_curve(frequency_array,
                                                                                     resonant_frequency_array[i],
                                                                                     shear_strain[i])
            frequency[i] = frequency_array

        return frequency, resonant_curves

    @staticmethod
    def generate_resonant_curve(frequency, resonant_frequency, max_shear_strain):
        """Функция генерафии резонансной кривой"""
        max_shear_strain /= 10000

        alpha = -np.log(1/max_shear_strain)/(frequency[-1] - frequency[0])**2
        betta = alpha/5
        """alpha = -(10e-12/(max_shear_strain))*(frequency[-1] - frequency[0])#-0.005
        betta = alpha/5#10e12*  alpha*max_shear_strain#np.array([alpha/i for i in range(1, len(frequency) + 1)][::-1])"""

        i_resonance, = np.where(frequency>resonant_frequency)
        resonant_curve = np.hstack(((0.6 * np.exp(10 * alpha * (frequency[:i_resonance[0]] - resonant_frequency) ** 2) +
                          0.2 * np.exp(3*betta * (frequency[:i_resonance[0]] - resonant_frequency) ** 2)) * \
                         max_shear_strain + max_shear_strain*0.2,
                                    (0.4 * np.exp(alpha * (frequency[i_resonance[0]:] - resonant_frequency) ** 2) +
                                     0.4 * np.exp(betta * (frequency[i_resonance[0]:] - resonant_frequency) ** 2)) * \
                                    max_shear_strain + max_shear_strain * 0.2))
        #resonant_curve = (0.6 * np.exp(alpha * (frequency - resonant_frequency) ** 2) +
        # 0.2 * np.exp(betta * (frequency - resonant_frequency) ** 2)) * max_shear_strain + max_shear_strain * 0.2
        return resonant_curve




if __name__ == '__main__':
    #file = "C:/Users/Пользователь/Desktop/Тест/Циклическое трехосное нагружение/Архив/19-1/Косинусное значение напряжения.txt"
    #file = "Z:/МДГТ - (Заказчики)/Инженерная Геология ООО (Аверин)/2021/332-21 Раменки/G0/Для отправки заказчику/1Х-1/RCCT.txt"
    #m = ModelRezonantColumn()
    #m.open_path(
        #"Z:/МДГТ - (Заказчики)/Инженерная Геология ООО (Аверин)/2021/332-21 Раменки/G0/Для отправки заказчику/1Х-1")
    #m.plotter()
    #plt.show()
    #ModelRezonantColumnSoilTest.create_G_array(100, 4.34)

    #ModelRezonantColumnSoilTest.generate_resonant_curves(0, np.array([150 , 120 , 100]), ro=2000)
    data_physical = {"Ip": "-", "e": 0.3, "Ir": "-", "r": 2,
                     "10": "-", "5": "-", "2": "-", "1": "-", "05": "-", "025": 50, "01": 40, "005": "-", "001": "-",
                     "0002": "-", "0000": "-"}
    param = {"Pref": 0.5, "c": 0.001, "fi": 42, "E": 70, "K0": 1, "data_phiz": data_physical}
    a = ModelRezonantColumnSoilTest()
    a.set_test_params(param)
    plt.show()
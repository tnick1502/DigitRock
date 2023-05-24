import numpy as np
import matplotlib.pyplot as plt
import warnings
from scipy.optimize import curve_fit
from scipy.optimize import differential_evolution

plt.style.use('bmh')

def cyclic_stress_ratio_curve_params(Ip, Il=None, e=None )-> tuple:
    """Функция находит параметры (alpha, betta) кривой CSR для образца по физическим свойствам
    :argument
        Ip (float): Число пластичности
        Il (float): Показатель текучести
        e (float) : Коэффициент пористости
    :return
        (alpha, betta)"""

    if Ip:
        alpha = -0.0026 * Ip + 0.139
        betta = 0.0033 * Ip + 0.91
    else:
        alpha = 0.08
        betta = 0.7

    return (alpha, betta)

def define_cyclic_stress_ratio(cycle, alpha, betta)->float:
    """Функция Возвращает значения кривой CSR при заданном цикле
    :argument
        cycle (float): Цикл нагружения
        alpha, betta: Параметры кривой CSR
    :return
        CSR"""
    return betta - alpha*np.log(cycle)

def define_cycle(CSR, alpha, betta)->float:
    """Функция Возвращает значение цикла при заданном значении нагружения
    :argument
        CSR (float): Параметр нагружения CSR
        alpha, betta: Параметры кривой CSR
    :return
        cycle"""
    return np.e**((betta-CSR)/alpha)

def cyclic_stress_ratio_load(sigma_1, t)->float:
    """Функция находит параметр CSR из условий нагружения
    :argument
        sigma_1 (float): Эффективное вертикальное дафление консолидации
        t (float): Максимальные касательные напряжения (половина амплитуды девиатора)
    :return
        CSR"""
    return t/sigma_1

def define_fail_cycle(cycles_count, sigma_1, t, Ip, Il, e)->tuple:
    """Функция находит цикл разрушения, либо запас по прочности
    :argument
        cycles_count (int): Предполагаемое количество циклов нагружения (из условия опыта)
        sigma_1 (float): Эффективное вертикальное дафление консолидации
        t (float): Максимальные касательные напряжения (половина амплитуды девиатора)
        Ip (float): Число пластичности
        Il (float): Показатель текучести
        e (float) : Коэффициент пористости
    :return (n_fail, Mscr)
        n_fail - цикл разрушения. При отсутствии разрушения n_fail = None
        Mscr - запас просности. Рассчитывается как отношение ординат CSR аналитическое к CSR образца.
            В случае разрушения Mscr = None"""

    # Найдем аналитические параметры кривой SCR
    alpha, betta = cyclic_stress_ratio_curve_params(Ip, Il, e)

    # Определим SCR образца через условия нагрузки
    sample_CSR = cyclic_stress_ratio_load(sigma_1, t)

    # Определим SCR образца через аналитическую кривую
    analytical_SCR = define_cyclic_stress_ratio(cycles_count, alpha, betta)

    if sample_CSR >= analytical_SCR:

        fail_cycle = define_cycle(sample_CSR, alpha, betta)

        if fail_cycle >= 500:
            return (None, np.random.uniform(1.2, 1.6))
        else:
            return (int(fail_cycle), None)

    else:
        return (None, analytical_SCR/sample_CSR)

def approximate_test_data(cycles, CSR)->tuple:
    """Функция находит параметры (alpha, betta) кривой SCR для образца по данным испытаний
        :argument
            cycles: Массив циклов разрушения
            CSR: Массив значений CSR
        :return
            (alpha, betta)"""

    def sumOfSquaredError(parameterTuple):
        warnings.filterwarnings("ignore")  # do not print warnings by genetic algorithm
        val = define_cyclic_stress_ratio(cycles, *parameterTuple)
        return np.sum((cycles - val) ** 2.0)

    def generate_Initial_Parameters():
        # min and max used for bounds
        maxX = np.max(cycles)
        maxY = np.max(CSR)

        parameterBounds = []
        parameterBounds.append([0, 1])
        parameterBounds.append([0, 1])

        result = differential_evolution(sumOfSquaredError, parameterBounds, seed=3)
        return result.x, parameterBounds

    geneticParameters, bounds = generate_Initial_Parameters()
    popt, pcov = curve_fit(define_cyclic_stress_ratio, cycles, CSR, geneticParameters, method="dogbox", maxfev=5000)

    return popt

def plotter(alpha, betta, borders=(5, 1000), sample_CSR=None, sample_cycles=None,
            sample_CSR_array=None, sample_cycles_array=None, save_path=None) -> None:
    """Функция построения кривой CSR
        :argument
            alpha, betta: Параметры кривой CSR
            borders: границы построения
            sample_CSR, sample_cycles: значения для образца, Построитель поставит точку на графике и посчитает запас
            save_path: пусть сохранения файла. Если None, то не будет сохранять
        :return None"""

    from matplotlib import rcParams
    rcParams['font.family'] = 'Times New Roman'
    rcParams['font.size'] = '14'
    rcParams['axes.edgecolor'] = 'black'
    rcParams["axes.grid"] = True

    figure = plt.figure(figsize=[9.3, 6])
    figure.subplots_adjust(right=0.98, top=0.98, bottom=0.1, wspace=0.25, hspace=0.25, left=0.1)

    ax = figure.add_subplot(2, 1, 1)
    ax.set_xlabel("Число циклов N, ед.")
    ax.set_ylabel("Cyclic Stress Ratio, д.е.")

    ax_log = figure.add_subplot(2, 1, 2)
    ax_log.set_xlabel("Число циклов N, ед. (логарифмический масштаб)")
    ax_log.set_ylabel("Cyclic Stress Ratio, д.е.")
    ax_log.set_xscale("log")

    cycles = np.linspace(*borders, 1000)
    CSR = define_cyclic_stress_ratio(cycles, alpha, betta)

    ax.plot(cycles, CSR)
    ax_log.plot(cycles, CSR)

    ax.set_ylim([0, 1.2 * CSR[0]])
    ax_log.set_ylim([0, 1.2 * CSR[0]])

    if sample_CSR and sample_cycles:
        ax.scatter(sample_cycles, sample_CSR, color="tomato", label="Параметры нагрузки образца")
        ax_log.scatter(sample_cycles, sample_CSR, color="tomato", label="Параметры нагрузки образца")
        Mcsr = np.round(define_cyclic_stress_ratio(sample_cycles, alpha, betta)/sample_CSR, 3)
        ax.plot([], [], label="$M_{csr}$" + " = " + str(Mcsr), color="#eeeeee")
        ax_log.plot([], [], label="$M_{csr}$" + " = " + str(Mcsr), color="#eeeeee")
        ax.legend()
        ax_log.legend()

    if sample_CSR_array is not None and sample_cycles_array is not None:
        ax.scatter(sample_cycles_array, sample_CSR_array, color="sandybrown", label="Результаты опытов")
        ax_log.scatter(sample_cycles_array, sample_CSR_array, color="sandybrown", label="Результаты опытов")
        ax.legend()
        ax_log.legend()


    if save_path:
        try:
            plt.savefig(save_path, format="png")
        except:
            pass


if __name__ == '__main__':

    # Зададим параметры
    sigma_1 = 10
    t = 5
    Ip = 6
    Il = "-"
    e = "-"
    sample_cycles = 24

    # Найдем цикл разрушения/коэффиуциент запаса
    print(define_fail_cycle(sample_cycles, sigma_1, t, Ip, Il, e))

    # Построим кривые
    plotter(*cyclic_stress_ratio_curve_params(Ip), borders=(5, 1000),
            sample_CSR=cyclic_stress_ratio_load(sigma_1, t), sample_cycles=sample_cycles, save_path=None)
    plt.show()

    # Аппроксимируем опытные данные
    cycles = np.array([10, 27, 89, 276])
    CSR = define_cyclic_stress_ratio(cycles, 0.08, 0.7)

    alpha, betta = approximate_test_data(cycles, CSR)
    plotter(*cyclic_stress_ratio_curve_params(Ip), borders=(5, 400),
            sample_CSR=cyclic_stress_ratio_load(sigma_1, t), sample_cycles=sample_cycles,
            sample_CSR_array=CSR, sample_cycles_array=cycles, save_path=None)
    plt.show()






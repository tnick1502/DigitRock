import numpy as np
import matplotlib.pyplot as plt
from numpy.linalg import lstsq


def lse(__y):
    A = np.vstack([np.zeros(len(__y)), np.ones(len(__y))]).T
    k, b = lstsq(A, __y, rcond=None)[0]
    return b

# inp_x = [1, 2, 3]
# inp_y = [2, 5, 10]
#
# b = lse(inp_y)
# b1 = sum(inp_y)/len(inp_y)
#
# x = np.linspace(0, 10)
# y = 0*x + b
# y1 = 0*x + b1
#
# plt.figure()
# plt.plot(x, y)
# plt.scatter(inp_x, inp_y)
# plt.show()
def define_xc_value_residual_strength(type_ground, e, Ip, Il, Ir, sigma_3, qf, E, test_mode=True):

    xc = xc_from_qf_e_if_is(sigma_3, type_ground, e, Ip, Il, Ir, test_mode)

    if sigma_3 <= 200:
        k = 1
        print(1)
    elif sigma_3 >= 200 and sigma_3 < 500:
        k = 0.002 * sigma_3 + 0.6
        print(2)
    else:
        k = 1.6
        print(3)

    if xc:
        xc = define_xc_qf_E(qf, E)
        if test_mode == True:
            xc = xc*k

    else:
        xc = 0.15

    if xc != 0.15:
        residual_strength = define_k_q(Il, e, sigma_3)

    else:
        residual_strength = 0.95

    if xc <= 0.03:
        print('xc2', xc)
        xc = 0.3#np.random.uniform(0.025, 0.03)
        if test_mode == True:
            xc = xc*k

    return xc, residual_strength


def xc_from_qf_e_if_is(sigma_3, type_ground, e, Ip, Il, Ir, test_mode=True):
    """Функция находит деформацию пика девиаорного нагружения в зависимости от qf и E50, если по параметрам материала
    пик есть, если нет, возвращает xc = 0.15. Обжимающее напряжение должно быть в кПа"""
    sigma3mor = sigma_3 / 1000  # так как дается в КПа, а необходимо в МПа
    if (test_mode == True) and type_ground > 5:
        # if sigma_3 <= 0.1:
        #     return 0
        # else:
        def scheme(sigma3mor):
            if sigma3mor <= 0.1:
                kr_fgs = np.random.choice([0, 1], p=[0.7, 0.3])
            else:
                kr_fgs = 1
            return kr_fgs

        if Il <= 0.25:
            kr_fgs = scheme(sigma3mor)
            print(4)
            return kr_fgs
        elif Il > 0.25 and Il <= 0.3:
            print(5)
            a = scheme(sigma3mor)
            kr_fgs = np.random.choice([a, 0], p=[0.3, 0.7])\

            return kr_fgs
        elif Il > 0.3:
            print(6)
            kr_fgs = 0
            return kr_fgs



    none_to_zero = lambda x: 0 if not x else x
    Ip = Ip if Ip else 0
    Il = Il if Il else 0.5
    e0 = e if e else 0.65
    Ir = Ir if Ir else 0

    if Il > 0.35 and Ir >= 50:
        return 0

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


    # if type_ground == 3 or type_ground == 4:  # Процентное содержание гранул размером 10 и 5 мм больше половины
    #     kr_fgs = 1
    if none_to_zero(Ip) == 0:  # число пластичности. Пески (и торф?)
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

    elif Ip <= 7:  # число пластичности. Супесь

        if Il > 1:  # показатель текучести. больше 1 - текучий
            kr_fgs = 0
        elif 0 < Il <= 1:  # показатель текучести. от 0 до 1 - пластичный (для супеси)
            kr_fgs = round(np.random.uniform(0, 1))
        else:  # <=0 твердый
            kr_fgs = 1

    elif Ip > 7:  # суглинок и глина
        if Il > 0.5:  # показатель текучести.от 0.5 мягко- и текучепласт., текучий (для суглинков и глины)
            kr_fgs = 0
        elif 0.25 < Il <= 0.5:  # от 0.25 до 0.5 тугопластичный (для суглинков и глины)
            kr_fgs = round(np.random.uniform(0, 1))
        else:  # меньше 0.25 твердый и полутвердый (для суглинков и глины)
            kr_fgs = 1
    else:
        kr_fgs = 0
    return kr_fgs

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
        print('xc1', xc)

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
    clay_k_q_min = 0.9  # значения k_q соотв. минимальному ILприведенн
    clay_k_q_max = 0.95  # значения k_q соотв. максимальному ILприведенн

    if not il or il == 0:  # Пески

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

def sigmoida(x, amplitude, x_indent, y_indent, shape):
    """Функция построения сигмоиды
    Входные параметры: x - значение или массив абсцисс
                       amplitude - фмплитуда сигмоиды,
                       x_indent - положение центра по оси x,
                       y_indent - положение центра по оси y,
                       shape - размах отображения по оси x"""

    k = 10 / shape
    return ((amplitude * 2) / (1 + np.e ** (-k * (x - x_indent)))) + (y_indent - amplitude)

print(define_xc_value_residual_strength(6, 0.6, 0, 0.25, 0, 200, 500, 100000, test_mode=True))

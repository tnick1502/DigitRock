import numpy as np
from general.general_functions import define_type_ground, define_E50

atmospheric_pressure = 0.1

def define_G0_Hardin_and_Black_1968(p_ref, e) -> float:
    """Функция находит параметр G0 для глины
    :argument
        p_ref (float): референтное давление
        e (float): Коэффициент пористости
    :return
        G0, МПа"""

    G0 = 3231 * ((2.97 - e) ** 2) / (1 + e) * (p_ref * 1000) ** 0.5

    return G0 / 1000

def define_G0_Marcuson_andWahls_1972(p_ref, e) -> float:
    """Функция находит параметр G0 для глины
    :argument
        p_ref (float): референтное давление
        e (float): Коэффициент пористости
    :return
        G0, МПа"""

    G0 = 445 * ((4.4 - e) ** 2) / (1 + e) * (p_ref * 1000) ** 0.5

    return G0 / 1000

def define_G0_Kim_and_Novac_1981(p_ref, e) -> float:
    """Функция находит параметр G0 для глины
    :argument
        p_ref (float): референтное давление
        e (float): Коэффициент пористости
    :return
        G0, МПа"""

    G0 = 1576 * ((2.97 + e) ** 2) / (1 + e) * (p_ref * 1000) ** 0.5

    return G0 / 1000

def define_G0_Kokusho_et_al_1982_Kaolinite(p_ref, e) -> float:
    """Функция находит параметр G0 для глины
    :argument
        p_ref (float): референтное давление
        e (float): Коэффициент пористости
    :return
        G0, МПа"""

    G0 = 4500 * ((2.97 + e) ** 2) / (1 + e) * (p_ref * 1000) ** 0.5

    return G0 / 1000

def define_G0_Kokusho_et_al_1982_Alluvial_clays(p_ref, e) -> float:
    """Функция находит параметр G0 для глины
    :argument
        p_ref (float): референтное давление
        e (float) : Коэффициент пористости
    :return
        G0, МПа"""

    G0 = 141 * ((7.32 + e) ** 2) / (1 + e) * (p_ref * 1000) ** 0.6

    return G0 / 1000

def define_G0_Stokoe_et_al_1995(p_ref, e) -> float:
    """Функция находит параметр G0 для глины
    :argument
        p_ref (float): референтное давление
        e (float) : Коэффициент пористости
    :return
        G0, МПа"""

    G0 = 370 * (1 / (0.3 + 0.7 * e) ** 2) * (p_ref * 1000) ** 0.54 * atmospheric_pressure ** 0.46

    return G0 / 1000

def define_G0_Jamiolkowski_et_al_1995(p_ref, e) -> float:
    """Функция находит параметр G0 для глины
    :argument
        p_ref (float): референтное давление
        e (float) : Коэффициент пористости
    :return
        G0, МПа"""

    G0 = 600 * e ** (-1.3) * (p_ref * 1000) ** 0.5 * atmospheric_pressure ** 0.5

    return G0 / 1000

def define_G0_Shibuya_and_Tanaka_1996(p_ref, e) -> float:
    """Функция находит параметр G0 для глины
    :argument
        p_ref (float): референтное давление
        e (float) : Коэффициент пористости
    :return
        G0, МПа"""

    G0 = 5000 * e ** (-1.3) * (p_ref * 1000) ** 0.5

    return G0 / 1000

def define_G0_Shibuya_and_Tanaka_1996(p_ref, e) -> float:
    """Функция находит параметр G0 для глины
    :argument
        p_ref (float): референтное давление
        e (float) : Коэффициент пористости
    :return
        G0, МПа"""

    G0 = 5000 * e ** (-1.3) * (p_ref * 1000) ** 0.5

    return G0 / 1000

def define_G0_DElia_and_Lanzo_1996_sandy_silt_silty_sand(p_ref, e) -> float:
    """Функция находит параметр G0 для торфа
    :argument
        p_ref (float): референтное давление
        e (float) : Коэффициент пористости
    :return
        G0, МПа"""

    G0 = 358 * e ** (-1.21) * (p_ref * 1000) ** 0.57 * atmospheric_pressure ** 0.43

    return G0 / 1000

def define_G0_DElia_and_Lanzo_1996_clayey_silts(p_ref, e) -> float:
    """Функция находит параметр G0 для торфа
    :argument
        p_ref (float): референтное давление
        e (float) : Коэффициент пористости
    :return
        G0, МПа"""

    G0 = 358 * e ** (-1.21) * (p_ref * 1000) ** 0.57 * atmospheric_pressure ** 0.43

    return G0 / 1000

def define_G0_Vrettos_andSavidis_1999(p_ref, e) -> float:
    """Функция находит параметр G0 для глины
    :argument
        p_ref (float): референтное давление
        e (float) : Коэффициент пористости
    :return
        G0, МПа"""

    G0 = 9600 * (1 / (1 + 1.2 * e ** 2)) * (p_ref * 1000) ** 0.5

    return G0 / 1000

def define_G0_Kallioglou_et_al_2008(p_ref, PI, e) -> float:
    """Функция находит параметр G0 для всех грунтов
    :argument
        p_ref (float): референтное давление
        PI (float): Индекс пластичности
        e (float) : Коэффициент пористости
    :return
        G0, МПа"""

    G0 = (6290 - 80 * PI) * e ** (-0.63) * (p_ref * 1000) ** 0.5

    return G0 / 1000

def define_G0_Sas_et_al_2017(p_ref) -> float:
    """Функция находит параметр G0 для всех грунтов
    :argument
        p_ref (float): референтное давление
        e (float) : Коэффициент пористости
    :return
        G0, МПа"""

    G0 = (3.02 * p_ref ** 0.68 + 0.82 * (p_ref * 1000) ** 0.96) / 2

    return G0 / 1000

def define_G0_sands(p_ref, e) -> float:
    """Функция находит параметр G0 для песков
    :argument
        p_ref (float): референтное давление
        e (float) : Коэффициент пористости
    :return
        G0, МПа"""

    G0 = ((220 * ((2.17 - e) ** 2) * ((p_ref * 1000) ** (0.623))) / (1 + e)) * 0.5

    return G0 / 1000

def define_G0_clays(p_ref, Ip, e) -> float:
    """Функция находит параметр G0 для песков
    :argument
        p_ref (float): референтное давление
        e (float) : Коэффициент пористости
    :return
        G0, МПа"""

    G0 = ((((330 * ((2.17 - e) ** 2) * p_ref ** (0.5)) * 1.4 / (1 + e)) + ((4000 * p_ref) / (Ip ** (0.7)))) / 2) * 0.5

    return G0 / 1000


def define_G0_plaxis(p_ref, e, c, fi, type_ground):
    """Функция находит параметр G0 для песков
        :argument
            p_ref (float): референтное давление
            e (float) : коэффициент пористости
            c, fi: хакактеристики прочности
            type_ground: тип грунта
        :return
            G0, МПа"""

    # Находим G0_ref по формуле из методички plaxis
    G0_ref = ((2.97 - e) ** 2 / (1 + e)) * 33

    # Находим G0 с учетом пересчета глубины
    G0 = define_E50(G0_ref, c, fi, p_ref, 0.1, 0.3, deviation=0)

    # Корректируем с учетом типа грунта
    if type_ground == 9:  # Торф, ил
        G0 *= 0.3

    elif type_ground in [1, 2, 3, 4, 5]:  # Песок
        G0 *= 0.8 - type_ground * 0.1

    elif type_ground in [6, 7, 8]:  # Глина
        G0 *= 1.1 - 0.1 * type_ground
    else:
        G0 *= 0.8
    return G0


def define_gam_07(E50, G0, p_ref, c, fi, K0, PI):
    """Функция находит параметр gam07
        :argument
            E50 (float): модуль деформации, Мпа
            p_ref (float): референтное давление
            c, fi: хакактеристики прочности
            K0: коэффициент бокового обжатия
        :return
            gam07"""
    fi = np.deg2rad(fi)
    gam07 = (((1 + ((E50 * 1000) * (5 / np.random.choice(np.linspace(50000, 70000, 20))))) * 10 ** (-4)) * 10000 + \
          ((1 / (9 * 1000 * G0)) * (2 * c * (1 + np.cos(2 * fi)) + (1000 * p_ref) *
                                    (1 + K0) * np.sin(2 * fi))) * 10000 +
             (0.0352 + 0.00101*PI*1)*(p_ref**0.348)*100) / 3

    return gam07


def define_G0_gam_07(p_ref, data_physical, E50, c, fi, K0) -> float:
    """Функция находит параметр G0 для всех грунтов
    :argument
        p_ref (float): референтное давление
        data_physical (float) : Словарь данных физических свойств
        E50 (float): модуль деформации, Мпа
        c, fi: хакактеристики прочности
        K0: коэффициент бокового обжатия
    :return
        (G0 МПа, gam07)"""

    type_ground = define_type_ground(data_physical, data_physical["Ip"], data_physical["Ir"])
    e = data_physical["e"]
    if data_physical["Ip"] != "-":
        PI = data_physical["Ip"]*100
    else:
        PI = 0

    # Предварительный рассчет
    G0_plaxis = define_G0_plaxis(p_ref, e, c, fi, type_ground)

    if type_ground == 9: # Торф, ил
        G0 = (define_G0_DElia_and_Lanzo_1996_sandy_silt_silty_sand(p_ref, e) +
             define_G0_DElia_and_Lanzo_1996_clayey_silts(p_ref, e ) +
             define_G0_Kallioglou_et_al_2008(p_ref, PI, e) +
             define_G0_Sas_et_al_2017(p_ref))/4

    elif type_ground in [1, 2, 3, 4, 5]: # Песок
        G0 = (define_G0_DElia_and_Lanzo_1996_sandy_silt_silty_sand(p_ref, e) +
              define_G0_Kallioglou_et_al_2008(p_ref, 0, e) +
              define_G0_Sas_et_al_2017(p_ref) +
              define_G0_sands(p_ref, e)) / 4
        G0 *= (1 + (1.25 - type_ground * 0.25))

    elif type_ground in [6, 7, 8]: # Глина
        G0 = ((define_G0_Hardin_and_Black_1968(p_ref, e) +
              define_G0_Marcuson_andWahls_1972(p_ref, e) +
              define_G0_Kim_and_Novac_1981(p_ref, e) +
              define_G0_Kokusho_et_al_1982_Kaolinite(p_ref, e) +
              define_G0_Kokusho_et_al_1982_Alluvial_clays(p_ref, e) +
              define_G0_Jamiolkowski_et_al_1995(p_ref, e) +
              define_G0_Shibuya_and_Tanaka_1996(p_ref, e) +
              define_G0_Vrettos_andSavidis_1999(p_ref, e) +
              define_G0_Kallioglou_et_al_2008(p_ref, PI, e) +
              define_G0_Sas_et_al_2017(p_ref)) / 10) * 0.6 + define_G0_clays(p_ref, data_physical["Ip"], e) * 0.4

    G0 = G0_plaxis * 0.7 + G0 * 0.3

    gam07 = define_gam_07(E50, G0, p_ref, c, fi, K0, PI)

    return (np.round(G0, 2), np.round(gam07, 2))


if __name__ == "__main__":
    e = 0.6
    p_ref = 0.5
    Ip = 17
    E50 = 100
    G0 = 190
    c = 0.001
    fi = 42
    K0 = 1
    PI = 60
    #print(define_G0_plaxis(p_ref, e, fi))

# p_ref=0.1
# e=0.6
# print(define_G0_Hardin_and_Black_1968(p_ref, e))
# print(define_G0_Marcuson_andWahls_1972(p_ref, e))
# print(define_G0_Kim_and_Novac_1981(p_ref, e))
# print(define_G0_Kokusho_et_al_1982_Kaolinite(p_ref, e))
# print(define_G0_Kokusho_et_al_1982_Alluvial_clays(p_ref, e))
# print(define_G0_Jamiolkowski_et_al_1995(p_ref, e))
# print(define_G0_Shibuya_and_Tanaka_1996(p_ref, e))
# print(define_G0_DElia_and_Lanzo_1996_sandy_silt_silty_sand(p_ref, e))
# print(define_G0_DElia_and_Lanzo_1996_clayey_silts(p_ref, e))
# print(define_G0_Vrettos_andSavidis_1999(p_ref, e))
# print(define_G0_Kallioglou_et_al_2008(p_ref, 1, e))
# print(define_G0_Sas_et_al_2017(0.1))

"""
Глина:
define_G0_Hardin_and_Black_1968
define_G0_Marcuson_andWahls_1972
define_G0_Kim_and_Novac_1981
define_G0_Kokusho_et_al_1982_Kaolinite
define_G0_Kokusho_et_al_1982_Alluvial_clays
define_G0_Jamiolkowski_et_al_1995
define_G0_Shibuya_and_Tanaka_1996
define_G0_Vrettos_andSavidis_1999
торф:
define_G0_DElia_and_Lanzo_1996_sandy_silt_silty_sand
define_G0_DElia_and_Lanzo_1996_clayey_silts
все типы грунтов:
define_G0_Kallioglou_et_al_2008
define_G0_Sas_et_al_2017
"""
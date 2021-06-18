import numpy as np
from general.general_functions import define_type_ground

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




def define_G0(p_ref, data_physical) -> float:
    """Функция находит параметр G0 для всех грунтов
    :argument
        p_ref (float): референтное давление
        data_physical (float) : Словарь данных физических свойств
    :return
        G0, МПа"""

    type_ground = define_type_ground(data_physical, data_physical["Ip"], data_physical["Ir"])

    if type_ground == 9: # Торф, ил
        pass

    


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

import numpy as np

def dependence_Eur(E50: float, Il: float, type_ground: int) -> float:
    """ Определение модуля Eur
    :param E50: модуль деформации
    :param Il: показатель текучести
    :param type_ground: гран состав
    :return: Eur"""

    if Il == None:
        Il = np.random.uniform(0.25, 0.75)

    def dependence_Eur_of_clay():
        if type_ground == 6 or type_ground == 7 or type_ground == 8:
            if Il <= 0:
                return np.random.uniform(2.5, 3.5)
            elif Il>0 and Il <= 0.25:
                return np.random.uniform(3, 5)
            elif Il > 0.25 and Il <= 0.5:
                return np.random.uniform(4, 7)
            elif Il > 0.5 and Il <= 0.75:
                return np.random.uniform(4.8, 7.3)
            elif Il > 0.75:
                return np.random.uniform(5.8, 9)



    dependence_Eur = {
        1: np.random.uniform(3, 4),  # Песок гравелистый
        2: np.random.uniform(3.3, 4.3),  # Песок крупный
        3: np.random.uniform(4, 5),  # Песок средней крупности
        4: np.random.uniform(4, 5.5),  # Песок мелкий
        5: np.random.uniform(4, 5.5),  # Песок пылеватый
        6: dependence_Eur_of_clay(),  # Супесь
        7: dependence_Eur_of_clay(),  # Суглинок
        8: dependence_Eur_of_clay(),  # Глина
        9: np.random.uniform(3, 5),  # Торф
    }

    return E50*dependence_Eur[type_ground]












def find_E(p, p_ref, Eref, m)->float:
    """Функция """
    return Eref * (p / p_ref) ** m

def define_m(p, E, p_ref, Eref)->float:
    """Функция аппроксимации значений p, E функцией из плаксис для получения параметра m
    arguments:
        p: давление МПа
        E: касательный модуль МПа
        p_ref: референтное давление МПа
        Eref: референтный касательный модуль МПа
    return:
        m:степенной показатель
    """
    popt, pcov = curve_fit(lambda px, m: (Eref * ((px / p_ref) ** m)), p, E, method='dogbox')
    return popt

if __name__ == '__main__':

    #file = "C:/Users/Пользователь/Desktop/Тест/Циклическое трехосное нагружение/Архив/19-1/Косинусное значение напряжения.txt"
    file = "C:/Users/Пользователь/Desktop/Опыты/Опыт Виброползучесть/Песок 1/E50/Косинусное значения напряжения.txt"
    file2 = "C:/Users/Пользователь/Desktop/Тест/Девиаторное нагружение/Архив/10-2/0.2.log"
    a = ModelVibrationCreep()
    a.set_static_test_path(file2)
    a.set_dynamic_test_path(file)
    a.plotter()
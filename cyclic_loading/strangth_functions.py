import numpy as np

def perpendicular_passing_through_the_point(a: float, x: float, y: float) -> tuple:
    """Функция нахождения коэффициентов для кривой, перпендикулярной заданной и прохлдящей через заданную точку
        :argument
            a: коэффициент уравнения a*x + b, к которому будет строится перпендикуляр
            x: координата точки x, через которую должна проходить прямая
            y: координата точки y, через которую должна проходить прямая
        :return (a, b) - коэффициенты ураынения a*x + b нужной прямой
    """
    res_a = -1 / a
    res_b = y - res_a * x
    return (res_a, res_b)

def cross_line(a1: float, b1: float, a2: float, b2: float) -> tuple:
    """Функция нахождения точки пересечения кривых
        :argument
            a1: коэффициент уравнения a*x + b первой кривой
            b1: коэффициент уравнения a*x + b первой кривой
            a2: коэффициент уравнения a*x + b второй кривой
            b2: коэффициент уравнения a*x + b второй кривой
        :return (x, y) точки пересечения
    """
    x = (b2 - b1) / (a1 - a2)
    y = a1 * x + b1
    return (x, y)

def distance_between_two_points(x1: float, y1: float, x2: float, y2: float) -> float:
    """Функция расстояния между 2мя точками
        :argument
            x1: координата x первой точки
            y1: координата y первой точки
            x2: координата x второй точки
            y2: координата y второй точки
        :return (x, y) точки пересечения
    """
    return ((x1 - x2)**2 + (y1 - y2)**2)**0.5

def define_t_rel_point(c: float, fi: float, sigma_3: float, sigma_1: float) -> tuple:
    """Функция определения точки trel
            :argument
                c: сцепление
                fi: угол внутреннего трения
                sigma_3: напряжение
                sigma_1: напряжение
            :return trel
        """
    perpendicular_a, perpendicular_b = perpendicular_passing_through_the_point(
        np.tan(np.deg2rad(fi)),
        (sigma_1 + sigma_3) / 2,
        0
    )

    trel_x, trel_y = cross_line(
        perpendicular_a,
        perpendicular_b,
        np.tan(np.deg2rad(fi)),
        c
    )
    return (trel_x, trel_y)

def define_t_rel(c: float, fi: float, sigma_3: float, sigma_1: float) -> float:
    """Функция определения trel
            :argument
                c: сцепление
                fi: угол внутреннего трения
                sigma_3: напряжение
                sigma_1: напряжение
            :return trel
        """
    trel_x, trel_y = define_t_rel_point(c, fi, sigma_3, sigma_1)

    return distance_between_two_points(trel_x, trel_y, (sigma_1 + sigma_3) / 2, 0)

if __name__ == "__main__":
    #print(np.tan(np.deg2rad(25.5)))
    print(perpendicular_passing_through_the_point(np.tan(np.deg2rad(25.5)), (0.16857 + 0.118) / 2, 0))
    #print(define_t_rel(c= 0.063, fi=25.5, sigma_3=0.118, sigma_1=0.16857))
    '''
    x = np.linspace(0, 100)
    y = x
    plt.plot(x, y)
    plt.show()
    '''
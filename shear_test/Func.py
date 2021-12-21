import numpy as np
import os
def define_velocity(test_mode: int, Ip: float, type_ground: int) -> list:
    if test_mode== "Срез плашка по плашке" or test_mode== "Срез НН" or test_mode== "Плашка по плашке":
        return 2
    if type_ground ==1 or type_ground ==2\
            or type_ground==3 or type_ground==4\
            or type_ground==5 or type_ground==6:
        return 0.5
    elif type_ground==7:
        if Ip is None:
            Ip = np.random.uniform(12, 17)
        if Ip <= 12:
            return 0.1
        else:
            return 0.005
    elif type_ground==8:
        if Ip is None:
            Ip = np.random.uniform(12, 17)
        if Ip<=30:
            return 0.02
        else:
            return 0.01
    elif type_ground==9:
        return 0.01


def dictionary_deviator_loading(strain, tau, vertical_strain, sigma, velocity):
    """Формирует словарь девиаторного нагружения"""

    time_end = (7.14 / velocity) * 60
    time = np.linspace(0, time_end, len(strain)) + 0.004
    time_initial = np.hstack((np.full(5, 0.004), np.repeat(np.array([60 + np.random.uniform(0.3, 0.6),
                                                                     1860 + np.random.uniform(0.3, 0.6)]), 2)))
    time = np.hstack((time_initial, time[1:] + time_initial[-1]))
    time = np.hstack((time, np.array(time[-1]), np.array(time[-1]) + np.random.uniform(100, 120)))

    action = [''] * 2 + ['Start'] * 2 + ['LoadStage'] * 2 + \
             ['Wait'] * 2 + ['WaitLimit'] * (len(time) - 8)
    action_changed = ['', 'True'] * 4 + [''] * (len(time) - 8)

    vertical_press = np.hstack((np.full(5, 0),
                                np.full(len(time) - 5,
                                        sigma + np.random.uniform(-2, 0.1, len(time) - 5))))
    vertical_press = np.hstack((vertical_press, np.array([vertical_press[-1], np.random.uniform(1, 2)])))
    vertical_deformation = np.hstack((np.full(5, 0),
                                      np.repeat(np.random.uniform(0.3, 0.7, 2), 2), vertical_strain[1:]))
    vertical_deformation = np.hstack(
        (vertical_deformation, np.array([vertical_deformation[-1], np.random.uniform(-0.5, -0.1)])))

    shear_deformation = np.hstack((np.full(5, 0),
                                   np.repeat(np.random.uniform(0.1, 0.15, 2), 2), strain[1:]))
    shear_deformation = np.hstack((shear_deformation, np.array([shear_deformation[-1], np.random.uniform(0.1, 0.3)])))
    shear_press = np.hstack((np.full(5, 0),
                             np.repeat(np.random.uniform(3, 6, 2), 2), tau[1:]))
    shear_press = np.hstack((shear_press, np.array([shear_press[-1],
                                                    np.random.uniform(-50, -40)])))
    stage = ['Пуск'] * 3 + ['Вертикальное нагружение'] * 4 + ['Срез'] * (len(time) - 7)

    data = {
        "Time": np.round(time, 3),
        "Action": action,
        "Action_Changed": action_changed,
        "SampleHeight_mm": np.round(np.full(len(time), 35)),
        "SampleDiameter_mm": np.round(np.full(len(time), 71.4), 1),
        "VerticalPress_kPa": np.round(vertical_press, 4),
        "VerticalDeformation_mm": np.round(vertical_deformation, 7),
        "ShearDeformation_mm": np.round(shear_deformation, 8),
        "ShearPress_kPa": np.round(shear_press, 6),
        "Stage": stage
    }

    return data
a=dictionary_deviator_loading(np.linspace(1, 60, 10), np.linspace(1, 10, 10), np.linspace(1, 20, 10), 100, 0.1)
print(a)


def text_file(file_path, data):
    """Сохранение текстового файла формата Willie.
                Передается папка, массивы"""
    p = os.path.join(file_path, "Тест.log")

    def make_string(data, i):
        s = ""
        for key in data:
            s += str(data[key][i]) + '\t'
        s += '\n'
        return (s)

    with open(file_path, "w") as file:
        file.write(
            "Time" + '\t' + "Action" + '\t' + "Action_Changed" + '\t' + "SampleHeight_mm" + '\t' + "SampleDiameter_mm" + '\t' +
            "VerticalPress_kPa" + '\t' + "VerticalDeformation_mm" + '\t' + "ShearDeformation_mm" + '\t' +
            "ShearPress_kPa" + '\t' + "Stage"+ '\n')
        for i in range(len(data["Time"])):
            file.write(make_string(data, i))

#text_file("C:/Users/Пользователь/Desktop/Test.txt", a)

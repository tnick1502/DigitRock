import numpy as np
import matplotlib.pyplot as plt
from numpy.linalg import lstsq
from general.general_functions import exponent


def lse(__y):
    A = np.vstack([np.zeros(len(__y)), np.ones(len(__y))]).T
    k, b = lstsq(A, __y, rcond=None)[0]
    return b


def dictionary_without_VFS(sigma_3=100, velocity=49):
    # Создаем массив набора нагрузки до обжимающего давления консолидации
    # sigma_3 -= effective_stress_after_reconsolidation
    k = sigma_3 / velocity
    if k <= 2:
        velocity = velocity / (2 / k) - 1
    load_stage_time = round(sigma_3 / velocity, 2)
    load_stage_time_array = np.arange(1, load_stage_time, 1)
    time_max = np.random.uniform(20, 30)
    time_array = np.arange(0, time_max, 1)
    # Добавим набор нагрузки к основным массивам
    time = np.hstack((load_stage_time_array, time_array + load_stage_time_array[-1]))

    load_stage_cell_press = np.linspace(0, sigma_3, len(load_stage_time_array) + 1)
    cell_press = np.hstack((load_stage_cell_press[1:], np.full(len(time_array), sigma_3))) + \
                 np.random.uniform(-0.1, 0.1, len(time))

    final_volume_strain = np.random.uniform(0.14, 0.2)
    load_stage_cell_volume_strain = exponent(load_stage_time_array[:-1], final_volume_strain,
                                             np.random.uniform(1, 1))
    # load_stage_cell_volume_strain[0] = 0
    cell_volume_strain = np.hstack((load_stage_cell_volume_strain,
                                    np.full(len(time_array) + 1, final_volume_strain))) * np.pi * (19 ** 2) * 76 + \
                         np.random.uniform(-0.1, 0.1, len(time))
    cell_volume_strain[0] = 0
    vertical_press = cell_press + np.random.uniform(-0.1, 0.1, len(time))

    # На нэтапе нагружения 'LoadStage', на основном опыте Stabilization
    load_stage = ['LoadStage' for _ in range(len(load_stage_time_array))]
    wait = ['Wait' for _ in range(len(time_array))]
    action = load_stage + wait

    action_changed = ['' for _ in range(len(time))]
    action_changed[len(load_stage_time_array) - 1] = "True"
    action_changed[-1] = 'True'

    # Значения на последнем LoadStage и Первом Wait (следующая точка) - равны
    cell_press[len(load_stage)] = cell_press[len(load_stage) - 1]
    vertical_press[len(load_stage)] = vertical_press[len(load_stage) - 1]
    cell_volume_strain[len(load_stage)] = cell_volume_strain[len(load_stage) - 1]

    trajectory = np.full(len(time), 'ReconsolidationWoDrain')
    trajectory[-1] = "CTC"

    # Подключение запуска опыта
    time_start = [time[0]]
    time = np.hstack((time_start, time))

    action_start = ['Start']
    action = np.hstack((action_start, action))

    action_changed_start = ['True']
    action_changed = np.hstack((action_changed_start, action_changed))

    cell_press_start = [cell_press[0]]
    cell_press = np.hstack((cell_press_start, cell_press))

    cell_volume_strain_start = [cell_volume_strain[0]]
    cell_volume_strain = np.hstack((cell_volume_strain_start, cell_volume_strain))

    vertical_press_start = [vertical_press[0]]
    vertical_press = np.hstack((vertical_press_start, vertical_press))

    trajectory_start = [trajectory[0]]
    trajectory = np.hstack((trajectory_start, trajectory))

    data = {
        "Time": time,
        "Action": action,
        "Action_Changed": action_changed,
        "SampleHeight_mm": np.round(np.full(len(time), 76)),
        "SampleDiameter_mm": np.round(np.full(len(time), 38)),
        "Deviator_kPa": np.full(len(time), 0),
        "VerticalDeformation_mm": np.full(len(time), 0),
        "CellPress_kPa": cell_press,
        "CellVolume_mm3": cell_volume_strain,
        "PorePress_kPa": np.full(len(time), 0),
        "PoreVolume_mm3": np.full(len(time), 0),
        "VerticalPress_kPa": vertical_press,
        "Trajectory": trajectory
    }

    return data

print(dictionary_without_VFS(sigma_3=400, velocity=49))

import numpy as np
import matplotlib.pyplot as plt

def open_wille_log(file_path, define_frequency=True):
    """Функция считывания файла опыта с прибора Вилли"""
    test_data = {"time": np.array([]), "cycles": np.array([]), "deviator": np.array([]), "strain": np.array([]),
                 "PPR": np.array([]), "mean_effective_stress": np.array([]), "cell_pressure": 0, "frequency": 0}

    columns_key = ["Time", 'Deviator', 'Piston position', 'Pore pressure', 'Cell pressure', "Sample height"]

    # Считываем файл
    f = open(file_path)
    lines = f.readlines()
    f.close()

    # Словарь считанных данных по ключам колонок
    read_data = {}

    for key in columns_key:  # по нужным столбцам
        index = (lines[0].split("\t").index(key))  #
        read_data[key] = np.array(list(map(lambda x: float(x.split("\t")[index]), lines[2:])))

    u_consolidations = read_data['Pore pressure'][0]

    test_data["cell_pressure"] = read_data['Cell pressure'] - u_consolidations
    pore_pressure = read_data['Pore pressure'] - u_consolidations
    test_data["PPR"] = pore_pressure / test_data["cell_pressure"]
    test_data["time"] = read_data["Time"] - read_data["Time"][0]
    test_data["deviator"] = read_data['Deviator']
    test_data["strain"] = (read_data['Piston position'] / read_data['Sample height']) - \
                          (read_data['Piston position'][0] / read_data['Sample height'][0])
    test_data["mean_effective_stress"] = ((test_data["cell_pressure"] * (1 - test_data["PPR"])) * 3 +
                                          test_data["deviator"]) / 3
    test_data["mean_effective_stress"] = (test_data["deviator"] + test_data["cell_pressure"] * (
                2 - 3 * test_data["PPR"])) / 3

    if define_frequency:
        test_data["frequency"], test_data["points"] = 30, 20
        test_data["cycles"] = test_data["time"] * test_data["frequency"]
    else:
        pass
    return test_data


if __name__ == "__main__":
    data = open_wille_log("path")
    plt.plot(data["strain"], data["deviator"])
    plt.show()
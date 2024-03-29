import numpy as np
import pickle
import os
import scipy.ndimage as ndimage
from singletons import E_models
from plaxis_average.statment import averaged_statment

class AveragedItemModel:
    tests: dict = {}

    averaged_strain: np.array = None
    averaged_deviator: np.array = None

    averaged_E50: float = None
    averaged_qf: float = None

    approximate_type: str
    approximate_param_poly: int
    approximate_param_sectors: int
    approximate_param_max_deformation: int

    def __init__(self, keys=None):
        self.tests = {}
        self.first_time = True
        if keys:
            self.set_tests(keys)

    def set_tests(self, keys):
        self.tests = {}
        self.approximate_type = "poly"
        self.approximate_param_poly = 6
        self.approximate_param_sectors = 500
        self.approximate_param_max_deformation = 0.15

        # TODO: Аппроксимация и уменьшение точек
        for key in keys:
            self.tests[key] = E_models[key].deviator_loading.get_for_average()
        self.first_time = True
        self.processing()
        self.first_time = False

    def processing(self):
        self.averaged_strain, self.averaged_deviator = self.approximate_average()
        self.averaged_E50, self.averaged_qf = AveragedItemModel.define_E50_qf(self.averaged_strain, self.averaged_deviator)

    def approximate_average(self) -> (np.array, np.array):
        param = self.approximate_param_poly if self.approximate_type == "poly" else self.approximate_param_sectors

        points = []

        '''max_strains_array = []
        for test in self.tests:
            i, = np.where(self.tests[test]["strain"] >= np.max(self.tests[test]["strain"]) - 0.015)
            i = i[0]
            if np.mean(self.tests[test]["deviator"][i:]) < 0.97 * np.max(self.tests[test]["deviator"]):
                max_strains_array.append(np.max(self.tests[test]["strain"]))

        if len(max_strains_array):
            max_strain = max(max_strains_array)
        else:
            max_strain = max([max(self.tests[test]["strain"]) for test in self.tests])

        if max_strain <= self.approximate_param_max_deformation:
            max_strain = self.approximate_param_max_deformation
        '''
        if self.first_time:
            max_strain = max([max(self.tests[test]["strain"]) for test in self.tests])
            max_strain = 0.1 if max_strain < 0.1 else max_strain
            self.approximate_param_max_deformation = max_strain
        else:
            max_strain = self.approximate_param_max_deformation

        for test in self.tests:
            if self.tests[test]["strain"][-1] <= max_strain:
                i_max = np.argmax(self.tests[test]["deviator"])
                points_count = int((max_strain - self.tests[test]["strain"][i_max]) * (1000 / 0.15))
                strain_for_sum = np.hstack((self.tests[test]["strain"][:i_max],
                                            np.linspace(self.tests[test]["strain"][i_max], max_strain, points_count)))
                deviator_for_sum = np.hstack(
                    (self.tests[test]["deviator"][:i_max], np.full(points_count, self.tests[test]["deviator"][i_max])))

            else:
                i, = np.where(self.tests[test]["strain"] >= max_strain)
                i = i[0]

                strain_for_sum = self.tests[test]["strain"][:i]
                deviator_for_sum = self.tests[test]["deviator"][:i]

            for point in zip(strain_for_sum, deviator_for_sum):
                points.append(point)

        points.sort(key=lambda point: point[0])

        strain = [point[0] for point in points]
        deviator = [point[1] for point in points]

        if self.approximate_type == "sectors":
            step = max(strain) / param
            step_points = {}
            for i in range(len(strain)):
                step_x = strain[i] // step
                step_key = step_x * step
                if step_points.get(step_key, None):
                    step_points[step_key].append(deviator[i])
                else:
                    step_points[step_key] = [deviator[i]]

            averange_strain = [0]
            averange_deviator = [0]
            for key in step_points.keys():
                if len(step_points[key]):
                    averange_strain.append(key)
                    averange_deviator.append(sum(step_points[key]) / len(step_points[key]))

            averange_deviator = ndimage.gaussian_filter(np.array(averange_deviator), 3, order=0)
            averange_deviator[0] = 0

            averange_strain, averange_deviator = np.array(averange_strain), np.array(averange_deviator)

        elif self.approximate_type == "poly":
            averange_strain = np.linspace(0, max(strain), 50)
            averange_deviator = np.polyval(np.polyfit(strain, ndimage.gaussian_filter(deviator, 3, order=0), param), averange_strain)
            averange_deviator[0] = 0

            averange_strain, averange_deviator = np.array(averange_strain), np.array(averange_deviator)

        averange_deviator = ndimage.gaussian_filter(averange_deviator, 1, order=0)
        averange_deviator[0] = 0
        return averange_strain, averange_deviator

    def set_approximate_type(self, approximate_type, approximate_param, approximate_max_deformation) -> None:
        self.approximate_type = approximate_type
        self.approximate_param_max_deformation = approximate_max_deformation
        if approximate_type == "poly":
            self.approximate_param_poly = approximate_param
        elif approximate_type == "sectors":
            self.approximate_param_sectors = approximate_param

        self.processing()

    def get_results(self) -> dict:
        return {
            "averaged_E50": self.averaged_E50,
            "averaged_qf": self.averaged_qf,
        }

    def get_plot_data(self) -> dict:
        res = dict(self.tests)
        res["averaged"] = {
            "strain": self.averaged_strain,
            "deviator": self.averaged_deviator
        }
        return res

    def save_plaxis_log(self, path):
        with open(path, "w") as file:
            for i in range(len(self.averaged_strain)):
                strain = float('{:.6f}'.format(-np.round(self.averaged_strain[i], 6)))
                deviator = float('{:.3f}'.format(np.round(self.averaged_deviator[i], 3)))
                file.write(f"{strain}\t{deviator}\n")

    @staticmethod
    def define_E50_qf(strain, deviator):
        """Определение параметров qf и E50"""
        qf = np.max(deviator)
        # Найдем область E50
        i_07qf, = np.where(deviator > qf * 0.7)
        imax, = np.where(deviator[:i_07qf[0]] > qf / 2)
        imin, = np.where(deviator[:i_07qf[0]] < qf / 2)
        imax = imax[0]
        imin = imin[-1]

        E50 = (qf / 2) / (
            np.interp(qf / 2, np.array([deviator[imin], deviator[imax]]), np.array([strain[imin], strain[imax]])))

        return np.round(E50, 1), np.round(qf, 1)

class AveragedModel:
    EGES: dict = {}

    def __init__(self):
        self.EGES = {}

    def set_data(self):
        test_dict = averaged_statment.EGES

        for EGE in test_dict:
            self.EGES[EGE] = AveragedItemModel(test_dict[EGE])

    def __iter__(self):
        for key in self.EGES:
            yield key

    def __getitem__(self, key):
        if key is None:
            raise KeyError(f"No test with key None")
        elif key not in list(self.EGES.keys()):
            raise KeyError(f"No EGE with key {key}")
        return self.EGES[key]

    def __len__(self):
        return len(self.EGES)

    def dump(self, path):
        with open(path, "wb") as file:
            pickle.dump(
                {
                    "EGES": self.EGES
                },
                file
            )

    def load(self, path):
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.EGES = data["EGES"]

    def save_plaxis(self, dir):
        if not os.path.isdir(dir):
            os.mkdir(dir)

        for EGE in self.EGES:
            self.EGES[EGE].save_plaxis_log(os.path.join(dir, f"{EGE}.txt"))

    def get_results(self):
        return {EGE: self.EGES[EGE].get_results() for EGE in self.EGES}


if __name__ == '__main__':
    averaged_statment.setExcelFile(r"C:\Users\Пользователь\Desktop\Новая папка (3)\1.xls")
    E_models.load(r"C:\Users\Пользователь\Desktop\Новая папка (3)\Трёхосное сжатие (E)\E_models - 1.0.pickle")
    a = AveragedModel()
    a.set_data()
    print(a.get_results())




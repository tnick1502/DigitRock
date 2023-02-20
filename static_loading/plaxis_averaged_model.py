import numpy as np
from scipy.interpolate import pchip_interpolate
import scipy.ndimage as ndimage
from singletons import E_models, FC_models, statment

class AveragedModel:
    tests: dict = {}

    averaged_strain: np.array = None
    averaged_deviator: np.array = None

    averaged_E50: float = None
    averaged_qf: float = None
    averaged_Eur: float = None
    averaged_qf: float = None

    averaged_c: float = None
    averaged_fi: float = None
    approximate_type: str
    approximate_param_poly: int
    approximate_param_sectors: int

    def __init__(self, keys):
        self.tests = {}
        self.approximate_type = "poly"
        self.approximate_param_poly = 8
        self.approximate_param_sectors = 500
        for key in keys:
            self.tests[key] = E_models[key].deviator_loading.get_for_average()
        self.processing()

    def processing(self):
        summary_c = 0
        summary_fi = 0
        summary_poissons_ratio = 0
        summary_dilatancy_angle = 0
        zero_dilatancy = 0

        for key in self.tests:
            res_E = E_models[key].deviator_loading.get_test_results()
            summary_poissons_ratio += res_E["poissons_ratio"]
            if res_E["dilatancy_angle"] is None:
                zero_dilatancy += 1
            else:
                summary_dilatancy_angle += res_E["dilatancy_angle"][0]

            try:
                res_FC = FC_models[key].get_test_results()
                summary_c += res_FC["c"]
                summary_fi += res_FC["fi"]
            except Exception as err:
                print(err)

        self.averaged_poissons_ratio = np.round(summary_poissons_ratio / len(self.tests), 2)
        self.averaged_dilatancy_angle = np.round(summary_dilatancy_angle / (len(self.tests) - zero_dilatancy), 1)

        if summary_fi and summary_c:
            self.averaged_c = np.round(summary_c / len(self.tests), 3)
            self.averaged_fi = np.round(summary_fi / len(self.tests), 1)

        self.averaged_strain, self.averaged_deviator = self.approximate_average(
            type=self.approximate_type,
            param=self.approximate_param_poly if self.approximate_type == "poly" else self.approximate_param_sectors
        )

        self.averaged_E50, self.averaged_qf = AveragedModel.define_E50_qf(self.averaged_strain, self.averaged_deviator)

    def approximate_average(self, type="poly", param=8) -> (np.array, np.array):
        points = []

        max_strain = max([max(self.tests[test]["strain"]) for test in self.tests])

        for test in self.tests:
            qf_index = (self.tests[test]["deviator"].argmax())
            if self.tests[test]["strain"][qf_index] <= max_strain:
                points_count = int((max_strain - self.tests[test]["strain"][qf_index]) * (1000 / 0.15))
                strain_for_sum = np.hstack((self.tests[test]["strain"][:qf_index],  np.linspace(self.tests[test]["strain"][qf_index], max_strain, points_count)))
                deviator_for_sum = np.hstack((self.tests[test]["deviator"][:qf_index], np.full(points_count, np.max(self.tests[test]["deviator"]))))
            else:
                strain_for_sum = self.tests[test]["strain"]
                deviator_for_sum = self.tests[test]["deviator"]

            for point in zip(strain_for_sum, deviator_for_sum):
                points.append(point)

        points.sort(key=lambda point: point[0])

        strain = [point[0] for point in points]
        deviator = [point[1] for point in points]

        if type == "sectors":
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

            return np.array(averange_strain), ndimage.gaussian_filter(np.array(averange_deviator), 3, order=0)

        elif type == "poly":
            averange_strain = np.linspace(0, max(strain), 50)
            averange_deviator = np.polyval(np.polyfit(strain, ndimage.gaussian_filter(deviator, 3, order=0), param), averange_strain)
            averange_deviator[0] = 0

            return np.array(averange_strain), np.array(averange_deviator)

    def set_approximate_type(self, approximate_type, approximate_param) -> None:
        self.approximate_type = approximate_type
        if approximate_type == "poly":
            self.approximate_param_poly = approximate_param
        elif approximate_type == "sectors":
            self.approximate_param_sectors = approximate_param
        print(self.approximate_param_sectors, self.approximate_param_poly)
        self.processing()

    def get_results(self) -> dict:
        return {
            "averaged_c": self.averaged_c,
            "averaged_fi": self.averaged_fi,
            "averaged_E50": self.averaged_E50,
            "averaged_qf": self.averaged_qf,
            "averaged_poissons_ratio": self.averaged_poissons_ratio,
            "averaged_dilatancy_angle": self.averaged_dilatancy_angle,
        }

    def get_plot_data(self) -> dict:
        res = dict(self.tests)
        res["averaged"] = {
            "strain": self.averaged_strain,
            "deviator": self.averaged_deviator
        }
        return res

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

        return np.round(E50/1000, 3), np.round(qf/1000, 3)

class AveragedStatment:
    EGES: dict = {}

    def __init__(self):
        test_dict = {}
        for test in statment:
            EGE = statment[test].physical_properties.ige
            if test_dict.get(EGE, None):
                test_dict[EGE].append(test)
            else:
                test_dict[EGE] = [test]

        for EGE in test_dict:
            self.EGES[EGE] = AveragedModel(test_dict[EGE])

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






import numpy as np
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
    averaged_poissons_ratio: float = None
    averaged_dilatancy_angle: float = None

    def __init__(self, keys):
        self.tests = {}
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
                summary_c = res_FC["c"]
                summary_fi = res_FC["fi"]
            except:
                pass

        self.averaged_poissons_ratio = np.round(summary_poissons_ratio / len(self.tests), 2)
        self.averaged_dilatancy_angle = np.round(summary_dilatancy_angle / (len(self.tests) - zero_dilatancy), 1)
        if summary_fi and summary_c:
            self.averaged_c = np.round(summary_c / len(self.tests), 3)
            self.averaged_fi = np.round(summary_fi / len(self.tests), 1)

    def get_results(self):
        return {
            "averaged_c": self.averaged_c,
            "averaged_fi": self.averaged_fi,
            "averaged_poissons_ratio": self.averaged_poissons_ratio,
            "averaged_dilatancy_angle": self.averaged_dilatancy_angle,
        }

    def get_plot_data(self):
        res = dict(self.tests)
        res["averaged"] = {
            "strain": self.averaged_strain,
            "deviator": self.averaged_deviator
        }
        return res

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






import numpy as np
import os
import matplotlib.pyplot as plt

from singletons import Cyclic_models, statment
from cyclic_loading.cyclic_stress_ratio_function import cyclic_stress_ratio_load, approximate_test_data, define_cyclic_stress_ratio

class LiquefactionPotentialModel:
    tests: dict = []
    cycles: list = []
    CSR: list = []
    alpha: float = None
    betta: float = None
    not_fail: list = []

    def __init__(self, tests):
        self.tests = tests
        self.processing()

    def processing(self):
        self.cycles = []
        self.CSR = []
        self.not_fail = []

        for test in self.tests:
            n_fail = Cyclic_models[test].get_test_results()['n_fail']

            if n_fail:
                self.cycles.append(
                    Cyclic_models[test].get_test_results()['n_fail']
                )
                self.CSR.append(
                    cyclic_stress_ratio_load(
                        statment[statment.current_test].mechanical_properties.sigma_1,
                        statment[statment.current_test].mechanical_properties.t
                    )
                )
            else:
                self.not_fail.append(test)

        self.alpha, self.betta = approximate_test_data(self.cycles, self.CSR)

    def get_plot_data(self, borders: tuple = (1, 1000)):
        cycles_array = np.linspace(*borders, 100)
        CSR_array = define_cyclic_stress_ratio(cycles_array, self.alpha, self.betta)

        return {
            'cycles_linspase_array': cycles_array,
            'CSR_linspase_array': CSR_array,
            'cycles_array': self.cycles_array,
            'CSR_array': self.CSR_array,
        }

    def get_results(self):
        return {
            'alpha': self.alpha,
            'betta': self.betta,
        }

class GeneralLiquefactionModel:
    EGES: dict = {}

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

    def __init__(self):
        test_dict = {}

        for test in statment:
            EGE = statment[test].physical_properties.ige
            if test_dict.get(EGE, None):
                test_dict[EGE].append(test)
            else:
                test_dict[EGE] = [test]

        for EGE in test_dict:
            self.EGES[EGE] = LiquefactionPotentialModel(test_dict[EGE])

    def processing(self):
        for EGE in self.EGES:
            self.EGES[EGE].processing()




if __name__ == '__main__':
    pass



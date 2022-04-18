from abc import abstractmethod, ABCMeta
import os
import copy
from singletons import statment
import numpy as np
from loggers.logger import app_logger

class BaseSaver(metaclass=ABCMeta):
    """Абстрактный суперкласс обработчика
        Суперкласс принимает объект модели и формирует из данных опыта данные для постоения"""
    def __init__(self, obj):
        self.obj = obj

    def save_log_file(self, file_path):
        """Метод генерирует логфайл прибора"""

        if self.obj.reconsolidation is not None:
            reconsolidation_dict = self.obj.reconsolidation.get_dict()
            effective_stress_after_reconsolidation = self.obj.reconsolidation.get_effective_stress_after_reconsolidation()
        else:
            reconsolidation_dict = None
            effective_stress_after_reconsolidation = 0

        if self.obj.consolidation is not None:
            consolidation_dict = self.obj.consolidation.get_dict(effective_stress_after_reconsolidation)
        else:
            consolidation_dict = None

        deviator_loading_dict = self.obj.deviator_loading.get_dict()

        main_dict = BaseSaver.triaxial_deviator_loading_dictionary(
            reconsolidation_dict, consolidation_dict, deviator_loading_dict)

        new = {
            "Time": main_dict["Time"],
            "Action": main_dict["Action"],
            "Action_Changed": main_dict["Action_Changed"],
            "Deviator_kPa": main_dict["Action_Changed"],
            "VerticalDeformation_mm": main_dict["Action_Changed"],
            "CellPress_kPa": main_dict["Action_Changed"],
            "CellVolume_mm3": main_dict["Action_Changed"],
            "PorePress_kPa": main_dict["Action_Changed"],
            "PoreVolume_mm3": main_dict["Action_Changed"],
            "Deviator_kgs": main_dict["Action_Changed"],
            "VerticalPress_kPa": main_dict["Action_Changed"],
            "VerticalStrain": main_dict["Action_Changed"],
            "VolumeStrain": main_dict["Action_Changed"],
            "StampVolumeDeformation_mm3": main_dict["Action_Changed"],
            "VolumeDeformation_cm3": main_dict["Action_Changed"],
            "SampleSquare_mm2": main_dict["Action_Changed"],
            "SampleVolume_mm3": main_dict["Action_Changed"],
            "Deviator_MPa": main_dict["Action_Changed"],
            "VerticalPress_MPa": main_dict["Action_Changed"],
            "CellPress_MPa": main_dict["Action_Changed"],
            "PorePress_MPa": main_dict["Action_Changed"],
            "CellVolume_cm3": main_dict["Action_Changed"],
            "StampVolumeDeformation_cm3": main_dict["Action_Changed"],
            "SampleVolume_cm3": main_dict["Action_Changed"],
            "PoreVolume_cm3": main_dict["Action_Changed"],
            "Trajectory": main_dict["Action_Changed"],
        }

        BaseSaver.text_file(file_path, main_dict)

        try:
            plaxis = self.deviator_loading.get_plaxis_dictionary()
            with open('/'.join(os.path.split(file_path)[:-1]) + "/plaxis_log.txt", "w") as file:
                for i in range(len(plaxis["strain"])):
                    file.write(f"{plaxis['strain'][i]}\t{plaxis['deviator'][i]}\n")
        except Exception as err:
            app_logger.exception(f"Проблема сохранения массива для plaxis {statment.current_test}")

    def save_plaxis_log(self, file_path):
        try:
            plaxis = self.obj.deviator_loading.get_plaxis_dictionary()
            with open('/'.join(os.path.split(file_path)[:-1]) + "/plaxis_log.txt", "w") as file:
                for i in range(len(plaxis["strain"])):
                    file.write(f"{plaxis['strain'][i]}\t{plaxis['deviator'][i]}\n")
        except Exception as err:
            app_logger.exception(f"Проблема сохранения массива для plaxis {statment.current_test}")

    @staticmethod
    def addition_of_dictionaries(data1, data2, initial=True, skip_keys=None):
        if data1 is None and data2 is None:
            return None
        elif data1 is None:
            return copy.deepcopy(data2)
        elif data2 is None:
            return copy.deepcopy(data1)

        dictionary_1 = copy.deepcopy(data1)
        dictionary_2 = copy.deepcopy(data2)
        if skip_keys is None:
            skip_keys = ['']
        keys_d1 = list(dictionary_1.keys())  # массив ключей словаря 1
        len_d1_elem = len(dictionary_1[keys_d1[0]])  # длина массива под произвольным ключем словаря 1
        keys_d2 = list(dictionary_2.keys())  # массив ключей словаря 2
        len_d2_elem = len(dictionary_2[keys_d2[0]])  # длина массива под произвольным ключем словаря 2

        for key in dictionary_1:
            if key in dictionary_2:  # если ключ есть в словаре 2
                if initial and (str(type(dictionary_1[key][0])) not in ["<class 'str'>", "<class 'numpy.str_'>"]) and (
                        key not in skip_keys):  # если initial=True и элементы под ключем не строки
                    # к эламентам словаря 2 прибавляется последний элемент словаря 1 под одним ключем
                    for val in range(len(dictionary_2[key])):
                        dictionary_2[key][val] += dictionary_1[key][-1]
                dictionary_1[key] = np.append(dictionary_1[key], dictionary_2[key])
            else:  # если ключа нет в словаре 2
                dictionary_1[key] = np.append(dictionary_1[key], np.full(len_d2_elem, ''))

        for key in dictionary_2:  # если ключа нет в словаре 1
            if key not in dictionary_1:
                dictionary_1[key] = np.append(np.full(len_d1_elem, ''), dictionary_2[key])

        return dictionary_1

    @staticmethod
    def triaxial_deviator_loading_dictionary(b_test, consolidation, deviator_loading):

        start = np.random.uniform(0.5, 0.8)
        dict = {
            'Time': [0, 0, np.round(start, 3), np.round(start + 0.1, 3), np.round(start + 2, 3)],
            'Action': ["", "", "Start", "Start", "Start"],
            'Action_Changed': ["", "True", "", "", "True"],
            'SampleHeight_mm': np.full(5, 76),
            'SampleDiameter_mm': np.full(5, 38),
            'Deviator_kPa': np.full(5, 0),
            'VerticalDeformation_mm': np.full(5, 0),
            'CellPress_kPa': np.full(5, 0),
            'CellVolume_mm3': np.full(5, 0),
            'PorePress_kPa': np.full(5, 0),
            'PoreVolume_mm3': np.full(5, 0),
            'VerticalPress_kPa': np.full(5, 0),
            'Trajectory': np.full(5, "HC")

            # 'skempton': skempton_step,
            # 'step_pressure': sigma_steps
        }

        data_start = BaseSaver.addition_of_dictionaries(dict, b_test, initial=True,
                                                                        skip_keys=["SampleHeight_mm",
                                                                                   "SampleDiameter_mm"])

        data = BaseSaver.addition_of_dictionaries(copy.deepcopy(data_start), consolidation, initial=True,
                                                                        skip_keys=["SampleHeight_mm",
                                                                                   "SampleDiameter_mm"])

        dictionary = BaseSaver.addition_of_dictionaries(copy.deepcopy(data), deviator_loading, initial=True,
                                              skip_keys=["SampleHeight_mm", "SampleDiameter_mm", "Action_Changed"])


        dictionary["Time"] = BaseSaver.current_value_array(dictionary["Time"], 3)
        dictionary["Deviator_kPa"] = BaseSaver.current_value_array(dictionary["Deviator_kPa"], 3)
        # dictionary["VerticalDeformation_mm"] = current_value_array(dictionary["VerticalDeformation_mm"], 5)

        # Для части девиаторного нагружения вертикальная деформация хода штока должна писаться со знаком "-"
        CTC_index, = np.where(dictionary["Trajectory"] == 'CTC')
        str = BaseSaver.current_value_array(dictionary["VerticalDeformation_mm"][:CTC_index[0]], 5)
        str.extend(BaseSaver.current_value_array(dictionary["VerticalDeformation_mm"][CTC_index[0]:], 5, change_negatives=False))
        dictionary["VerticalDeformation_mm"] = str

        dictionary["CellPress_kPa"] = BaseSaver.current_value_array(dictionary["CellPress_kPa"], 5)
        dictionary['CellVolume_mm3'] = BaseSaver.current_value_array(dictionary["CellVolume_mm3"],
                                                                                          5)
        dictionary['PoreVolume_mm3'] = BaseSaver.current_value_array(dictionary["PoreVolume_mm3"],
                                                                                           5)
        #dictionary["CellVolume_mm3"] = dictionary["CellVolume_mm3"]
        dictionary["PorePress_kPa"] = BaseSaver.current_value_array(dictionary["PorePress_kPa"], 5)
        #dictionary["PoreVolume_mm3"] = dictionary["PoreVolume_mm3"]
        dictionary["VerticalPress_kPa"] = BaseSaver.current_value_array(dictionary["VerticalPress_kPa"], 5)


        return dictionary

    @staticmethod
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
                "Deviator_kPa" + '\t' + "VerticalDeformation_mm" + '\t' + "CellPress_kPa" + '\t' + "CellVolume_mm3" + '\t' +
                "PorePress_kPa" + '\t' + "PoreVolume_mm3" + '\t' + "VerticalPress_kPa" + '\t' +
                "Trajectory" + '\n')
            for i in range(len(data["Time"])):
                file.write(make_string(data, i))

    @staticmethod
    def current_value_array(array, number, change_negatives=True):
        s = []
        for i in range(len(array)):
            num = BaseSaver.number_format(array[i], number, change_negatives=change_negatives).replace(".", ",")
            if num == "0.00000":
                num = "0"
            s.append(num)
        return s

    @staticmethod
    def number_format(x, characters_number=0, split=".", change_negatives=True):
        """Функция возвращает число с заданным количеством знаков после запятой
        :param characters_number: количество знаков после запятой
        :param format: строка или число
        :param split: кразделитель дробной части. точка или запятая
        :param change_negatives: удаление начального знака минус"""

        if str(type(x)) in ["<class 'numpy.float64'>", "<class 'numpy.int32'>", "<class 'int'>", "<class 'float'>"]:
            # установим нужный формат
            _format = "{:." + str(characters_number) + "f}"
            round_x = np.round(x, characters_number)
            x = _format.format(round_x)

            # Уберем начальный минус  (появляется, например, когда округляем -0.0003 до 1 знака)
            if change_negatives:
                if x[0] == "-":
                    x = x[1:len(x)]

            if split == ".":
                return x
            elif split == ",":
                return x.replace(".", ",")


        else:
            _format = "{:." + str(characters_number) + "f}"

            if str(type(x)) == "<class 'numpy.ndarray'>":
                x = list(x)

            for i in range(len(x)):
                # Уберем начальный минус  (появляется, например, когда округляем -0.0003 до 1 знака)
                x[i] = _format.format(x[i])
                if change_negatives:
                    if x[i][0] == "-":
                        x[i] = x[i][1:len(x)]

                if split == ".":
                    pass
                elif split == ",":
                    x[i].replace(".", ",")

            return x





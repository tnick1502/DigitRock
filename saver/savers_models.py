import os
import copy
from singletons import statment
import numpy as np
from loggers.logger import app_logger
import shutil
from singletons.models import FC_models, E_models
from thrd.socket_thd import send_to_server

class TriaxialSaver:
    """Абстрактный суперкласс обработчика
        Суперкласс принимает объект модели и формирует из данных опыта данные для постоения"""
    def __init__(self, obj, save_path, size=[76, 38]):
        self.obj = obj
        if os.path.isdir(save_path):
            pass
        else:
            os.mkdir(save_path)
        self.size = size
        self.save_path = save_path

    def save_log_file(self, name):

        path = self.create_path(name)
        TriaxialSaver.text_file(path, self.get_dict_for_enggeo(self.size))

    def get_dict_for_enggeo(self, size):
        time_start = len(self.obj.deviator_loading._test_data.time) - len(self.obj.deviator_loading._test_data.deviator_cut)
        time = self.obj.deviator_loading._test_data.time[time_start:]
        volume_mm = np.round(np.pi * (size[1]/2)**2 *size[0], 2)
        volume_cm = np.round(volume_mm/1000, 5)
        square = np.round(np.pi * (size[1]/2)**2, 2)

        new = {
            "Time": time,
            "Action": np.full(len(time), "WaitLimit"),
            "Action_Changed": np.full(len(time), ""),
            "Deviator_kPa": self.obj.deviator_loading._test_data.deviator_cut,
            "VerticalDeformation_mm": self.obj.deviator_loading._test_data.strain_cut*size[0],
            "CellPress_kPa": np.full(len(time), self.obj.deviator_loading._test_params.sigma_3),
            "CellVolume_mm3": self.obj.deviator_loading._test_data.volume_strain_cut*volume_mm,
            "PorePress_kPa": np.full(len(time), "0"),
            "PoreVolume_mm3": self.obj.deviator_loading._test_data.volume_strain_cut*volume_mm,

            "Deviator_kgs": self.obj.deviator_loading._test_data.deviator_cut * 0.11564754,
            "VerticalPress_kPa": self.obj.deviator_loading._test_data.deviator_cut + self.obj.deviator_loading._test_params.sigma_3,
            "VerticalStrain": self.obj.deviator_loading._test_data.strain_cut,
            "VolumeStrain": self.obj.deviator_loading._test_data.volume_strain_cut,
            "StampVolumeDeformation_mm3": np.full(len(time), "0"),  ###########
            "VolumeDeformation_cm3": self.obj.deviator_loading._test_data.volume_strain_cut*volume_cm,
            ############
            "SampleSquare_mm2": np.full(len(time), str(square).replace(".", ",")),
            "SampleVolume_mm3": np.full(len(time), str(volume_mm).replace(".", ",")),
            "Deviator_MPa": self.obj.deviator_loading._test_data.deviator_cut / 1000,
            "VerticalPress_MPa": (self.obj.deviator_loading._test_data.deviator_cut + self.obj.deviator_loading._test_params.sigma_3)/1000,
            "CellPress_MPa": np.full(len(time), self.obj.deviator_loading._test_params.sigma_3)/1000,
            "PorePress_MPa": np.full(len(time), "0"),
            "CellVolume_cm3": self.obj.deviator_loading._test_data.volume_strain_cut*volume_cm,
            "StampVolumeDeformation_cm3": np.full(len(time), "0"),
            "SampleVolume_cm3": np.full(len(time), "86,19275"),
            "PoreVolume_cm3": self.obj.deviator_loading._test_data.volume_strain_cut*volume_cm,
            "Trajectory": np.full(len(time), "CTC"),
        }

        return new

    def save_plaxis_log(self, file_path):
        try:
            plaxis = self.obj.deviator_loading.get_plaxis_dictionary()
            with open('/'.join(os.path.split(file_path)[:-1]) + "/plaxis_log.txt", "w") as file:
                for i in range(len(plaxis["strain"])):
                    file.write(f"{plaxis['strain'][i]}\t{plaxis['deviator'][i]}\n")
        except Exception as err:
            app_logger.exception(f"Проблема сохранения массива для plaxis {statment.current_test}")

    def create_path(self, name):
        name_path = os.path.join(self.save_path, name)

        if os.path.exists(name_path):
            shutil.rmtree(name_path)
        os.mkdir(os.path.join(name_path, name_path))
        os.mkdir(os.path.join(name_path, "General"))

        with open(os.path.join(name_path, "General", "General.1.log"), "w") as file:
            file.write("SampleHeight_mm\tSampleDiameter_mm\n")
            file.write(f"{self.size[0]}\t{self.size[1]}\n")

        shutil.copy(os.getcwd() + "/saver/test.xml", os.path.join(name_path, f"{name}.xml"))

        os.mkdir(os.path.join(name_path, "Test"))

        return os.path.join(name_path, "Test")


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

        data_start = TriaxialSaver.addition_of_dictionaries(dict, b_test, initial=True,
                                                                        skip_keys=["SampleHeight_mm",
                                                                                   "SampleDiameter_mm"])

        data = TriaxialSaver.addition_of_dictionaries(copy.deepcopy(data_start), consolidation, initial=True,
                                                                        skip_keys=["SampleHeight_mm",
                                                                                   "SampleDiameter_mm"])

        dictionary = TriaxialSaver.addition_of_dictionaries(copy.deepcopy(data), deviator_loading, initial=True,
                                              skip_keys=["SampleHeight_mm", "SampleDiameter_mm", "Action_Changed"])


        dictionary["Time"] = TriaxialSaver.current_value_array(dictionary["Time"], 3)
        dictionary["Deviator_kPa"] = TriaxialSaver.current_value_array(dictionary["Deviator_kPa"], 3)
        # dictionary["VerticalDeformation_mm"] = current_value_array(dictionary["VerticalDeformation_mm"], 5)

        # Для части девиаторного нагружения вертикальная деформация хода штока должна писаться со знаком "-"
        CTC_index, = np.where(dictionary["Trajectory"] == 'CTC')
        str = TriaxialSaver.current_value_array(dictionary["VerticalDeformation_mm"][:CTC_index[0]], 5)
        str.extend(TriaxialSaver.current_value_array(dictionary["VerticalDeformation_mm"][CTC_index[0]:], 5, change_negatives=False))
        dictionary["VerticalDeformation_mm"] = str

        dictionary["CellPress_kPa"] = TriaxialSaver.current_value_array(dictionary["CellPress_kPa"], 5)
        dictionary['CellVolume_mm3'] = TriaxialSaver.current_value_array(dictionary["CellVolume_mm3"],
                                                                                          5)
        dictionary['PoreVolume_mm3'] = TriaxialSaver.current_value_array(dictionary["PoreVolume_mm3"],
                                                                                           5)
        #dictionary["CellVolume_mm3"] = dictionary["CellVolume_mm3"]
        dictionary["PorePress_kPa"] = TriaxialSaver.current_value_array(dictionary["PorePress_kPa"], 5)
        #dictionary["PoreVolume_mm3"] = dictionary["PoreVolume_mm3"]
        dictionary["VerticalPress_kPa"] = TriaxialSaver.current_value_array(dictionary["VerticalPress_kPa"], 5)


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
            num = TriaxialSaver.number_format(array[i], number, change_negatives=change_negatives).replace(".", ",")
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

    @staticmethod
    def umn(x, k, number):
        s = []
        for i in x:
            s.append(float(i)*k)

        return TriaxialSaver.current_value_array(s, number)

    @staticmethod
    def text_file(file_path, data):
        """Сохранение текстового файла формата Willie.
                    Передается папка, массивы"""
        p = os.path.join(file_path, "Test.1.log")

        def make_string(data, i):
            s = ""
            for key in data:
                s += str(data[key][i]) + '\t'
            s += '\n'
            return (s)

        with open(p, "w") as file:
            file.write("\t".join(
                ["Time", "Action", "Action_Changed", "Deviator_kPa", "VerticalDeformation_mm", "CellPress_kPa",
                 "CellVolume_mm3", "PorePress_kPa", "PoreVolume_mm3", "Deviator_kgs", "VerticalPress_kPa",
                 "VerticalStrain", "VolumeStrain", "StampVolumeDeformation_mm3", "VolumeDeformation_cm3",
                 "SampleSquare_mm2", "SampleVolume_mm3", "Deviator_MPa", "VerticalPress_MPa", "CellPress_MPa",
                 "PorePress_MPa", "CellVolume_cm3", "StampVolumeDeformation_cm3", "SampleVolume_cm3", "PoreVolume_cm3",
                 "Trajectory"]))
            file.write("\n")

            for i in range(len(data["Time"])):
                file.write(make_string(data, i))

class MohrSaver:
    """Абстрактный суперкласс обработчика
        Суперкласс принимает объект модели и формирует из данных опыта данные для постоения"""

    def __init__(self, obj, save_path, size):
        self.obj = obj
        if os.path.isdir(save_path):
            pass
        else:
            os.mkdir(save_path)
        self.size = size
        self.save_path = save_path

    def save_log_file(self, name):

        for test in self.obj._tests:
            s = TriaxialSaver(test, save_path=self.save_path, size=self.size)
            s.save_log_file(f"{name} {np.round(test.deviator_loading._test_params.sigma_3/1000, 3)}")

class SaverModel:
    def __init__(self, path, port):
        self.path = path
        self._port = port

    def process(self):

        send_to_server(self._port, {"window_title": "Процесс ..."})
        send_to_server(self._port, {"label": "Генерация xml..."})
        send_to_server(self._port, {"maximum": len(statment)})

        for i, lab in enumerate(statment):

            d, h = statment[lab].physical_properties.sample_size

            if statment.general_parameters.test_mode == "Трёхосное сжатие (E)":
                s = TriaxialSaver(E_models[lab], self.path, size=[h, d])
                s.save_log_file(lab)

            elif statment.general_parameters.test_mode == "Трёхосное сжатие с разгрузкой":
                s = TriaxialSaver(E_models[lab], self.path, size=[h, d])
                s.save_log_file(lab)

            elif statment.general_parameters.test_mode == "Трёхосное сжатие с разгрузкой (plaxis)":
                s = TriaxialSaver(E_models[lab], self.path, size=[h, d])
                s.save_log_file(lab)

            elif statment.general_parameters.test_mode == "Трёхосное сжатие (F, C, E)":
                s = TriaxialSaver(E_models[lab], self.path, size=[h, d])
                s.save_log_file(lab)

                s = MohrSaver(FC_models[lab], self.path, size=[h, d])
                s.save_log_file(lab)

            elif statment.general_parameters.test_mode == "Трёхосное сжатие (F, C, Eur)":
                s = TriaxialSaver(E_models[lab], self.path, size=[h, d])
                s.save_log_file(lab)

                s = MohrSaver(FC_models[lab], self.path, size=[h, d])
                s.save_log_file(lab)

            elif statment.general_parameters.test_mode == 'Трёхосное сжатие (F, C)':
                s = MohrSaver(FC_models[lab], self.path, size=[h, d])
                s.save_log_file(lab)

            elif statment.general_parameters.test_mode == 'Трёхосное сжатие КН':
                s = MohrSaver(FC_models[lab], self.path, size=[h, d])
                s.save_log_file(lab)

            elif statment.general_parameters.test_mode == 'Трёхосное сжатие НН':
                s = MohrSaver(FC_models[lab], self.path, size=[h, d])
                s.save_log_file(lab)

            send_to_server(self._port, {"value": i + 1})

        send_to_server(self._port, {"break": True})
        app_logger.info("Выгнаны xml")










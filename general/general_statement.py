from PyQt5.QtWidgets import QFileDialog, QHBoxLayout, QGroupBox, QDialog, \
    QComboBox, QWidget, QLineEdit, QPushButton, QVBoxLayout, QLabel, QMessageBox, QApplication
from PyQt5.QtCore import Qt
import sys
import os

from openpyxl import load_workbook

from general.excel_functions import read_customer, form_xlsx_dictionary, table_data
from general.general_functions import create_json_file, read_json_file, unique_number
from general.initial_tables import Table
from general.report_general_statment import save_report

class StatementGenerator(QDialog):
    """
    Класс для представления пользовательского интерфейса импорта ведомости и
    вывода и экспорта обработанных данных в соответствии с заданными параметрами


    Атрибуты
    --------

    path : str
        путь к xls файлу ведомости
    customer : dict
        загруженные данные из ведомости по ключам
        ["customer", "object_name", "data", "accreditation"] о ["Заказчик", "Объект", "Дата", "Аккредитация"]
    statment_data : dict
        словарь с ключами по наименованиям колонок и соответствующими массивами колонок - numpy.ndarray


    Методы
    ------
    create_UI():
        устанавливает пользовательский интерфейс для импорта ведомости и вывода и экспорта
        считывает из ведомости данные в customer и statment_data

    _plot():
        выводит данные в таблицу на интерфесе
    _save_report():
        экспортирует данные в pdf-файл
    _structure_assretion_tests(table, structure):
        тесты для проверки корректности введенных пользователем параметров и возможности
        отображения и/или экспорта ведомости. Возвращает true, если все тесты успешны

    """

    def __init__(self, parent, path=None, statement_structure=None):
        super().__init__(parent)

        self.setGeometry(100, 50, 1000, 950)

        self.path = path
        self.customer = None

        if path:
            self.open_excel(path)

        self.statment_data = None

        self.create_UI()

    def create_UI(self):
        self.layout = QVBoxLayout()
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(5, 5, 5, 5)

        self.open_box = QGroupBox("Текущая ведомость")
        self.open_box_layout = QHBoxLayout()
        self.button_open = QPushButton("Открыть файл ведомости")
        self.button_open.clicked.connect(self.open_excel)
        self.open_box_layout.addWidget(self.button_open)
        self.text_file_path = QLineEdit()
        self.text_file_path.setDisabled(True)
        self.open_box.setFixedHeight(80)
        self.open_box_layout.addWidget(self.text_file_path)
        self.open_box.setLayout(self.open_box_layout)
        self.layout.addWidget(self.open_box)

        self.customer_table = Table(headers=["Заказчик", "Объект", "Дата", "Аккредитация"])
        self.customer_table.set_data([["Заказчик", "Объект", "Дата", "Аккредитация"], ["", "", "", ""]], "Stretch")
        self.customer_table.setFixedHeight(80)
        self.layout.addWidget(self.customer_table)

        self.StatementStructure = StatementStructure(statement_structure_key="triaxial_cyclic")
        self.layout.addWidget(self.StatementStructure)

        self.statment_table = Table(moove=True)
        self.layout.addWidget(self.statment_table)

        self.StatementStructure.plot_structure_button.clicked.connect(self._plot)

        self.StatementStructure.save_button.clicked.connect(self._save_report)

        self.setLayout(self.layout)

    def open_excel(self, path=None):
        if path:
            self.path = path
        else:
            self.path = QFileDialog.getOpenFileName(self, 'Open file', '/home')[0]
            if self.path:
                try:
                    wb = load_workbook(self.path, data_only=True)
                    marker, self.customer = read_customer(wb)
                    self.customer_table.set_data([["Заказчик", "Объект", "Дата", "Аккредитация"],
                                                  [self.customer[i] for i in
                                                   ["customer", "object_name", "data", "accreditation"]]], "Stretch")
                    self.text_file_path.setText(self.path)
                    self.statment_data = form_xlsx_dictionary(wb, last_key='IV')
                except FileNotFoundError as error:
                    print(error)
            else:
                pass

    def _plot(self):
        # print(self.StatementStructure.get_structure())
        # print(table_data(self.statment_data, self.StatementStructure.get_structure()))
        if self.statment_data:
            if self._structure_assretion_tests(self.statment_data, self.StatementStructure.get_structure()):
                titles, data, scales = table_data(self.statment_data, self.StatementStructure.get_structure())
                for i in range(len(data)):
                    for j in range(len(data[i])):
                        if data[i][j] == 'None':
                            data[i][j] = ' '
                self.statment_table.set_data([titles] + data, "Stretch")
            else:
                pass

    def _structure_assretion_tests(self, table, structure):
        '''
        функция проверки корректности структуры для имеющейся таблицы данных
        возвращает True если все тесты успешны
        возвращает False если нет
        '''
        try:

            # Блок теста триггеров:

            # Корректировка триггеров как в table_data
            if (structure["trigger"] is None) or (structure["trigger"] == []):
                structure["trigger"] = [None]
            while len(structure["trigger"]) > 1 and structure["trigger"].count(None) > 0:
                structure["trigger"].remove(
                    None)  # удаляем None так, чтобы остался массив из одного None на случай массива [None, A]
            # для каждого тригера вызываем проверку его налачия в данных таблицы
            if structure["trigger"].count(None) == 0:
                for i in range(len(structure["trigger"])):
                    assert (structure["trigger"][i] in table.keys()), 'Триггер ' + str(
                        structure["trigger"][i]) + ' отсутствует'

            #
            for i in range(len(structure["columns"])):
                # for j in range(len(structure["columns"][str(i)]['cell'])):
                assert (structure["columns"][str(i)]['cell'] in table.keys()), 'Ячейка ' + str(
                    structure["columns"][str(i)]['cell']) + ' отсутствует'

            return True

        except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error))
            return False

    def _save_report(self):
        if self.statment_data:
            if self._structure_assretion_tests(self.statment_data, self.StatementStructure.get_structure()):
                try:
                    # file = QFileDialog.getOpenFileName(self, 'Open file')[0]
                    save_file_pass = QFileDialog.getExistingDirectory(self, "Select Directory")

                    save_file_name = 'Отчет.pdf'
                    # считывание параметра "Заголовок"

                    statement_title = self.StatementStructure.get_structure().get("statement_title", '')

                    # self.StatementStructure._additional_parameters = \
                    #    StatementStructure.read_ad_params(self.StatementStructure.additional_parameters.text())

                    titles, data, scales = table_data(self.statment_data, self.StatementStructure.get_structure())
                    for i in range(len(data)):
                        for j in range(len(data[i])):
                            if data[i][j] == 'None':
                                data[i][j] = ' '
                    # ["customer", "object_name", "data", "accreditation"]
                    # ["Заказчик", "Объект", "Дата", "Аккредитация"]
                    # Дата
                    data_report = self.customer["data"]
                    customer_data_info = ['Заказчик:', 'Объект:']
                    # Сами данные (подробнее см. Report.py)
                    customer_data = [self.customer[i] for i in ["customer", "object_name"]]

                    try:
                        if save_file_pass:
                            save_report(titles, data, scales, data_report, customer_data_info, customer_data,
                                        statement_title, save_file_pass, unique_number(length=7, postfix="-ОВ"),
                                        save_file_name)
                            QMessageBox.about(self, "Сообщение", "Успешно сохранено")
                    except PermissionError:
                        QMessageBox.critical(self, "Ошибка", "Закройте файл для записи", QMessageBox.Ok)
                    except:
                        pass
                except (ValueError, IndexError, ZeroDivisionError) as error:
                    QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
                    pass
            else:
                pass
            pass

class StatementStructure(QWidget):
    """
    Класс для представления пользовательского интерфейса и механизмов создания и хранения шаблонов
    для параметров общей ведомости и структуры данных


    Атрибуты
    --------

    params : dict
        общий перечень перечень параметров ведомости
    _statement_structures_path : str
        путь к .json файлу с шаблономи ведомостей
    _statement_structures : dict
        общий перечень шаблонов параметров ведомости, ключем к конкретной структуре с шаблоном является имя шаблона
    _statement_structure : dict
        шаблон параметров ведомости в виде структуры вида:
            {"trigger": ["A"], "columns": {"0": {"title": "Скважина", "cell": "B", "number_of_decimal_places": None, "scale_factor": "*"},
                        "1": {"title": "Лаб.номер", "cell": "A", "number_of_decimal_places": None, "scale_factor": "*"},
                        "2": {"title": "Глубина", "cell": "C", "number_of_decimal_places": None, "scale_factor": "*"}}}


    Методы
    ------
    create_UI():
        устанавливает пользовательский интерфейс для параметров общей ведомости и вывода и сохранения результатов
    get_structure():
        считывает текущие параметры ведомости с интерфеса в структуру _statement_structure и возвращает её

    _open_statement_structures(path = None):
        загружает файл с шаблонами параметров в _statement_structures, загружает перечень шаблонов в список
    _combo_changed():
        устанавливает в _statement_structure текущий набор параметров по выбранному шаблону ведомости в списке шаблонов
    _set_combo_structure(key):
        устанавливает текущий шаблон по имени из списка
    _set_structure():
        заполняет поля параметров на интерфейсе согласно текущему набору в _statement_structure
    _save_structure():
        добавляет заполненные пользователем параметры к списку шаблонов по названию, определенному польлзователем
    _get_structure():
        загружает текущие параметры с интерфейса в _statement_structure

    """

    def __init__(self, path=None, statement_structure_key=None):
        super().__init__()

        self.params = {"parameter_title": "Заголовок",
                       "parameter_trigger": "Триггеры",
                       "parameter_cells": "Выбранные ячейки",
                       "parameter_column_titles": "Имена в ведомости",
                       "parameter_decimal": "Число знаков после запятой",
                       "scale_factor": "Размер столбцов",
                       "additional_parameters": "Дополнительные параметры испытаний"}

        self._statement_structures_path = os.path.join(os.getcwd() + "/project_data/", "structures.json")

        self._statement_structures = None
        self._statement_structure = None

        self.create_UI()
        self.setFixedHeight(38 * len(self.params) + 70)  # задаем высоту в завивисиости от числа параметров

        self._open_statement_structures(self._statement_structures_path)  # вызываем функцию от пути которая считывает структуру из файла json
        if statement_structure_key:  # только если в переменную передали ключ
            self._set_combo_structure(statement_structure_key)


    def create_UI(self):
        self.layout = QVBoxLayout()
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(5, 5, 5, 5)

        self.parameter_box = QGroupBox("Параметры общей ведомости")
        self.parameter_box_layout = QVBoxLayout()

        for param in self.params.keys():
            setattr(self, "line_{}".format(param), QHBoxLayout())  # Создаем элемент QHBoxLayout()
            label = QLabel(self.params[param])  # Создааем подпись
            label.setFixedWidth(150)  # Фиксируем размер подписи
            getattr(self, "line_{}".format(param)).addWidget(label)  # Размещаем подпись на ранее созданном layout

            setattr(self, "{}".format(param), QLineEdit())  # Создаем элемент QLineEdit()
            getattr(self, "line_{}".format(param)).addWidget(getattr(self, "{}".format(param)))  # Размещаем
            # QLineEdit()
            # в layout
            self.parameter_box_layout.addLayout(getattr(self, "line_{}".format(param)))

        self.parameter_box.setLayout(self.parameter_box_layout)

        self.end_line = QHBoxLayout()
        self.dafault_parameter_box = QGroupBox("Шаблоны ведомостей")
        self.dafault_parameter_box.setFixedWidth(800)
        self.dafault_parameter_box.setFixedHeight(70)
        self.dafault_parameter_box_layout = QHBoxLayout()
        self.combo_box = QComboBox()
        self.combo_box.activated.connect(self._combo_changed)
        self.dafault_parameter_box_layout.addWidget(self.combo_box)
        self.combo_box.setFixedWidth(180)
        self.new_statement_name = QLineEdit()
        #self.new_statement_name.setFixedWidth(120)
        self.dafault_parameter_box_layout.addWidget(self.new_statement_name)
        self.save_new_structure_button = QPushButton("Сохранить шаблон")
        self.save_new_structure_button.setFixedWidth(110)
        self.dafault_parameter_box_layout.addWidget(self.save_new_structure_button)
        self.save_new_structure_button.clicked.connect(self._save_structure)
        self.open_new_structure_button = QPushButton("Открыть шаблон")
        self.open_new_structure_button.setFixedWidth(110)
        self.dafault_parameter_box_layout.addWidget(self.open_new_structure_button)
        self.dell_structure_button = QPushButton("Удалить шаблон")
        self.dell_structure_button.setFixedWidth(110)
        self.dafault_parameter_box_layout.addWidget(self.dell_structure_button)
        """!!!"""
        self.dell_structure_button.clicked.connect(self._dell_structure)

        self.dafault_parameter_box.setLayout(self.dafault_parameter_box_layout)
        self.end_line.addWidget(self.dafault_parameter_box)

        self.plot_structure_button = QPushButton("Построить по шаблону")
        self.plot_structure_button.setFixedWidth(140)
        self.plot_structure_button.setFixedHeight(70)
        self.end_line.addWidget(self.plot_structure_button)
        self.save_button = QPushButton("Сохранить ведомость")
        self.save_button.setFixedWidth(140)
        self.save_button.setFixedHeight(70)
        self.end_line.addWidget(self.save_button)
        self.end_line.addStretch(-1)
        self.parameter_box_layout.addLayout(self.end_line)
        self.layout.addWidget(self.parameter_box)
        self.setLayout(self.layout)

    def _open_statement_structures(self, path=None):
        """Чтение файла структур"""
        if path:
            file = path
        else:
            file = QFileDialog.getOpenFileName(self, 'Open file', '/home')[0]

        self._statement_structures_path = file

        try:
            self.combo_box.clear()  # необходимо для очистки предыдущего импорта если он был
            self._statement_structures = read_json_file(self._statement_structures_path)
            self.combo_box.addItems(self._statement_structures.keys())
        except:
            pass

    def _combo_changed(self):
        """Смена значений в combo_change"""
        if self._statement_structures:
            self._statement_structure = self._statement_structures[self.combo_box.currentText()]
        self._set_structure()
        """!!!"""
        self.new_statement_name.setText(self.combo_box.currentText())

    def _set_combo_structure(self, key):
        """Поставить значение по ключу в combo_box"""
        index = self.combo_box.findText(key, Qt.MatchFixedString)
        if index >= 0:
            self.combo_box.setCurrentIndex(index)
        if index == -1:
            self._statement_structure = None
        self._combo_changed()

    def _set_structure(self):
        """Заполнение формы и заголовка по структуре таблицы"""
        if self._statement_structure:
            statement_title, triggers, cells, titles, decimal, scale_factor, additional_parameters = StatementStructure.form_output_from_structure(
                self._statement_structure)
            self.parameter_title.setText(statement_title)
            self.parameter_trigger.setText(triggers)
            self.parameter_cells.setText(cells)
            self.parameter_column_titles.setText(titles)
            self.parameter_decimal.setText(decimal)
            self.scale_factor.setText(scale_factor)
            self.additional_parameters.setText(additional_parameters)
        else:
            self.parameter_title.setText("")
            self.parameter_trigger.setText("")
            self.parameter_cells.setText("")
            self.parameter_column_titles.setText("")
            self.parameter_decimal.setText("")
            self.scale_factor.setText("")
            self.additional_parameters.setText("")

        # self.additional_parameters.setText('; '.join(self._additional_parameters))

    def _save_structure(self):
        """Функция сохранения новой структуре в json файле"""
        text = self.new_statement_name.text()

        if text:
            try:
                # self._additional_parameters=StatementStructure.read_ad_params(self.additional_parameters.text())
                self._get_structure()

                self._statement_structures[text] = self._statement_structure
                create_json_file(self._statement_structures_path, self._statement_structures)
                self._open_statement_structures(self._statement_structures_path)
                self._set_combo_structure(text)
            except:
                QMessageBox.critical(self, "Ошибка", "Ошибка добавления")
        else:
            QMessageBox.critical(self, "Ошибка", "Введите имя шаблона")

    """!!!"""
    def _dell_structure(self):
        """Функция удаления структуры"""

        text = self.new_statement_name.text()

        if text:
            try:
                self._statement_structures.pop(text)
                create_json_file(self._statement_structures_path, self._statement_structures)
                self._open_statement_structures(self._statement_structures_path)
                self.combo_box.setCurrentIndex(0)
                self._set_combo_structure(self.combo_box.currentText())
            except KeyError:
                QMessageBox.critical(self, "Ошибка", "Неверное имя шаблона")

    def _get_structure(self):
        statement_title = self.parameter_title.text()
        triggers = StatementStructure.read_line(self.parameter_trigger.text())
        cells = StatementStructure.read_line(self.parameter_cells.text())
        titles = StatementStructure.read_titles(self.parameter_column_titles.text())
        decimal = StatementStructure.read_line(self.parameter_decimal.text())
        scale_factor = StatementStructure.read_scale(self.scale_factor.text())
        additional_parameters = self.additional_parameters.text()
        self._statement_structure = StatementStructure.form_structure(statement_title, triggers, cells, titles, decimal, scale_factor,
                                                                      additional_parameters)

    def get_structure(self):
        """Для вызова извне. Считывает структуру таблицы"""
        self._get_structure()
        return self._statement_structure

    @staticmethod
    def form_output_from_structure(structure):
        """
        формирует 5 строк для вывода по ключам из структуры вида:
                structure = {"trigger": ["A"],  #None
                     "columns": {"0": {"title": "Скважина", "cell": "B", "number_of_decimal_places": None, "scale_factor": "*"},
                                 "1": {"title": "Лаб.номер", "cell": "A", "number_of_decimal_places": None, "scale_factor": "*"},
                                 "2": {"title": "Глубина", "cell": "C", "number_of_decimal_places": None, "scale_factor": "*"}}}
        """

        if structure["trigger"] is None:
            structure["trigger"] = [None]

        additional_parameters = structure.get("additional_parameter", "")
        statement_title = structure.get("statement_title", '')

        triggers = ', '.join(str(structure["trigger"][j]) for j in range(len(structure["trigger"])))

        titles = '; '.join(str(structure["columns"][str(j)]["title"]) for j in range(len(structure["columns"])))
        cells = ', '.join(str(structure["columns"][str(j)]["cell"]) for j in range(len(structure["columns"])))
        try:
            decimal = ', '.join(
                str(structure["columns"][str(j)]["number_of_decimal_places"]) for j in range(len(structure["columns"])))
        except:
            decimal = "None"
        try:
            scale_factor = ', '.join(
                str(structure["columns"][str(j)]["scale_factor"]) for j in range(len(structure["columns"])))
        except:
            scale_factor = "*"

        # Пользователю не нужно видеть None
        triggers = triggers.replace(', None', "").replace('None', "")
        cells = cells.replace(', None', "").replace('None', "")
        titles = titles.replace('; None', "").replace('None', "")
        decimal = decimal.replace(', None', "").replace('None', "")


        # scale_factor = scale_factor.replace(', *', '').replace('*', '')

        return statement_title, triggers, cells, titles, decimal, scale_factor, additional_parameters

    @staticmethod
    def read_scale(line):
        line = StatementStructure.read_line(line)
        for i in range(len(line)):
            try:
                float(line[i])
            except:
                if line[i] != '*':
                    line[i] = '*'
        return line

    @staticmethod
    def read_titles(line):

        if line is None:
            s = [None]  # иначе вылетают forы
        else:
            s = [i.strip(" ") for i in line.split(";")]

        return s

    @staticmethod
    def read_ad_params(line):

        if line is None:
            s = [None]  # иначе вылетают forы
        else:
            s = [i.strip(" ") for i in line.split(";")]

        return s

    @staticmethod
    def read_line(line):

        if line is None:
            s = [None]  # иначе вылетают forы
        else:
            s = line.upper().replace(' ', "").split(",")

        return s

    @staticmethod
    def check_lines_len(line1, line2):
        """
        Сравнивает две строки, дополняет меньшую строку до больше через None
        """
        while len(line1) > len(line2):
            line2.append(None)
        while len(line2) < len(line2):
            line2 = line2[:-1]
        return line1, line2

    @staticmethod
    def check_scale_factor_len(line1, line2):
        """
        проверяет длину line2, если она меньше, то в нее дописываются "*"
        """
        while len(line1) > len(line2):
            line2.append("*")
        while len(line1) < len(line2):
            line2 = line2[:-1]
        return line2

    @staticmethod
    def form_structure(statement_title, trigger, cell, title, number_of_decimal_places, scale_factor, additional_parameters):
        """
        Формирует структуру следующего вида
        structure = {"statement_title": "statement_title",
                     "trigger": ["A"],  #None
                     "columns": {"0": {"title": "Скважина", "cell": "B", "number_of_decimal_places": None, "scale_factor": "*"},
                                 "1": {"title": "Лаб.номер", "cell": "A", "number_of_decimal_places": None, "scale_factor": "*"},
                                 "2": {"title": "Глубина", "cell": "C", "number_of_decimal_places": None, "scale_factor": "*"}},
                     "additional_parameter": [additional_parameters]}
        """

        if number_of_decimal_places[0] == "":
            number_of_decimal_places = [None]
        if scale_factor[0] == "":
            scale_factor = ["*"]
        if trigger[0] == "":
            trigger = [None]

        cell, title = StatementStructure.check_lines_len(cell, title)
        cell, number_of_decimal_places = StatementStructure.check_lines_len(cell, number_of_decimal_places)
        scale_factor = StatementStructure.check_scale_factor_len(cell, scale_factor)

        structure = {"statement_title": statement_title,
                     "trigger": trigger,
                     "columns": {str(i): {"title": title[i], "cell": cell[i],
                                          "number_of_decimal_places": number_of_decimal_places[i],
                                          "scale_factor": scale_factor[i]} for i in range(len(cell))},
                     "additional_parameter": additional_parameters}
        return structure

if __name__ == "__main__":
    app = QApplication(sys.argv)

    headlines = ["Лаб. ном.", "Модуль деформации E, кПа", "Сцепление с, МПа",
                 "Угол внутреннего трения, град",
                 "Обжимающее давление 𝜎3", "K0", "Косательное напряжение τ, кПа",
                 "Число циклов N, ед.", "Бальность, балл", "Магнитуда", "Понижающий коэф. rd"]

    fill_keys = ["lab_number", "E", "c", "fi", "sigma3", "K0", "t", "N", "I", "magnituda", "rd"]

    data_test_parameters = {"equipment": ["Выберите прибор", "Прибор: Вилли", "Прибор: Геотек"],
                            "test_type": ["Режим испытания", "Сейсморазжижение", "Штормовое разжижение"],
                            "k0_condition": ["Тип определения K0",
                                             "K0: По ГОСТ-65353", "K0: K0nc из ведомости",
                                             "K0: K0 из ведомости", "K0: Формула Джекки",
                                             "K0: K0 = 1"]
                            }

    Dialog = StatementGenerator(None)
    Dialog.show()
    app.setStyle('Fusion')


    sys.exit(app.exec_())



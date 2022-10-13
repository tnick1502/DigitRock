from copy import copy
from typing import List

import openpyxl
from openpyexcel.utils import get_column_letter, coordinate_from_string
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Alignment


# file = r"C:\\reports\\test_join.xlsx"
# img = r"C:\\reports\\logo.png"
#
# wb = openpyxl.load_workbook(file)
# ws = wb.worksheets[0]
# # img = openpyxl.drawing.image.Image(img)
# # img.anchor = 'A1'
# # ws.add_image(img)
# wb.save('C:\\reports\\out.xlsx')


class ReportXlsxSaver:
    __TEMPLATE_PATH: str = r"general/test_join.xlsx"
    __book: 'Workbook' = None
    __sheet: 'Worksheet' = None
    __tests_data: 'dict' = {'labNum': {'skv': None, 'depth': None, 'type': None, 'params': {}}}
    __params_positions: 'dict' = {}
    _base_height = 15

    def __init__(self):
        self.__book = openpyxl.load_workbook(self.__TEMPLATE_PATH)
        self.__sheet = self.__book.worksheets[0]

    def set_data(self, customer: 'str', obj_name: 'str', test_title: 'str', date: 'str', tests_data: 'dict',
                 additional_data: 'List' = None, accreditation: 'str' = None):
        """

        """
        self.__tests_data = copy(tests_data)

        if len(self.__tests_data.keys()) < 1:
            return

        # данные по объекту
        self.__sheet[self.pos_of('date')].value = date
        self.__sheet[self.pos_of('customer')].value = customer
        self.__sheet[self.pos_of('obj_name')].value = obj_name
        self.__sheet[self.pos_of('test_title')].value = test_title

        # дополнителньые данные
        if accreditation:
            accreditation_font = copy(self.__sheet[self.pos_of('accreditation')].font)
            accreditation_border = copy(self.__sheet[self.pos_of('accreditation')].border)
            accreditation_fill = copy(self.__sheet[self.pos_of('accreditation')].fill)

            self.__sheet[self.pos_of('accreditation')].value = accreditation
            self.__sheet[self.pos_of('accreditation')].font = accreditation_font
            self.__sheet[self.pos_of('accreditation')].border = accreditation_border
            self.__sheet[self.pos_of('accreditation')].fill = accreditation_fill
            self.__sheet[self.pos_of('accreditation')].alignment = Alignment(wrapText=True,
                                                                             horizontal='center',
                                                                             vertical='center')

        # Заполняем заголовки с параметрами опыта:
        _first_col = self.pos_of('last_title_col') + 1
        _params = [*self.__tests_data.keys()]
        if _params and len(_params) > 0:
            for param in self.__tests_data[[*self.__tests_data.keys()][0]]['params']:
                self.__params_positions[param] = get_column_letter(_first_col)
                self.set_cell_value(f"{self.__params_positions[param]}{self.pos_of('first_row')}", value=param,
                                    style_key='labNum')
                lab_num_width = self.__sheet.column_dimensions[self.pos_of('labNum')].width
                self.__sheet.column_dimensions[self.__params_positions[param]].width = lab_num_width

                _first_col = _first_col + 1

        # Начинаем вставлять строчки с опытами
        _cur_row = self.pos_of('first_row') + 1  # строка с заголовками + 1
        for labnum in self.__tests_data:
            # Вставляем строчку с новым опытом и записываем лобораторный номер
            self.__sheet.insert_rows(idx=_cur_row)
            self.__sheet.row_dimensions[_cur_row].height = self._base_height
            self.set_cell_value(self.pos_of('labNum')+str(_cur_row), value=labnum, style_key='labNum')
            # Далее проходим по всем свойствам пробы кроме дополнительных 'params'
            for prop in self.__tests_data[labnum]:
                if prop != 'params':
                    self.set_cell_value(f"{self.pos_of(prop)}{_cur_row}",
                                        value=self.__tests_data[labnum][prop],
                                        style_key=prop)
                    if prop == 'type':
                        self.__sheet.merge_cells(f"{self.pos_of('type')}{_cur_row}"
                                                 f":{get_column_letter(self.pos_of('last_title_col'))}{_cur_row}")
                    continue

                # Параметры заполняем отдельно для каждого цикла
                for param in self.__tests_data[labnum]['params']:
                    self.set_cell_value(f"{self.__params_positions[param]}{_cur_row}",
                                        value=self.__tests_data[labnum]['params'][param],
                                        style_key='depth')
            # Конец заполнения свойств пробы
            _cur_row = _cur_row + 1

        # После всех проб заполняем дополнительные параметры
        _last_col = get_column_letter(self.pos_of('last_title_col'))
        if self.__params_positions:
            _values = [*self.__params_positions.values()]
            _last_col = max(_values)
        self.__sheet.merge_cells(f"{self.pos_of('labNum')}{_cur_row}:{_last_col}{_cur_row}")
        _cur_row = _cur_row + 1
        if additional_data:
            for data in additional_data:
                self.__sheet.insert_rows(idx=_cur_row)
                self.__sheet.row_dimensions[_cur_row].height = self._base_height
                self.set_cell_value(f"{self.pos_of('labNum')}{_cur_row}",
                                    value=data,
                                    style_key='labNum')
                self.__sheet.merge_cells(f"{self.pos_of('labNum')}{_cur_row}:{_last_col}{_cur_row}")
                _cur_row = _cur_row + 1
        # Конец заполнения дополнительных параметров

        # Теперь нужно привести в порядок табличку внизу отчета
        _b_table_first_row = coordinate_from_string(self.pos_of('date'))[-1] + (_cur_row - self.pos_of('first_row')) - 2
        self.__sheet.row_dimensions[_b_table_first_row - 6].height = self._base_height
        self.__sheet.row_dimensions[_b_table_first_row - 5].height = self._base_height
        self.__sheet.row_dimensions[_b_table_first_row - 4].height = self._base_height
        self.__sheet.row_dimensions[_b_table_first_row].height = self._base_height
        self.__sheet.row_dimensions[_b_table_first_row + 1].height = self._base_height
        self.__sheet.row_dimensions[_b_table_first_row + 2].height = self._base_height

        self.__sheet.merge_cells(f"{get_column_letter(self.pos_of('bottomTableJoinLastCol')+1)}{_b_table_first_row + 1}:"
                                 f"{get_column_letter(self.pos_of('bottomTableJoinLastCol')+1)}{_b_table_first_row + 2}")

        self.__sheet.merge_cells(f"{self.pos_of('bottomTableJoinFirstCol')}{_b_table_first_row}:"
                                 f"{get_column_letter(self.pos_of('bottomTableJoinLastCol'))}{_b_table_first_row + 2}")

        # Вся экселька обернута в границы, поэтому необходимо
        left_border = copy(self.__sheet['U5'].border)
        right_border = copy(self.__sheet['A5'].border)
        for i in range(2, _b_table_first_row):
            self.__sheet[f"U{i}"].border = left_border
            self.__sheet[f"A{i}"].border = right_border

        self.__sheet.print_area = f"A1:{get_column_letter(self.pos_of('bottomTableJoinLastCol') + 1)}" \
                                  f"{_b_table_first_row + 2}"

    def save(self, path):
        self.__book.save(path)

    def set_cell_value(self, cell, value, style_key):
        style_cell = f"{self.pos_of(style_key)}{self.pos_of('first_row')}"
        self.__sheet[cell].value = value
        self.__sheet[cell].font = copy(self.__sheet[style_cell].font)
        self.__sheet[cell].border = copy(self.__sheet[style_cell].border)
        self.__sheet[cell].fill = copy(self.__sheet[style_cell].fill)
        self.__sheet[cell].alignment = copy(self.__sheet[style_cell].alignment)

        if type(value) in (int, float):
            split = str(value).split('.')
            if len(split) == 1:
                self.__sheet[cell].number_format = '0.00'
                return
            if len(split) > 1:
                strlen = len(str(value).split('.')[-1])
                self.__sheet[cell].number_format = f"0.{'0'*strlen}"

    @staticmethod
    def pos_of(key: str):
        __positions = {'customer': 'L2', 'obj_name': 'L4', 'accreditation': 'C7', 'test_title': 'B11', 'date': 'J31',
                       'bottomTableJoinFirstCol': 'K', 'bottomTableJoinLastCol': 20,
                       'labNum': 'B', 'skv': 'C', 'depth': 'D', 'type': 'E', 'first_row': 13, 'last_title_col': 13}
        return __positions[key]

    @staticmethod
    def form_tests_data(titles, data):
        """
        titles = ['Лаб. №', 'Скв. №', 'Глубина отбора, м', 'Наименование грунта', '<p>Референтное давление p<sub rise="0.5" size="5">ref</sub>]
        data = [['8-1', '8.0', '28,8', 'Супесь пластичная', '0,350', '100,8', '3,58'], ['']]
        """
        if len(titles) < 4:
            return {}

        _result = {}
        _additional = []

        for row in data:
            if len(row) == 1 and len(row[0]) > 0:
                _additional.append(row[0])
                continue
            if len(row) < 4:
                continue

            _result[row[0]] = {'skv': row[1], 'depth': row[2], 'type': row[3]}

            if 'params' not in _result[row[0]]:
                _result[row[0]]['params'] = {}

            for i in range(4, len(row)):
                title = titles[i].replace('<p>', '').replace('</p>', '').replace("<sub>", '')\
                    .replace('</sub>', '').replace('<sub rise="0.5" size="5">', '')\
                    .replace('<sup rise="-2" size="4">', 'E').replace('</sup>', '')\
                    .replace(' *10', '').replace('*10', '')
                title = title.replace('&alpha', 'α').replace('&beta', 'β').replace('&gamma', 'γ')\
                    .replace('&delta', 'δ')\
                    .replace('&epsilon', 'ε').replace('&zeta', 'ζ').replace('&eta', 'η')\
                    .replace('&theta', 'θ').replace('&iota', 'ι').replace('&kappa', 'κ')\
                    .replace('&lambda', 'λ').replace('&mu', 'μ').replace('&nu', 'ν')\
                    .replace('&xi', 'ξ').replace('&omikron', 'ο').replace('&pi', 'π') \
                    .replace('&rho', 'ρ').replace('&sigma', 'σ').replace('&tau', 'τ') \
                    .replace('&upsilon', 'υ').replace('&phi', 'φ').replace('&chi', 'χ') \
                    .replace('&psi', 'ψ').replace('&omega', 'ω')
                _result[row[0]]['params'][title] = row[i]

        return _result, _additional



def test_report():
    file = r"C:\\reports\\test_join.xlsx"
    writer = ReportXlsxSaver()
    writer.set_data(customer='ОАО «АМИГЭ»',
                    obj_name='Дополнительные инженерно-геологические изыскания на объекте: «Поисково-оценочная скважина № 5 Русановского лицензионного участка» в рамках договора по объекту «Бурение пяти инженерно-геологических скважин на шельфе Российской Федерации в 2021 году»,',
                    test_title='ВЕДОМОСТЬ РЕЗУЛЬТАТОВ ОПРЕДЕЛЕНИЯ ШТОРМОВОЙ РАЗЖИЖАЕМОСТИ ГРУНТОВ МЕТОДОМ ЦИКЛИЧЕСКИХ ТРЕХОСНЫХ СЖАТИЙ\n С РЕГУЛИРУЕМОЙ НАГРУЗКОЙ (ГОСТ 56353-2015, ASTM D5311/ASTM D5311M-13)',
                    date='14.03.2022',
                    tests_data={'22-63': {'skv': '1', 'depth': 22.1, 'type': 'Я просто камушек',
                                          'params': {"σ'1, кПа": 17,
                                                     "σ'3, кПа": 17,
                                                     "τ, кПа": 29,
                                                     "PPRmax, д.е.": 0.671,
                                                     "εmax, д.е.": 0.083,
                                                     "Nfail, ед.": "-",
                                                     "Результат испытания": "дин. неуст."}}},
                    additional_data=["Частота воздействия = 0,1 Гц",
                                     "Расчетная высота волны, м: 11,5",
                                     "Расчетное число циклов: 49371",
                                     "Плотность воды, кН/м3: 10"])
    writer.save("C:\\reports\\result.xlsx")

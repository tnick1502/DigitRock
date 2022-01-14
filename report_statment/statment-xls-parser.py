import re
from dataclasses import dataclass
from datetime import datetime
import os

from typing import Dict, List, Optional
import pickle

import xlrd
from xlrd import open_workbook


@dataclass
class ReportUnit:
    """Класс хранит одну строчку с выданными протоколами и ведомостями по объекту"""
    program: str = "unknown" # [plaxis/midas, TRM, mathCAD, dynamic, compression, triaxial]
    count: int = 0

    def __repr__(self):
        return f"[Количество: {self.count}, Программа: {self.program}]"


@dataclass
class Unit:
    """Класс хранит одну строчку с выданными протоколами и ведомостями по объекту"""
    object_number: str = None
    engineer: str = "unknown"
    report: ReportUnit = ReportUnit()
    statement: ReportUnit = ReportUnit()
    mechanics_statement: ReportUnit = ReportUnit()

    def __repr__(self):
        return f"\n\t\t\tОбъект: {self.object_number}, Исполнитель: {self.engineer}, Протоколы: {self.report}, Ведомости: {self.statement}, Ведомости по механике: {self.mechanics_statement}"

    def get_reports(self):
        return {'report': self.report, 'statement': self.statement, 'mechanics_statement': self.mechanics_statement}

class Statment:
    """Класс хранит всю ведомость выданных протоколов"""
    data: Dict[datetime, List[Unit]] = {}
    path: str = ""

    def __init__(self):
        self.data = {
            datetime(year=2019, month=1, day=1): [
                Unit(object_number="705-32", engineer="Михайлов А.И.",
                     report=ReportUnit(program="triaxial", count=5),
                     statement=ReportUnit(program="triaxial", count=5),
                     mechanics_statement=ReportUnit(program="TRM", count=5)),
                Unit(object_number="356-46", engineer="Жмылев Д.А.",
                     report=ReportUnit(program="triaxial", count=5),
                     statement=ReportUnit(program="triaxial", count=5),
                     mechanics_statement=ReportUnit(program="TRM", count=5))],
            datetime(year=2019, month=2, day=1): [
                Unit(object_number="705-32", engineer="Михайлов А.И.",
                     report=ReportUnit(program="triaxial", count=5),
                     statement=ReportUnit(program="triaxial", count=5),
                     mechanics_statement=ReportUnit(program="TRM", count=5)),
                Unit(object_number="356-46", engineer="Жмылев Д.А.",
                     report=ReportUnit(program="triaxial", count=5),
                     statement=ReportUnit(program="triaxial", count=5),
                     mechanics_statement=ReportUnit(program="TRM", count=5))]
        }

    def set_excel_statment_path(self, path: str):
        if os.path.isfile(path) and path.endswith("xls"):
            self.path = path
        else:
            print("Check file path")

    def update(self):
        """Подгрузка файла ведомости"""
        self.data = Statment.read_excel_statment(self.path)

    def dump(self, directory, name="statment.pickle"):
        dump_data = {
            "data": self.data,
            "path": self.path
        }
        with open(directory + "/" + name, "wb") as file:
            pickle.dump(dump_data, file)

    def load(self, file):
        with open(file, 'rb') as f:
            load_data = pickle.load(f)
        self.data = load_data["data"]
        self.path = load_data["path"]

    def set_data(self, data: 'Statment.data'):
        self.data = data

    def get_month_count(self, date: datetime):
        result: Dict = {}

        if date not in self.data.keys():
            return result

        for unit in self.data[date]:
            reports = unit.get_reports()
            for report in reports:
                if reports[report].program not in result.keys():
                    result[reports[report].program] = reports[report].count
                else:
                    result[reports[report].program] += reports[report].count

        return result

    @staticmethod
    def read_excel_statment(path: str) -> 'Statment.data':
        __result: 'Statment.data' = {}
        result: 'Statment.data' = {}

        # colors
        YELLOW = (255, 255, 0)
        GREEN_1 = (0, 128, 0)  # Дружелюбный зеленый
        GREEN_2 = (0, 255, 0)  # Вырвиглазный зеленый
        GREEN_3 = (51, 153, 102)  #
        GREEN_4 = (153, 204, 0)  #
        BLUE_1 = (0, 204, 255)  #
        BLUE_2 = (51, 204, 204)  #
        BLUE_3 = (51, 51, 153)  #
        BLUE_4 = (0, 51, 102)
        RED = (255, 0, 0)  # Продающий красный
        WHITE = None
        SPECIAL = 1

        def color(rgb: tuple):
            if rgb in [GREEN_1, GREEN_2, GREEN_3, GREEN_4]:
                return GREEN_2
            if rgb in [BLUE_1, BLUE_2, BLUE_3, BLUE_4]:
                return BLUE_1
            if rgb == RED:
                return RED
            if rgb != WHITE and rgb != (0, 0, 0):
                print(f"New Color: {rgb}")
            return WHITE

        # types
        PROGRAM_TYPE = {RED: 'plaxis/midas',
                        GREEN_2: 'compression',
                        BLUE_1: 'triaxial',
                        SPECIAL: 'mathCAD',
                        WHITE: 'TRM'}

        def program(color, special: Optional[bool] = False) -> str:
            """Returns program name by color

            Parameters
            ----------
                color
                    from color() func
                special: bool, default = False
                    set True for special type of PROGRAM_TYPE
            """
            if color not in PROGRAM_TYPE.keys():
                if special:
                    return PROGRAM_TYPE[SPECIAL]
                return PROGRAM_TYPE[WHITE]

            if special:
                if color == WHITE:
                    return PROGRAM_TYPE[SPECIAL]
            return PROGRAM_TYPE[color]

        # local columns for engineer
        N_COLS = 4
        '''cols count per engineer'''

        # columns shift from object column
        REP_COL = 1
        '''report column'''
        STAT_COL = 2
        '''statement column'''
        MECH_COL = 3
        '''mechanics_statement column'''

        # load book
        book = XlsBook(path)
        ncols = book.sheet.ncols + 1  # Natural ncols
        nrows = book.sheet.nrows + 1  # Natural nrows

        # fill-in engineers
        engineers = []
        engineers_row = 1
        for col in range(ncols):
            curr_engineer = book.cell_value(engineers_row, col)
            if len(curr_engineer) > 0:
                engineers.append(curr_engineer)
        if len(engineers) < 1:  # no engineers = no data
            return Statment.data

        def engineer(natural_col: int):
            """Returns engineer name by natural column index"""
            __col = natural_col - 1
            if __col // N_COLS >= len(engineers):
                return None
            return engineers[__col // N_COLS]

        # first month row
        start_row = 3

        # start date
        start_date = datetime(year=2017, month=2, day=1)
        last_date = None
        '''last defined date is the last date overall'''

        def next_month(_date):
            month = _date.month
            if month + 1 == 13:
                return datetime(year=_date.year + 1, month=1, day=1)
            return datetime(year=_date.year, month=month + 1, day=1)

        def prev_month(_date):
            month = _date.month
            if month - 1 == 0:
                return datetime(year=_date.year - 1, month=12, day=1)
            return datetime(year=_date.year, month=month - 1, day=1)

        # start parsing
        for row in range(start_row, nrows):

            # search for date (YELLOW line)
            dates = [*__result.keys()]
            if book.cell_back_color(row, 1) == YELLOW:

                # save the last date
                for col in range(1, ncols):
                    value = book.cell_value_date(row, col)
                    if value:
                        last_date = value

                # we fill in base dates to recalculate them later by last_date
                if dates:
                    __result[next_month(dates[-1])] = []
                else:
                    __result[start_date] = []
                continue

            if not dates:
                continue

            # we skip the summarize row
            if book.cell_value(row, 1) == "Сумма":
                continue

            # then parse columns for each engineer
            for col in range(1, ncols + 1, N_COLS):
                _object = book.cell_value(row, col).replace(' ', '')

                # first one should find out if there any object
                if not engineer(col) or not _object:
                    continue

                # we separate next ones from above cause of empty columns at end
                _report_count = book.cell_value_int(row, col + REP_COL)
                if not _report_count:
                    _report_type = program(WHITE, special=True)
                else:
                    _report_type = program(color(book.cell_front_color(row, col + REP_COL)), special=True)

                _statement_count = book.cell_value_int(row, col + STAT_COL)
                if not _statement_count:
                    _statement_type = program(WHITE)
                else:
                    _statement_type = program(color(book.cell_front_color(row, col + STAT_COL)))

                _mechanics_count = book.cell_value_int(row, col + MECH_COL)
                if not _mechanics_count:
                    _mechanics_type = program(WHITE)
                else:
                    _mechanics_type = program(color(book.cell_front_color(row, col + MECH_COL)))

                #
                __result[dates[-1]].append(Unit(object_number=str(_object), engineer=engineer(col),
                                           report=ReportUnit(program=_report_type,
                                                             count=_report_count),
                                           statement=ReportUnit(program=_statement_type,
                                                                count=_statement_count),
                                           mechanics_statement=ReportUnit(program=_mechanics_type,
                                                                          count=_mechanics_count)))
        # recalculate dates
        if last_date:
            start_date = last_date

            for i in range(len(__result.keys())):
                start_date = prev_month(start_date)

            for date in __result.keys():
                if len([*result.keys()]) > 0:
                    result[next_month([*result.keys()][-1])] = __result[date]
                else:
                    result[next_month(start_date)] = __result[date]

        return result

    def __repr__(self):
        return "\n".join(list(map(lambda key: f"{key.strftime('%d.%m.%Y')}: {repr(self.data[key])}", self.data)))


class XlsBook:
    """
    Convenience class for xlrd xls reader (only read mode)

    Note: Methods imputes operates with Natural columns and rows indexes
    """

    book = None
    sheet = None

    def __init__(self, path: str):
        self.set_book(path)

    def set_book(self, path: str):
        assert path.endswith('.xls'), 'Template should be .xls file format'
        self.book = open_workbook(path, formatting_info=True)
        self.set_sheet_by_index(0)

    def set_sheet_by_index(self, index: int):
        self.sheet = self.book.sheet_by_index(index)

    def cell_value(self, natural_row: int, natural_column: int):
        return self.sheet.cell(natural_row - 1, natural_column - 1).value

    def cell_value_int(self, natural_row: int, natural_column: int) -> int:
        value = self.cell_value(natural_row, natural_column)
        try:
            return int(value)
        except ValueError:
            return 0

    def cell_value_date(self, natural_row: int, natural_column: int):
        MARKS = ['/', ' ', ',']

        value = str(self.cell_value(natural_row, natural_column))

        if not value.replace(' ', ''):
            return None

        if self.cell_value_int(natural_row, natural_column):
            value = self.cell_value_int(natural_row, natural_column)
            return xlrd.xldate_as_datetime(value, 0)

        for mark in MARKS:
            if mark in value:
                value = value.replace(mark, '.')

        if re.fullmatch(r'[0-9]{2}[.][0-9]{2}[.][0-9]{4}', value):
            try:
                return datetime.strptime(value, '%d.%m.%Y').date()
            except ValueError:
                pass
        if re.fullmatch(r'[0-9]{2}[.][0-9]{2}[.][0-9]{2}', value):
            try:
                return datetime.strptime(value, '%d.%m.%y').date()
            except ValueError:
                pass

        return None



    def cell_back_color(self, natural_row: int, natural_column: int):
        row = natural_row - 1
        col = natural_column - 1
        cell = self.sheet.cell(row, col)
        xf = self.book.xf_list[cell.xf_index]
        if not xf.background:
            return None
        return self.__get_color(xf.background.pattern_colour_index)

    def cell_front_color(self, natural_row: int, natural_column: int):
        row = natural_row - 1
        col = natural_column - 1
        cell = self.sheet.cell(row, col)
        xf = self.book.xf_list[cell.xf_index]
        font = self.book.font_list[xf.font_index]
        if not font:
            return None
        return self.__get_color(font.colour_index)

    def __get_color(self, color_index: int):
        return self.book.colour_map.get(color_index)


if __name__ == "__main__":
    x = Statment()
    # print(x)
    x.set_excel_statment_path("C:/Users/Пользователь/Desktop/ПРОТОКОЛЫ+ведомости 2.xls")
    x.update()
    print(x.get_month_count(datetime(year=2022, month=1, day=1)))
    # total: int = 0
    # eng = 'Селиванова О.С.'
    # for _key in data.keys():
    #     for unit in data[_key]:
    #         if unit.engineer == eng:
    #             # print(unit)
    #             total += unit.report.count + unit.statement.count + unit.mechanics_statement.count
    # print(f"{eng}: {total}")

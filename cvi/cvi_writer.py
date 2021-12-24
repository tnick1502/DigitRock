import xlrd
import xlwt
import xlutils.copy
import numpy as np


def save_cvi_FC(file_path: str, data: dict):
    assert file_path.endswith('.xls'), 'File should be .xls file format'
    assert data.keys() is not None

    XLS_TEMPLATE = r"cvi/cvi_FC.xls"
    _in_Book = xlrd.open_workbook(XLS_TEMPLATE, formatting_info=True)
    _out_Book = xlutils.copy.copy(_in_Book)
    _out_Sheet = _out_Book.get_sheet(0)
    _col_formats: dict = {0: None}

    def set_cell(real_col: int, real_row: int, value, cache_col_format: bool = True):
        """ Change cell value without changing formatting. """
        assert real_col > 0, "Col number should be greater than 1"
        assert real_row > 0, "Col number should be greater than 1"
        col = real_col - 1
        row = real_row - 1
        previousCell = _get_cell(col, row)
        _out_Sheet.write(row, col, value)
        if previousCell:
            newCell = _get_cell(col, row)
            if newCell:
                newCell.xf_idx = previousCell.xf_idx
                if cache_col_format:
                    _col_formats[col] = previousCell.xf_idx

    def set_cell_f(real_col: int, real_row: int, value):
        """ Change cell value without changing formatting. """
        assert real_col > 0, "Col number should be greater than 1"
        assert real_row > 0, "Col number should be greater than 1"
        col = real_col - 1
        row = real_row - 1
        _out_Sheet.write(row, col, value)
        newCell = _get_cell(col, row)
        if newCell:
            newCell.xf_idx = _col_formats[col]

    def _get_cell(colIndex, rowIndex):
        row = _out_Sheet._Worksheet__rows.get(rowIndex)
        if not row:
            return None
        cell = row._Row__cells.get(colIndex)
        return cell

    COL = {'laboratory_number': 1, 'borehole': 2, 'ige': 3, 'depth': 4, "sample_composition": 6,
           'b': 9, 'main_stress': 16, 'strain': 14, 'sigma_3': 10}
    FIRST_ROW = 8

    set_cell(COL['laboratory_number'], FIRST_ROW, data['laboratory_number'])
    set_cell(COL['borehole'], FIRST_ROW, data['borehole'])
    set_cell(COL['ige'], FIRST_ROW, data['ige'])
    set_cell(COL['sample_composition'], FIRST_ROW, data['sample_composition'])
    set_cell(COL['b'], FIRST_ROW, data['b'])

    set_cell(COL['depth'], FIRST_ROW, data['depth'])
    set_cell(COL['depth'] + 1, FIRST_ROW, data['depth'] + 0.2)

    row = FIRST_ROW
    for test in data['test_data'].keys():
        if row == FIRST_ROW:
            set_cell(COL['sigma_3'], row, data['test_data'][test]['sigma_3'])
            set_cell(17, row, float(np.max(data['test_data'][test]['main_stress'])))
            set_cell(18, row, data['test_data'][test]['sigma_3'])
        else:
            set_cell_f(COL['sigma_3'], row, data['test_data'][test]['sigma_3'])
            set_cell_f(17, row, float(np.max(data['test_data'][test]['main_stress'])))
            set_cell_f(18, row, data['test_data'][test]['sigma_3'])

        for i in range(len(data['test_data'][test]['main_stress']) - 1):
            if row == FIRST_ROW:
                set_cell(COL['strain'], row, float(data['test_data'][test]['strain'][i]))
                set_cell(COL['main_stress'], row, float(data['test_data'][test]['main_stress'][i]))
            else:
                set_cell_f(COL['strain'], row, float(data['test_data'][test]['strain'][i]))
                set_cell_f(COL['main_stress'], row, float(data['test_data'][test]['main_stress'][i]))
            # next row in xls
            row = row + 1

    _out_Book.save(file_path)

def save_cvi_E(file_path: str, data: dict):
    assert file_path.endswith('.xls'), 'File should be .xls file format'
    assert data.keys() is not None

    XLS_TEMPLATE = r"cvi/cvi_E.xls"
    _in_Book = xlrd.open_workbook(XLS_TEMPLATE, formatting_info=True)
    _out_Book = xlutils.copy.copy(_in_Book)
    _out_Sheet = _out_Book.get_sheet(0)
    _col_formats: dict = {0: None}

    def set_cell(real_col: int, real_row: int, value, cache_col_format: bool = True):
        """ Change cell value without changing formatting. """
        assert real_col > 0, "Col number should be greater than 1"
        assert real_row > 0, "Col number should be greater than 1"
        col = real_col - 1
        row = real_row - 1
        previousCell = _get_cell(col, row)
        _out_Sheet.write(row, col, value)
        if previousCell:
            newCell = _get_cell(col, row)
            if newCell:
                newCell.xf_idx = previousCell.xf_idx
                if cache_col_format:
                    _col_formats[col] = previousCell.xf_idx

    def set_cell_f(real_col: int, real_row: int, value):
        """ Change cell value without changing formatting. """
        assert real_col > 0, "Col number should be greater than 1"
        assert real_row > 0, "Col number should be greater than 1"
        col = real_col - 1
        row = real_row - 1
        _out_Sheet.write(row, col, value)
        newCell = _get_cell(col, row)
        if newCell:
            newCell.xf_idx = _col_formats[col]

    def _get_cell(colIndex, rowIndex):
        row = _out_Sheet._Worksheet__rows.get(rowIndex)
        if not row:
            return None
        cell = row._Row__cells.get(colIndex)
        return cell

    COL = {
        'laboratory_number': 1,
        'borehole': 2,
        'ige': 3,
        'depth': 4,
        "sample_composition": 6,
        'b': 9,
        'main_stress': 16,
        'strain': 14,
        'sigma_3': 10,
        'sample_aria': 11,
        'stock_aria': 12,
        'volume_strain': 15
    }

    FIRST_ROW = 8

    set_cell(COL['laboratory_number'], FIRST_ROW, data['laboratory_number'])
    set_cell(COL['borehole'], FIRST_ROW, data['borehole'])
    set_cell(COL['ige'], FIRST_ROW, data['ige'])
    set_cell(COL['sample_composition'], FIRST_ROW, data['sample_composition'])
    set_cell(COL['b'], FIRST_ROW, data['b'])

    set_cell(COL['depth'], FIRST_ROW, data['depth'])
    set_cell(COL['depth'] + 1, FIRST_ROW, data['depth'] + 0.2)

    row = FIRST_ROW
    for test in data['test_data'].keys():
        if row == FIRST_ROW:
            set_cell(COL['sigma_3'], row, data['test_data'][test]['sigma_3'])
            set_cell(17, row, float(np.max(data['test_data'][test]['main_stress'])))
            set_cell(18, row, data['test_data'][test]['sigma_3'])
        else:
            set_cell_f(COL['sigma_3'], row, data['test_data'][test]['sigma_3'])
            set_cell_f(17, row, float(np.max(data['test_data'][test]['main_stress'])))
            set_cell_f(18, row, data['test_data'][test]['sigma_3'])

        for i in range(len(data['test_data'][test]['main_stress']) - 1):
            if row == FIRST_ROW:
                set_cell(COL['strain'], row, float(data['test_data'][test]['strain'][i]))
                set_cell(COL['main_stress'], row, float(data['test_data'][test]['main_stress'][i]))
                set_cell(COL['volume_strain'], row, float(data['test_data'][test]['volume_strain'][i]))
            else:
                set_cell_f(COL['strain'], row, float(data['test_data'][test]['strain'][i]))
                set_cell_f(COL['main_stress'], row, float(data['test_data'][test]['main_stress'][i]))
                set_cell_f(COL['volume_strain'], row, float(data['test_data'][test]['volume_strain'][i]))
            # next row in xls
            row = row + 1

    _out_Book.save(file_path)


def save_cvi_Cons(file_path: str, data: dict):
    assert file_path.endswith('.xls'), 'File should be .xls file format'
    assert data.keys() is not None

    XLS_TEMPLATE = r"cvi/cvi_cons.xls"
    _in_Book = xlrd.open_workbook(XLS_TEMPLATE, formatting_info=True)
    _out_Book = xlutils.copy.copy(_in_Book)
    _out_Sheet = _out_Book.get_sheet(0)
    _col_formats: dict = {0: None}

    def set_cell(real_col: int, real_row: int, value, cache_col_format: bool = True):
        """ Change cell value without changing formatting. """
        assert real_col > 0, "Col number should be greater than 1"
        assert real_row > 0, "Col number should be greater than 1"
        col = real_col - 1
        row = real_row - 1
        previousCell = _get_cell(col, row)
        _out_Sheet.write(row, col, value)
        if previousCell:
            newCell = _get_cell(col, row)
            if newCell:
                newCell.xf_idx = previousCell.xf_idx
                if cache_col_format:
                    _col_formats[col] = previousCell.xf_idx

    def set_cell_f(real_col: int, real_row: int, value):
        """ Change cell value without changing formatting. """
        assert real_col > 0, "Col number should be greater than 1"
        assert real_row > 0, "Col number should be greater than 1"
        col = real_col - 1
        row = real_row - 1
        _out_Sheet.write(row, col, value)
        newCell = _get_cell(col, row)
        if newCell:
            newCell.xf_idx = _col_formats[col]

    def _get_cell(colIndex, rowIndex):
        row = _out_Sheet._Worksheet__rows.get(rowIndex)
        if not row:
            return None
        cell = row._Row__cells.get(colIndex)
        return cell

    COL = {'laboratory_number': 1, 'borehole': 2, 'ige': 3, 'depth': 4, "sample_composition": 6,
           'b': 9, 'vertical_pressure': 10, 'vertical_stress': 11}
    FIRST_ROW = 8

    set_cell(COL['laboratory_number'], FIRST_ROW, data['laboratory_number'])
    set_cell(COL['borehole'], FIRST_ROW, data['borehole'])
    set_cell(COL['sample_composition'], FIRST_ROW, data['sample_composition'])
    set_cell(COL['b'], FIRST_ROW, data['b'])

    set_cell(COL['depth'], FIRST_ROW, data['depth'])
    set_cell(COL['depth'] + 1, FIRST_ROW, data['depth'] + 0.2)

    row = FIRST_ROW
    for test in data['test_data'].keys():
        if row == FIRST_ROW:
            set_cell(COL['vertical_pressure'], row, float(data['test_data'][test]['vertical_pressure']))
        else:
            set_cell_f(COL['vertical_pressure'], row, float(data['test_data'][test]['vertical_pressure']))

        for i in range(len(data['test_data'][test]['vertical_stress'])):
            if row == FIRST_ROW:
                set_cell(COL['vertical_stress'], row, float(data['test_data'][test]['vertical_stress'][i]))
            else:
                set_cell_f(COL['vertical_stress'], row, float(data['test_data'][test]['vertical_stress'][i]))
            # next row in xls
            row = row + 1

    _out_Book.save(file_path)


#save_cvi(r"labNo ЦВИ.xls", data)

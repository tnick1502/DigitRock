import xlrd

path = r"C:\Users\Пользователь\Desktop\984-21 Паромный причал - мех.xls"

from excel_statment.position_configs import GeneralDataColumns

x = xlrd.open_workbook(path, formatting_info=True)
sheet = x.sheet_by_index(0)
for key in GeneralDataColumns:
    print(f"{key}: {sheet.cell(*GeneralDataColumns[key][1]).value}")

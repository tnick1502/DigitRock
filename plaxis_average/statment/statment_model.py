import pandas as pd
import os

from plaxis_average.statment.properties import Properties
from plaxis_average.statment.params import averaged_params

class AveragedStatment:
    data: dict = {}
    excel_path: str = ''
    dataframe: pd.DataFrame
    EGES: dict = {}

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(AveragedStatment, cls).__new__(cls)
        return cls.instance

    def setExcelFile(self, path: str) -> None:
        """Открытие и загрузка файла excel
            :argument path: путь к файлу
            :return None
        """
        if not all([os.path.exists(path), (path.endswith('.xls') or path.endswith('.xlsx'))]):
            raise Exception("Wrong file excel")

        self.data = {}

        self.excel_path = path

        df = pd.read_excel(self.excel_path, sheet_name='Лист1', usecols="A:BK", skiprows=[0, 1, 3])
        self.dataframe = df[df['Unnamed: 0'].notna()]

        for i, laboratory_number in enumerate(self.dataframe['Unnamed: 0']):
            self.data[laboratory_number] = Properties()
            self.data[laboratory_number].defineProperties(data_frame=self.dataframe, number=i)

        self.splitEGE()

    def getData(self) -> dict:
        """Получение всех параметров

            :return словарь с ключам лабнмеров, по значением в которых словарь с оригинальными
            зачениями параметров по ключу origin_data и измененными по ключу modified_data
        """
        return {
            key: self.data[key].getData() for key in self.data
        }

    def splitEGE(self):
        self.EGES = {}

        for test in self:
            EGE = self[test].EGE
            if self.EGES.get(EGE, None):
                self.EGES[EGE].append(test)
            else:
                self.EGES[EGE] = [test]
        print(self.EGES)

    def getAvarange(self):
        result_EGES = {}

        for EGE in self.EGES:
            params = {
                param: {
                    'count': 0,
                    'summury': 0,
                } for param in averaged_params
            }

            for test in self.EGES[EGE]:
                for param in averaged_params:
                    value = getattr(self[test], param)
                    if value is not None:
                        params[param]['count'] += 1
                        params[param]['summury'] += getattr(self[test], param)

            result = {}
            for param in params:
                if params[param]['count']:
                    result[param] = round(params[param]['summury'] / params[param]['count'], 3)
                else:
                    result[param] = None

            result_EGES[EGE] = result

        return result_EGES

    def save_excel(self):
        data = self.getAvarange()
        keys = list(data.keys())
        print(data)

        matrix = [data[key].values() for key in keys]
        df1 = pd.DataFrame(matrix,
                           index=keys,
                           columns=list(data[keys[0]]))

        path = os.path.split(self.excel_path)[0] + '/Усредненные параметры по ИГЭ.xlsx'
        df1.to_excel(path)

    def __iter__(self):
        for key in self.data:
            yield key

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        if not key in list(self.data.keys()):
            return KeyError(f"No test with key {key}")
        return self.data[key]

    def __str__(self):
        data = '\n'.join([''] + [f'{key}: {self.data[key].getData()}' for key in self.data])
        return f'''Путь: {self.excel_path}

Данные:
{data}
'''

if __name__ == '__main__':
    s = AveragedStatment()
    s.setExcelFile(r"C:\Users\Пользователь\Desktop\1.xls")
    print(s.getAvarange())


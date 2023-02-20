import json

path = "Z:/Digitrock/version_log.json"
local = 'version_control/version_log.json'

def open_json(path: str) -> dict:
    """Считывание json файла в словарь"""
    with open(path, 'r', encoding='utf-8') as file:
        json_data = json.load(file)
    return json_data

def write_json(path: str, data: dict) -> None:
    """Запись словаря в json файл. Если файл отсутствует, то создается новый"""
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False)

def add_data(version: str, text: str):

    def write(file):
        file_data = open_json(file)
        if file_data.get(version, None) is None:
            file_data[version] = text
            write_json(file, file_data)
            print(f"Сhanges saved in local successfully in {file}")
        else:
            print(f"This version already exists in {file}")

    for file in [local, path]:
        write(file)


def get_actual_version() -> float:
    """Получение актуальной версии программы"""
    data = open_json(path)
    return "{:.2f}".format(max([float(i) for i in list(data.keys())]))

def test_version(version: float) -> bool:
    """Проверка совпадения актуальной версии программы с текущей версией"""
    return True if float(version) == float(get_actual_version()) else False

if __name__ == "__main__":
    add_data("3.68", """
    1. В сейсмике параметр MSF убран из расчетов и из отчета
    2. Добавлена возможность выдавать отчеты с меньшим количеством исполнителей
    3. Добавлен тектовый виджет усреднения кривых для ИГЭ
    4. Добавлен виджет просмотра бекапов
    5. Влияние экспоненты при построении девиаторной кривой немного стало больше, добавлен ползунок влияния экспоненты
    """)

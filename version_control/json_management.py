import json

path = "Z:/Digitrock/version_log.json"
local = 'version_control/version_log.json'
#local = 'c://projects/DigitRock/version_control/version_log.json'

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
    add_data("3.77", """
    1. Убраны точки из протокола E
    2. Повышена точность Kd
    3. Более стабильное сохранение всех протоколов
    4. Доработка отчетов сейсмо и штормовой прочности
    5. Доработка модуля усреднения кривых
    6. Выгрузка данных сводной ведомости смещена на 2 ячейки вправо
    """)

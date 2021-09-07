import json
from version_control.configs import path, actual_version

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
    file_path = path
    file_data = open_json(file_path)
    if file_data.get(version, None) is not None:
        file_data[version] = text
        write_json(file_path, file_data)
        print("Сhanges saved successfully")
    else:
        print("This version already exists")

def get_actual_version() -> float:
    """Получение актуальной версии программы"""
    data = open_json(path)
    return max([float(i) for i in list(data.keys())])

def test_version(version: float) -> bool:
    """Проверка совпадения актуальной версии программы с текущей версией"""
    return True if version == get_actual_version() else False

if __name__ == "__main__":
    print(get_actual_version())

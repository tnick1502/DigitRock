import json

path = "Z:/НАУКА/Разработка/!Программы/Digitrock/version_log.json"

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
    file_data = open_json(path)
    if file_data.get(version, None) is None:
        file_data[version] = text
        write_json(path, file_data)
        print("Сhanges saved successfully")
    else:
        print("This version already exists")

def get_actual_version() -> float:
    """Получение актуальной версии программы"""
    data = open_json(path)
    return "{:.2f}".format(max([float(i) for i in list(data.keys())]))

def test_version(version: float) -> bool:
    """Проверка совпадения актуальной версии программы с текущей версией"""
    return True if float(version) == float(get_actual_version()) else False

if __name__ == "__main__":
    #write_json(path, {"3.09": """1. Добавлен ЦВИ для E и FC
#2. добавлена зависимость Kd из тз
#3. Новый отчет по вибро с 3мя опытами"""})

    #add_data("2.10", "Добавлена возможность обработки 4х кругов мора из ведомости. Размер теперь автоопределяется из грансостава, также можно в ручном режиме задать 150х300. Теперь в отчет идет дата из 239 столбца, если она заполнена, если не заполнена - дата берется как обычно")


    add_data("3.51", """
1. Добавлен режим построения и дополнительные виды протоколов для прогноза виброползучести на 50 и 100 лет
""")

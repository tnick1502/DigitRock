import os

def program_data_dir(path: str):
    """Проверка наличия и создание пути в случае отсутствия"""

    check_array = os.path.normcase(path).split("\\")
    check_path = check_array[0]

    for subdirectory in check_array[1:]:
        check_path = f"{check_path}/{subdirectory}"
        if not os.path.isdir(check_path):
            os.mkdir(check_path)

program_data_dir("C:/111/111/1111/11111/11111")
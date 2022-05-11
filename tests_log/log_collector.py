import os
import shutil

def get_all_files(rootdir: str, part_file_name: str) -> list:
    """
    Функция для поиска файлов по части названия
    :param rootdir: Корневая папка для поиска
    :param part_file_name: Часть имени файла для поиска
    :return: Список полных путей к файлам
    """
    file_paths = []
    for dirpath, dirs, files in os.walk(rootdir):
        for filename in files:
            if part_file_name in filename:
                file_paths.append(os.path.join(dirpath, filename))
    return file_paths

def create_log_path(path: str):
    """
    Функция создает папке, если папка уже есть, то удаляет и создает новую
    :param path:
    :return:
    """
    if not os.path.exists(path):
        os.mkdir(path)
    else:
        shutil.rmtree(path)
        os.mkdir(path)

def copy_and_rename(logs: list, log_path: str):
    """
    Функция для переименования и копирования файла. Вторую часть имени берет из папки нахождения файла
    :param logs:
    :param log_path:
    :return:
    """
    for log in logs:
        copy_log_path = os.path.join(log_path, os.path.split(log)[-1])
        shutil.copy(log, copy_log_path)

        s = log.split("\\")
        try:
            float(s[-2])
        except ValueError:
            lab_number = s[-2]
            postfix = ""
        else:
            lab_number = s[-3]
            postfix = " " + s[-2]

        new_name = os.path.join(os.path.split(copy_log_path)[0], f"{lab_number}{postfix}.txt")

        os.rename(copy_log_path, new_name)

def find_logs(root_path: str, log_path_name: str, part_file_name: str):
    log_path = os.path.join(root_path, log_path_name)
    create_log_path(log_path)
    logs = get_all_files(root_path, part_file_name)
    copy_and_rename(logs, log_path)

if __name__ == "__main__":
    find_logs(root_path=r"C:\Users\Пользователь\Desktop\Резонансная колонка", log_path_name="логи", part_file_name="RCCT_ModulusTable.txt")


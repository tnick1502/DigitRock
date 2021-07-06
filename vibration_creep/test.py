
def openfile(file_path, columns_key, separator="\t", index_start_string=1):
    """ункция считывания данных с файла прибора
    arguments:
        file_path - Путь к файлу
        columns_key - список с именами столбцов
        separator - разделитель
        begin - строка начала считывания"""
    # Открываем файл
    f = open(file_path)
    # Счиитываем все строки
    lines = f.readlines()
    f.close()

    read_data = {}

    for key in columns_key:  # по нужным столбцам
        index = (lines[0].split(separator).index(key))
        try:
            read_data[key] = list(map(lambda x: float(x.split(separator)[index]), lines[index_start_string:]))
        except ValueError: # когда столбец не число
            read_data[key] = list(map(lambda x: x.split(separator)[index], lines[index_start_string:]))

    return read_data

print(int(3.9))
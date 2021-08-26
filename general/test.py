import os

path = 'C:/Users/Пользователь/Desktop/Тест/Девиаторное нагружение/Архив'

c_fi_E_PropertyPosition = {
    "Трёхосное сжатие (E)": [["BI", "BJ", "BK"], [60, 61, 62]],
    "Трёхосное сжатие (F, C)": [["BF", "BG", "BH"], [57, 58, 59]],
    "Трёхосное сжатие (F, C, E)": [["BC", "BD", "BE"], [54, 55, 56]],
    "Трёхосное сжатие с разгрузкой": [["BL", "BM", "BN"], [63, 64, 65]],
    "Сейсморазжижение": [["BY", "BZ", "CA"], [76, 77, 78]],
    "Штормовое разжижение": [["BY", "BZ", "CA"], [76, 77, 78]],
    "Виброползучесть": [["BS", "BT", "BU"], [70, 71, 72]],
    "Резонансная колонка": [["BC", "BD", "BE"], [54, 55, 56]]}

def reprocessing(path):
    params = {}

    def folders_in_path(path):
        return [i for i in os.listdir(path) if os.path.isdir(os.path.join(path, i))]

    def find_test(path, test_name):
        test_path = os.path.join(path, test_name)
        return test_path if os.path.isfile(test_path) else None

    def find_tests(path, test_name):
        internal_paths = [os.path.join(path, x) for x in folders_in_path(path)]
        return [find_test(x, test_name) for x in internal_paths]

    laboratory_numbers = folders_in_path(path)

    for laboratory_number in laboratory_numbers:
        params[laboratory_number] = {
            "E": find_test(os.path.join(path, laboratory_number), "Test.1.log"),
            "FC": find_tests(os.path.join(path, laboratory_number), "Test.1.log")
        }

    return params


print(reprocessing(path))
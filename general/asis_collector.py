import os
import shutil
import xlwt
import glob
import csv


class AsisCollector:
    """
        Собирает готовые логи приборов в отдельную папку и создает их .xls версии.

        Методы:
        collect_logs - Основной метод, которым и необходимо пользоваться. Возвращает коды ошибок. См. описание метода.

        Папка с логами определяется по наличию папки "Архив [Тип испытания]". Папка Архив МДГТ игнорируется.

    """

    print_logs = False
    'В значении True печатает в консоль ошибки'

    path = ''
    'Путь до рабочей папки. Подается в `collect_logs`'
    asis_dir = ''
    'Путь до папки, в которую будут собираться логи АСИС '

    ARCHIVE_NAME = 'Архив МДГТ'
    'Название папки для подпапки с логами АСИС'

    ASIS_NAME = 'Логи АСИС'
    'Название подпапки с логами'

    def collect_logs(self, path: 'str', print_logs=False) -> 'float':
        """
        Собирает готовые логи асис в папку и создает их .xls версии.

        Структура пути `path` должна соответствовать:

        `path`
            "Архив [Тип испытания]"
                [Номера проб]
                    [Кривая 1]
                        ''.log
                    [Кривая 2]
                        ''.log
                    [Кривая 3]
                        ''.log
                    ''.log ?

        Логи собираются из папок `path`/"Архив [Тип испытания]"/[Номер пробы]/[Кривая #]/''.log
        И копируются в соответствующую папку для логов АСИС с названием `[Номер пробы] Кривая #`

        Коды ошибок:
            - `1` : Сбор прошёл успешно
            - `0` : Выбраного пути `path` не существует
            - `-1` : Папки "Архив [Тип испытания]" не существует
            - `-2' : Список проб пустой
            - `-3` : Ошибка очистки папки Логи АСИС
            - `-4` : Не найден файл .log в папке c пробой

        Прочие ошибки НЕ обрабатываются, для их обработки необходимо обернуть эту функцию в свой обработчик.

        :param path: Путь до рабочей папки, в которой находится папка "Архив [Тип испытания]"
        :param print_logs: Флаг печати текста ошибок в консоль

        :returns: Код результата сбора логов.
        """

        self.print_logs = print_logs
        self.path = path

        # Проверка существования поданного пути
        if not path or path.replace(' ', '') == '' or not os.path.isdir(path):
            self._log('Папки не существует')
            return 0

        # Получение структуры и проверка наличия в ней папки "Архив [Тип испытания]"
        structure = os.listdir(path)
        archive_folder, ind = self._find_first_str_in_list('Архив', structure)
        if ind == -1:
            self._log('Папки "Архив [Тип испытания]" не существует')
            return -1

        # Определяем папки с пробами
        probes_folder = f'{path}/{archive_folder}'
        probes = os.listdir(probes_folder)
        if len(probes) == 0:
            self._log('Список проб пустой')
            return -2

        # Создает папку `self.ARCHIVE_NAME`
        archive_mdgt_dir = f'{path}/{self.ARCHIVE_NAME}'
        if not os.path.isdir(archive_mdgt_dir):
            os.mkdir(archive_mdgt_dir)

        # Создаем папку `self.ASIS_NAME` если ее нет, если папка есть ОЧИЩАЕМ ЕЕ
        asis_dir = f'{archive_mdgt_dir}/{self.ASIS_NAME}'
        if not os.path.isdir(asis_dir):
            os.mkdir(asis_dir)
        else:
            for filename in os.listdir(asis_dir):
                file_path = os.path.join(asis_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    self._log('Ошибка очистки папки Логи АСИС')
                    self._log('Failed to delete %s. Reason: %s' % (file_path, e))
                    return -3
        self.asis_dir = asis_dir

        # Производим копирование для каждой пробы
        for probe in probes:
            # Получаем список кривых в отсортированном виде
            curves = self._find_curves(f'{probes_folder}/{probe}')

            # Для кажой кривой производим копирование файла с названием по порядку
            for num, curve in enumerate(curves):
                curve_path = f'{probes_folder}/{probe}/{curve}'
                logs, logs_ind = self._find_first_str_in_list('.log', os.listdir(curve_path))
                if logs_ind == -1:
                    self._log(f'Не найден файл .log в папке {curve_path}/{logs}')
                    return -4
                self._copy_to_asis(f'{curve_path}/{logs}', f'{probe} Кривая {num + 1}')

            # В некоторых опытах существует 4 кривая на том же уровне что и папки с кривыми
            E_curve, E_curve_ind = self._find_first_str_in_list('.log', os.listdir(f'{probes_folder}/{probe}'))
            if E_curve_ind != -1:
                self._copy_to_asis(f'{probes_folder}/{probe}/{E_curve}', f'{probe} Кривая 4')

        self._log('Копирование успешно')
        return 1

    def _log(self, val):
        if self.print_logs:
            print(val)

    def _copy_to_asis(self, file_path, new_name):
        """
            Копирует файл `file_path` в путь `asis_dir` с названием `new_name`.log и создает его .xls копию.
        """
        new_file_path = os.path.join(self.asis_dir, f'{new_name}.txt')
        shutil.copy(file_path, new_file_path)

        for csvfile in glob.glob(new_file_path):
            workbook = xlwt.Workbook(f"{self.asis_dir}/{new_name}.xls")
            worksheet = workbook.add_sheet('Sheet 1', cell_overwrite_ok=True)
            with open(csvfile, 'rt') as f:
                reader = csv.reader(f, delimiter='\t')
                for r, row in enumerate(reader):
                    for c, col in enumerate(row):
                        worksheet.write(r, c, col)
            workbook.save(f"{self.asis_dir}/{new_name}.xls")

    @staticmethod
    def _find_curves(path):
        """
            Производит поиск папок по пути `path` и возвращает их список в отсортированном виде.
        """
        structure = []
        for item in os.listdir(path):
            if os.path.isdir(f'{path}/{item}'):
                structure.append(item)
        structure.sort()

        return structure

    @staticmethod
    def _find_first_str_in_list(string, string_list):
        """
            Находит ПЕРВОЕ вхождение подстроки `string` в список строк `string_list`.

            Возвращает соответствующую строку и ее индекс в `string_list`.
             Возвращает -1 в индексе если подстрока не найдена.
        """
        if len(string_list) == 0:
            return '', -1
        for ind, item in enumerate(string_list):
            if string in item and item != 'Архив МДГТ':
                return item, ind
        return '', -1





if __name__ == '__main__':
    curr_dir = os.curdir
    collect_logs(path=curr_dir)

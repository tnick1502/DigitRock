import os
import shutil
from typing import List, Dict
import logging
from thrd.socket_thd import send_to_server

import progressbar
from PyPDF4 import PdfFileWriter, PdfFileReader
import json
from loggers.logger import app_logger

def read_json_file(path):
    """Читает JSON в словарь питон"""
    with open(path, 'r', encoding='utf-8') as file:
        json_data = json.load(file)
    return json_data

class WaterMarks:
    """Модель генерации ватермарок"""
    # Выбранная папка с отчетами
    _initial_directory: str = ""

    # Папка с отчетами с ватермаркой
    _modified_directory: str = ""

    # Все PDF файлы из self._initial_directory
    _files: List[str] = []

    # Все файлы ватермарок
    #_watermark: str = "pdf_watermark/5.pdf"

    try:
        _watermark: Dict = {
            "vertical": "pdf_watermark/vertical.pdf",
            "horizontal": "pdf_watermark/horizontal.pdf"
        }

        _watermark_config: Dict = read_json_file("pdf_watermark/configs.json")
    except FileNotFoundError:
        _watermark: Dict = {
            "vertical": "vertical.pdf",
            "horizontal": "horizontal.pdf"
        }

        _watermark_config: Dict = read_json_file("configs.json")

    def __init__(self, directory: str, port: int = 5001):
        self.set_initial_directory(directory)
        self._port = port

    def set_initial_directory(self, directory: str) -> None:
        """Назначение начальной директории"""

        assert os.path.exists(directory), "Не создана папка с отчетами"

        self._initial_directory = directory
        app_logger.info("pdf_watermark: initial directory: {}".format(directory))
        self._make_modified_directory()
        self._files = WaterMarks._get_files(self._initial_directory)
        app_logger.info("pdf_watermark: {} files were found".format(len(self._files)))

        assert len(self._files), "В папке отсутствуют отчеты"

    def get_initial_directory(self) -> str:
        return self._initial_directory

    def _make_modified_directory(self) -> None:
        """Создадние папки с модифицированными отчетами"""
        if self._initial_directory:
            modified_directory = os.path.join(self._initial_directory, "modified")
            if os.path.exists(modified_directory):
                shutil.rmtree(modified_directory)
            try:
                os.mkdir(modified_directory)
                self._modified_directory = modified_directory
            except OSError:
                app_logger.info("pdf_watermark: failed to create a directory of modified reports")

    def process(self) -> bool:
        """Метод обработки директории, ищет все файлы"""
        if self._files:
            send_to_server(self._port, {"window_title": "Процесс ..."})
            send_to_server(self._port, {"label": "Обработка PDF отчетов..."})
            send_to_server(self._port, {"maximum": len(self._files)})

            for i, file in enumerate(self._files):
                file_name = os.path.split(file)[-1]
                WaterMarks.set_watermark(file, os.path.join(self._modified_directory, file_name),
                                         self._watermark_config, self._watermark)
                send_to_server(self._port, {"value": i + 1})

            app_logger.info("pdf_watermark: {} files processed successfully".format(len(self._files)))
            send_to_server(self._port, {"break": True})

            return True
        else:
            return False


    @staticmethod
    def set_watermark(input_pdf: str, output_pdf: str, _watermark_config: Dict, watermark: Dict) -> None:
        """ Dставка Ватермарки
            :param input_pdf: Исходный файл (путь)
            :param output_pdf: Итоговый файл (путь)
            :param watermark: Ватермарка (путь)
            Все три должны быть с форматом .PDF

            :return: None"""
        pdf_reader = PdfFileReader(input_pdf)
        w, h = pdf_reader.getPage(0).mediaBox[2], pdf_reader.getPage(0).mediaBox[3]
        #if pdf_reader.getPage(0).get('/Rotate') == 0:
        if h > w:
            watermark = watermark["vertical"]
        else:
            watermark = watermark["horizontal"]
        watermark_instance = PdfFileReader(watermark)
        watermark_page = watermark_instance.getPage(0)
        pdf_writer = PdfFileWriter()
        for page in range(pdf_reader.getNumPages()):
            page = pdf_reader.getPage(page)
            page.mergePage(watermark_page)
            pdf_writer.addPage(page)

        with open(output_pdf, 'wb') as out:
            pdf_writer.write(out)

    @staticmethod
    def _get_files(_initial_directory: str) -> List[str]:
        """Метод поиска всех файлов с расширением PDF в каталоге self._initial_directory"""
        file_paths = []
        for dirpath, dirs, files in os.walk(_initial_directory):
            for filename in files:
                if (filename.upper().endswith(".PDF")):
                    file_paths.append(os.path.join(dirpath, filename))

        if len(file_paths) == 0:
            app_logger.info("pdf_watermark: Не найдено файфлов в расширением PDF")

        return file_paths

if __name__ == "__main__":
    WM = WaterMarks()
    WM.set_initial_directory("Example")
    WM.process()



import hashlib
def hash_id(labolatory_number: str, object_number: str):
    hash_object = hashlib.sha1(f"{object_number} {labolatory_number}".encode("utf-8"))
    return hash_object.hexdigest()


import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QProgressDialog

from vibration_creep.vibration_creep_widgets import VibrationCreepSoilTestApp, __version__
from version_control.json_management import test_version, get_actual_version
from version_control.configs import actual_version
from loggers.logger import app_logger



if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    #app.setStyleSheet("QLabel{font-size: 14pt;}")
    progress = QProgressDialog("Сохранение протоколов...", "Процесс сохранения:", 0, 1)
    progress.setCancelButton(None)
    #progress.setWindowFlags(progress.windowFlags() & ~Qt.WindowCloseButtonHint)
    #progress.setWindowModality(Qt.WindowModal)
    progress.setValue(0)
    progress.show()
    sys.exit(app.exec_())
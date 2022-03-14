from PyQt5.QtWidgets import QApplication
from app_modules.widget import WaterMartWidget
import sys
import logging

#logging.basicConfig(level="INFO")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = WaterMartWidget()

    win.show()
    sys.exit(app.exec_())


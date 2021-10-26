from PyQt5.QtWidgets import QTextEdit, QApplication
import sys
import logging

app_logger = logging.getLogger("app_logger")

handler = logging.Handler()
handler.setLevel(logging.INFO)
app_logger.addHandler(handler)
f = logging.Formatter(fmt='%(message)s')
handler.setFormatter(f)

app = QApplication(sys.argv)

app.setStyle('Fusion')
ex = QTextEdit()
handler.emit = lambda record: ex.append(handler.format(record))
app_logger.info("dgf")

ex.show()
sys.exit(app.exec_())



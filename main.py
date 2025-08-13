# main.py
import sys
from PyQt5 import QtCore, QtWidgets
from timer  import TaskbarTimer
from logging_config import setup_logging

if __name__ == "__main__":
    setup_logging()
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    timer = TaskbarTimer()
    timer.show()
    sys.exit(app.exec_())

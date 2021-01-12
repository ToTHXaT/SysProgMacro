import sys
from PyQt5 import QtCore, QtGui, QtWidgets, QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem
from src.ui.main_w import Ui_MainWindow
from pprint import pprint
from src.handlers import setup_handlers

from typing import *
from dataclasses import dataclass


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)

    win = QtWidgets.QMainWindow()

    mw = Ui_MainWindow()
    mw.setupUi(win)

    setup_handlers(mw)

    win.show()

    sys.exit(app.exec_())

    import src.FPass
    import src.SPass

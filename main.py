import sys
import argparse
from PyQt5 import QtCore, QtGui, QtWidgets, QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem
from src.ui.main_w import Ui_MainWindow
from pprint import pprint
from src.handlers import setup_handlers, cli_run

from typing import *
from dataclasses import dataclass


def main():
    import argparse

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--input_file', metavar='INPUT_FILE', type=str, default='console',
                        help='Path to a file with source code')
    parser.add_argument('--output_file', metavar='OUTPUT_FILE', type=str, default='console',
                        help='Path to a file to dump result to')

    args = parser.parse_args()

    if args.input_file == 'console' and args.output_file == 'console':

        app = QtWidgets.QApplication(sys.argv)

        win = QtWidgets.QMainWindow()

        mw = Ui_MainWindow()
        mw.setupUi(win)

        setup_handlers(mw)

        win.show()

        sys.exit(app.exec_())
    else:
        with open(args.input_file, 'r') as file:
            src = file.read()
            output = cli_run(src)

        if not output:
            return

        if args.output_file == 'console':
            print(output)
        else:
            with open(args.output_file, 'w') as file:
                file.write('\n'.join(output))


if __name__ == '__main__':
    main()


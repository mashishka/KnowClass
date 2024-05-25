import logging as log
import sys

from PyQt5 import QtWidgets

from ui.pyui.MainWindow import MainUI

if __name__ == "__main__":

    # уровень логирования для приложения
    log.getLogger().setLevel(log.DEBUG)
    app = QtWidgets.QApplication(sys.argv)
    main = MainUI()
    main.show()
    app.exec_()

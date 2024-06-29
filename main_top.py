from pathlib import Path
import logging as log
import sys

from PyQt5 import QtWidgets

from ui.pyui.MainWindow import MainUI
import ui.pyui.ui_path as ui_path
if __name__ == "__main__":
    ui_path.PATH_TO_UI = (Path(__file__).parent.absolute() / "ui/widgets").as_posix()
    # уровень логирования для приложения
    log.getLogger().setLevel(log.DEBUG)
    app = QtWidgets.QApplication(sys.argv)
    main = MainUI()
    main.showMaximized()
    app.exec_()

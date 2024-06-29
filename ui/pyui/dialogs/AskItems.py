from enum import Enum

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QDir, QSettings, QModelIndex, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi  # type: ignore

import ui.pyui.ui_path as ui_path


class AskItems(QDialog):
    ask_label: QLabel
    items_combo: QComboBox
    button_box: QDialogButtonBox

    cur_num: int | float | None = None

    def __init__(self, parent, title: str, ask_text: str, items: list[str]):
        super().__init__(parent)
        loadUi(ui_path.PATH_TO_UI+"/dialogs/ask_items.ui", self)

        self.setWindowTitle(title)
        self.ask_label.setText(ask_text)

        self.items_combo.addItems(items)

    @staticmethod
    def get_item(parent, title: str, ask_text: str, items: list[str]):
        dlg = AskItems(parent, title, ask_text, items)
        done = dlg.exec_() == QDialog.Accepted
        return dlg.items_combo.currentText(), done

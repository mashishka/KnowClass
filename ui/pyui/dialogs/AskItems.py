from enum import Enum

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QDir, QSettings, QModelIndex, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi  # type: ignore


class AskItems(QDialog):
    ask_label: QLabel
    items_combo: QComboBox
    button_box: QDialogButtonBox

    cur_num: int | float | None = None

    def __init__(self, parent, title: str, ask_text: str, items: list[str]):
        super().__init__(parent)
        loadUi("ui/widgets/dialogs/ask_items.ui", self)

        self.setWindowTitle(title)
        self.ask_label.setText(ask_text)

        # for item in items:
        self.items_combo.addItems(items)

        # if min is not None:
        #     self.int_field.setMinimum(min)

        # self.cur_num = cur_num

        # if isinstance(self.cur_num, int):
        #     self.int_field.setValue(self.cur_num)
        # elif isinstance(self.cur_num, float):
        #     self.double_field.setValue(self.cur_num)

        # if mode == AskNumberType.only_int:
        #     self.double_field.setVisible(False)
        # elif mode == AskNumberType.only_double:
        #     self.int_field.setVisible(False)

    @staticmethod
    def get_item(parent, title: str, ask_text: str, items: list[str]):
        dlg = AskItems(parent, title, ask_text, items)
        done = dlg.exec_() == QDialog.Accepted
        return dlg.items_combo.currentText(), done

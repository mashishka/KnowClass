from enum import Enum

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QDir, QSettings, QModelIndex, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi  # type: ignore


class AskNumberType(Enum):
    only_int = "int"
    only_double = "double"


class AskNumber(QDialog):
    ask_label: QLabel
    int_field: QSpinBox
    double_field: QDoubleSpinBox
    button_box: QDialogButtonBox

    cur_num: int | float | None = None

    def __init__(
        self,
        parent,
        title: str,
        ask_text: str,
        mode: AskNumberType,
        cur_num: int | float | None = None,
        min: int | float | None = None,
    ):
        super().__init__(parent)
        loadUi("ui/widgets/dialogs/ask_number.ui", self)

        self.setWindowTitle(title)
        self.ask_label.setText(ask_text)

        if isinstance(min, int):
            self.int_field.setMinimum(min)
        if isinstance(min, float):
            self.double_field.setMinimum(min)

        self.cur_num = cur_num

        if isinstance(self.cur_num, int):
            self.int_field.setValue(self.cur_num)
        elif isinstance(self.cur_num, float):
            self.double_field.setValue(self.cur_num)

        if mode == AskNumberType.only_int:
            self.double_field.setVisible(False)
        elif mode == AskNumberType.only_double:
            self.int_field.setVisible(False)

    @staticmethod
    def get_int(
        parent,
        title: str,
        ask_text: str,
        cur_num: int | float | None = None,
        min: int | None = 0,
    ):
        dlg = AskNumber(parent, title, ask_text, AskNumberType.only_int, cur_num, min)
        done = dlg.exec_() == QDialog.Accepted
        return dlg.int_field.value(), done

    @staticmethod
    def get_double(
        parent,
        title: str,
        ask_text: str,
        cur_num: int | float | None = None,
        min: float | None = None,
    ):
        dlg = AskNumber(
            parent, title, ask_text, AskNumberType.only_double, cur_num, min
        )
        done = dlg.exec_() == QDialog.Accepted
        return dlg.double_field.value(), done

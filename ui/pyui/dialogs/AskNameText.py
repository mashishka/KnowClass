from enum import Enum

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QDir, QSettings, QModelIndex, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi  # type: ignore

import ui.pyui.ui_path as ui_path


class AskType(Enum):
    only_name = "o_n"
    only_text = "o_t"
    all = "all"


class AskNameText(QDialog):
    name_label: QLabel
    name_edit: QLineEdit
    text_label: QLabel
    text_edit: QTextEdit
    button_box: QDialogButtonBox

    cur_text: str | None = None

    def __init__(
        self,
        parent,
        title: str,
        ask_text: str,
        mode: AskType,
        cur_text: str | None = None,
    ):
        super().__init__(parent)
        loadUi(ui_path.PATH_TO_UI + "/dialogs/ask_factor.ui", self)

        self.setWindowTitle(title)
        self.text_label.setText(ask_text)

        self.cur_text = cur_text

        if self.cur_text is not None:
            self.text_edit.setText(self.cur_text)

        if mode == AskType.only_name:
            self.text_label.setVisible(False)
            self.text_edit.setVisible(False)
        elif mode == AskType.only_text:
            self.name_label.setVisible(False)
            self.name_edit.setVisible(False)

        self.button_box.accepted.disconnect()
        self.button_box.accepted.connect(self.try_accept)

    @pyqtSlot()
    def try_accept(self):
        fact_name = self.name_edit.text()
        if fact_name != "" or self.cur_text is not None:
            self.accept()
        else:
            QMessageBox.warning(self, self.windowTitle(), "Имя не должно быть пустым!")

    @staticmethod
    def get_info(
        parent, title: str, ask_text: str, mode: AskType, cur_text: str | None = None
    ):
        dlg = AskNameText(parent, title, ask_text, mode, cur_text)

        done = dlg.exec_() == QDialog.Accepted
        if mode == AskType.only_name:
            return dlg.name_edit.text(), done
        elif mode == AskType.only_text:
            return dlg.text_edit.toPlainText(), done
        return dlg.name_edit.text(), dlg.text_edit.toPlainText(), done

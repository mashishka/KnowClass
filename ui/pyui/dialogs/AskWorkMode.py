from enum import Enum

from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi  # type: ignore


class WorkMode(Enum):
    probability = "prob"
    weight = "weight"


class AskWorkMode(QDialog):
    main_frame: QFrame
    prob_rad: QRadioButton
    weight_rad: QRadioButton

    hidden_frame: QFrame
    low_check: QCheckBox
    value_spin: QDoubleSpinBox

    button_box: QDialogButtonBox

    def __init__(self, parent):
        super().__init__(parent)
        loadUi("ui/widgets/dialogs/ask_work_mode.ui", self)

        self.hidden_frame.setVisible(False)
        self.resize(self.width(), 5)

    @staticmethod
    def get_mode(parent):
        dlg = AskWorkMode(parent)

        done = dlg.exec_() == QDialog.Accepted

        if dlg.prob_rad.isChecked():
            res_mode = WorkMode.probability
        else:
            res_mode = WorkMode.weight

        if dlg.low_check.isChecked() and dlg.weight_rad.isChecked():
            val = dlg.value_spin.value()
        else:
            val = None

        return res_mode, done, val

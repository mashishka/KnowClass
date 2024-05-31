from dataclasses import dataclass
import PyQt5
from data_utils.controllers.ExampleController import ExampleController
from data_utils.controllers.FactorController import FactorController
from data_utils.controllers.ResultValueController import ResultValueController
from data_utils.controllers.TreeController import TreeController
from data_utils.controllers.ValueController import ValueController
from data_utils.controllers.ResultController import ResultController
from data_utils.core import DataBase
from tree.TreeClass import _DecisionNode, _LeafNode, TreeType

from tree.TreeClass import _DecisionNode, _LeafNode, TreeType
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QDir, QSettings, QModelIndex, QItemSelection, Qt
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi  # type: ignore


def same_value(value: ValueController | None, chosen: str):
    if value is None:
        return chosen == "*"
    if chosen == "*":
        return False
    return value.name == chosen


@dataclass
class TreeConsultState:
    node: TreeType | list[_LeafNode]
    examples: list[ExampleController]


@dataclass
class SetupState:
    factor: FactorController
    names: list[str]
    textes: list[str]


class CancelConsult(Exception):
    pass


class ConsultDialog(QDialog):
    # ui
    ans_list: QListWidget
    question: QLabel
    ans_btn: QPushButton
    close_btn: QPushButton

    def __init__(self, db: DataBase):
        QDialog.__init__(self)
        self.selected = False

        loadUi("ui/widgets/consult.ui", self)
        self.setup_state: SetupState

        mode, done = QInputDialog.getItem(
            self,
            f"Консультация",
            "Выберите способ обработки коэффициента неопределённости:",
            ["Вероятностный", "Веса"],
            editable=False,
        )
        if not done:
            self.reject()
            return

        self.db = db
        self.mode = mode
        self.state = TreeConsultState(  # -> раньше проверка идёт?
            node=TreeController.get(db).data,  # type: ignore
            examples=ExampleController.get_all(db),
        )
        self._next_state()

    @pyqtSlot()
    def on_ans_list_itemSelectionChanged(self):
        self.selected = len(self.ans_list.selectedItems()) > 0
        self.ans_btn.setEnabled(self.selected)

    @pyqtSlot()
    def on_close_btn_clicked(self):
        QMessageBox.warning(self, "Внимание", "Консультация отменена")
        self.reject()

    @pyqtSlot()
    def on_ans_btn_clicked(self):
        names = self.setup_state.names
        textes = self.setup_state.textes
        selected_text = self.ans_list.selectedItems()[0].text()
        selected_name = names[textes.index(selected_text)]

        examples = self.state.examples

        next_examples = [
            example
            for example in examples
            if same_value(example.get_value(self.setup_state.factor), selected_name)
        ]
        self.state = TreeConsultState(
            node=self.state.node.children[selected_name],
            examples=next_examples,
        )
        self._next_state()

    def setup(self, factor_name: str, tree_values: list[str]) -> None:
        factor = FactorController.get(self.db, factor_name)
        with_none = "*" in tree_values

        textes = [value.text for value in factor.get_values()]
        names = [value.name for value in factor.get_values()]
        if with_none:
            names += ["*"]
            textes += ["*"]

        self.setup_state = SetupState(factor=factor, names=names, textes=textes)
        self.question.setText(f"{factor.text}?")

        self.ans_btn.setDisabled(True)
        self.ans_list.clear()
        for text in textes:
            item = QListWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)
            self.ans_list.addItem(item)

    def show_result(self, leafs: list[_LeafNode]):
        result_list = []
        for leaf in leafs:
            result_text = ResultController.get(self.db).get_value(leaf.label).text
            if self.mode == "Вероятностный":
                text = f"{result_text}\n" + f"\tС вероятностью: {leaf.probability:.3f}\n"
            else:
                text = f"{result_text}\n" + f"\tС уверенностью: {leaf.weight:.3f}\n"
            result_list.append(text)

        result_text = "\n".join(result_list)
        result_text = ResultController.get(self.db).text + "\n" + result_text
        QMessageBox.information(self, "Результат консультации", result_text)
        self.accept()

    def _next_state(self) -> None:
        node = self.state.node
        exampels = self.state.examples

        def correct_leaf(leaf: _LeafNode):
            examples_ = [
                example.weight for example in exampels if example.result_value.name == leaf.label
            ]
            leaf.weight = sum(examples_)
            leaf.probability *= len(examples_)

        if isinstance(node, _DecisionNode):
            self.setup(node.attribute, list(node.children.keys()))
            return

        if isinstance(node, _LeafNode):
            correct_leaf(node)
            self.show_result([node])
            return

        unique_subnodes = sorted(
            list({subnode.label: subnode for subnode in node}.values()), key=lambda node: node.label
        )
        for subnode in unique_subnodes:
            correct_leaf(subnode)
        self.show_result(unique_subnodes)

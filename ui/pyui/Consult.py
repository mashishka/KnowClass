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
from tree.utils import recalc_stat

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QDir, QSettings, QModelIndex, QItemSelection, Qt
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi  # type: ignore
from ui.pyui.dialogs.AskItems import AskItems
from ui.pyui.dialogs.AskWorkMode import WorkMode


# def same_value(value: ValueController | None, chosen: str):
#     if value is None:
#         return chosen == "*"
#     if chosen == "*":
#         return False
#     return value.name == chosen


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

    def __init__(
        self, parent, db: DataBase, mode: WorkMode, min_val: float | None = None
    ):
        super(ConsultDialog, self).__init__(parent)
        self.selected = False

        loadUi("ui/widgets/consult.ui", self)
        self.setup_state: SetupState

        self.db = db
        self.mode = mode
        self.min_val = min_val
        self.state = TreeConsultState(  # -> раньше проверка идёт?
            node=TreeController.get(db).data.tree,  # type: ignore
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

        # examples = self.state.examples
        examples = [
            ExampleController.get(self.db, ex_id)
            for ex_id in self.state.node.examples_list
        ]

        # next_examples = [
        #     example
        #     for example in examples
        #     if same_value(
        #         example.get_value(self.setup_state.factor).name, selected_name
        #     )
        # ]

        next_node: TreeType = self.state.node.children[selected_name]
        if isinstance(next_node, (_DecisionNode, _LeafNode)):
            next_examples = [
                ExampleController.get(self.db, ex_id)
                for ex_id in next_node.examples_list
            ]
        if isinstance(next_node, list):
            next_examples = []
            for leaf in next_node:
                next_examples += [
                    ExampleController.get(self.db, ex_id)
                    for ex_id in leaf.examples_list
                ]

        self.state = TreeConsultState(
            node=next_node,
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
        if "no-data" in [leaf.label for leaf in leafs]:
            QMessageBox.information(
                self, "Результат консультации", "Нет информации об этой ситуации"
            )
            self.accept()
            return
        result_list = []
        recalc_stat(leafs)

        def sort_key(elem: _LeafNode):
            return (
                elem.probability if self.mode == WorkMode.probability else elem.weight
            )

        sort_leafs = list(sorted(leafs, key=sort_key, reverse=True))

        # пока что отсечение ниже порога есть только для режима весов
        if self.min_val is not None:

            def low_pruning(elem: _LeafNode):
                return elem.weight >= self.min_val

            sort_leafs = list(filter(low_pruning, sort_leafs))

        # TODO: что делать, если отфильтровались все ответы?

        for leaf in sort_leafs:
            result_text = ResultController.get(self.db).get_value(leaf.label).text
            if self.mode == WorkMode.probability:
                text = (
                    f"{result_text}\n" + f"\tС вероятностью: {leaf.probability:.3f}\n"
                )
            else:
                text = f"{result_text}\n" + f"\tС уверенностью: {leaf.weight:.3f}\n"
            result_list.append(text)

        result_text = "\n".join(result_list)
        result_text = ResultController.get(self.db).text + "\n" + result_text
        QMessageBox.information(self, "Результат консультации", result_text)
        self.accept()

    def _next_state(self) -> None:
        node = self.state.node
        examples = self.state.examples

        def correct_leaf(leaf: _LeafNode):
            examples_ = [
                example.weight
                for example in examples
                if example.result_value.name == leaf.label
            ]
            leaf.weight = sum(examples_)
            # leaf.probability *= len(examples_)

        if isinstance(node, _DecisionNode):
            self.setup(node.attribute, list(node.children.keys()))
            return

        if isinstance(node, _LeafNode):
            correct_leaf(node)
            self.show_result([node])
            return

        unique_subnodes = sorted(
            list({subnode.label: subnode for subnode in node}.values()),
            key=lambda node: node.label,
        )
        for subnode in unique_subnodes:
            correct_leaf(subnode)
        self.show_result(unique_subnodes)

    def check_before_exec(self) -> bool:
        return isinstance(self.state.node, _DecisionNode)

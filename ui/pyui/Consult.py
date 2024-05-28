from data_utils.controllers.ExampleController import ExampleController
from data_utils.controllers.FactorController import FactorController
from data_utils.controllers.ResultValueController import ResultValueController
from data_utils.controllers.ValueController import ValueController
from data_utils.controllers.ResultController import ResultController
from data_utils.core import DataBase
from tree.TreeClass import _DecisionNode, _LeafNode, TreeType

from tree.TreeClass import _DecisionNode, _LeafNode, TreeType
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QDir, QSettings, QModelIndex
from PyQt5.QtWidgets import *


class CancelConsult(Exception):
    pass


# TODO: тип вероятность / веса
def consult(parent: QWidget, db: DataBase, tree: TreeType, name: str):
    def same_value(value: ValueController | None, chosen: str):
        if value is None:
            return chosen == "*"
        if chosen == "*":
            return False
        return value.name == chosen

    def chose_factor_value(factor: FactorController, with_none: bool = False) -> str:
        textes = [value.text for value in factor.get_values()]
        names = [value.name for value in factor.get_values()]
        if with_none:
            names += ["*"]
            textes += ["*"]
        text, done = QInputDialog.getItem(
            parent, "Консультация", f"{factor.text}?", textes, editable=False
        )
        if not done:
            raise CancelConsult("Не выбран вариант")
        name_index = textes.index(text)
        return names[name_index]

    def leaf_info(leaf: _LeafNode):
        result_text = ResultController.get(db).get_value(leaf.label).text
        if name == "Вероятностный":
            return f"{result_text}\n" + f"\tС вероятностью: {leaf.probability:.3f}\n"
        else:
            return f"{result_text}\n" + f"\tС уверенностью: {leaf.weight:.3f}\n"

    # возвращает список результатов leaf_info / исключение об отмене
    def _consult(
        node, examples: list[ExampleController], parent_node=None, edge_label=None
    ) -> list[str]:
        if isinstance(node, _DecisionNode):
            fator_name = str(node.attribute)
            children_map_list: list[tuple[str, TreeType | list[_LeafNode]]] = list(
                node.children.items()
            )
            factor_values = [value for value, child_node in children_map_list]
            # print(factor_values)

            factor = FactorController.get(db, fator_name)
            chosen_value_name_or_none = chose_factor_value(
                factor, with_none=("*" in factor_values)
            )
            chosen_value_index = factor_values.index(chosen_value_name_or_none)

            next_examples = [
                example
                for example in examples
                if same_value(example.get_value(factor), chosen_value_name_or_none)
            ]
            return _consult(
                children_map_list[chosen_value_index][1],
                next_examples,
                node,
                factor_values[chosen_value_index],
            )

        if isinstance(node, _LeafNode):
            examples = [
                example.weight
                for example in examples
                if example.result_value.name == node.label
            ]
            node.weight = sum(examples)
            node.probability *= len(examples)
            # print(node.weight, examples)
            return [leaf_info(node)]

        res = []

        unique_subnodes = list({subnode.label: subnode for subnode in node}.values())
        unique_subnodes = sorted(unique_subnodes, key=lambda node: node.label)
        for subnode in unique_subnodes:
            res += _consult(subnode, examples, parent_node)
        return res

    try:
        result_list = _consult(tree, examples=ExampleController.get_all(db))
        result_text = "\n".join(result_list)
        result_text = ResultController.get(db).text + "\n" + result_text
        QMessageBox.information(parent, "Результат консультации", result_text)
    except CancelConsult as e:
        QMessageBox.warning(parent, "Консультация отменена", str(e))

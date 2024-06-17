from tree.TreeClass import *
from data_utils.controllers.ExampleController import *
from data_utils.controllers.FactorController import *
from data_utils.controllers.TreeController import *
from data_utils.controllers.ValueController import *
from data_utils.core import DataBase
from tree.TreeClass import _DecisionNode, _LeafNode
import pandas as pd

from tree.create_tree import make_dataframe
from pathlib import Path, PurePath
import copy


# рекурсивно добавить ко всем узлам отсутствующие значения
def alt_add_nodata(tree: TreeType, db: DataBase) -> TreeType:
    if isinstance(tree, (_LeafNode, list)):
        return tree

    child_names = []
    for atr, child in tree.children.items():
        child_names.append(atr)
        alt_add_nodata(child, db)

    name = tree.attribute
    factor = FactorController.get(db, name)

    val_names = [value.name for value in factor.get_values()]
    for val in val_names:
        if val not in child_names:
            tree.add_child(
                val, [_LeafNode(label="no-data", weight=0.00, probability=0.0)]
            )

    return tree


# ========================================================================================


def find_nodata_definitions(db: DataBase) -> list:
    df = make_dataframe(db)
    nodata = []
    values = ValueController.get_all(db)
    for value in values:
        if value.name not in list(df[value.factor.name]):
            nodata.append([value.factor.name, value.name])
    return nodata


def _add_nodata(new_tree: TreeType, factor: str, value: str):
    if not is_leaf(new_tree):
        if new_tree.attribute == factor:  # type: ignore
            new_tree.add_child(  # type: ignore
                value, [_LeafNode(label="No-data", weight=0.00, probability=0.0)]
            )
            return new_tree
        else:
            for child in new_tree.children.keys():  # type: ignore
                _add_nodata(new_tree.children[child], factor, value)  # type: ignore


def add_nodata(tree: TreeType, db: DataBase) -> TreeType:
    nodata = find_nodata_definitions(db)
    new_tree = copy.deepcopy(tree)
    for value in nodata:
        _add_nodata(new_tree, factor=value[0], value=value[1])
    return new_tree


# path = PurePath(
#     "C:\\Users\\maria\\Desktop\\KnowClass-main\\KnowClass-main\\res\\kb_examples\\nodata.db"
# )
# db = DataBase.load(path)
# tree = TreeController.get(db).data
# print_tree(tree)

# new_tree = add_nodata(tree, db)


# def print_tree(tree: TreeType, depth=0):
#     if not is_leaf(tree):
#         print("|------" * depth, tree.attribute)
#         for child in tree.children.keys():
#             print("|------" * depth, child)
#             print_tree(tree.children[child], depth + 1)
#     else:
#         for leaf in tree:
#             print("|------" * depth, leaf.label, "with weight: ", leaf.weight)


# print_tree(new_tree)

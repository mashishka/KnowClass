from enum import Enum
from tree.C45 import C45Classifier
from tree.L2R import LeftToRight

import pandas as pd

from data_utils.controllers.ExampleController import *
from data_utils.controllers.FactorController import *
from data_utils.controllers.TreeController import *
from data_utils.core import DataBase


class MethodType(Enum):
    left_to_right = "l2r"
    optimize = "c45"


def make_dataframe(db: DataBase) -> pd.DataFrame:
    data = {}
    factors = [FactorController.get_by_position(db, i) for i in range(FactorController.get_count(db))]#FactorController.get_all(db)
    examples = ExampleController.get_all(db)

    def get_value_or_none(factor: FactorController, example: ExampleController):
        val = example.get_value(factor)
        return val.name if val else val

    for factor in factors:
        data[factor.name] = [get_value_or_none(factor, example) for example in examples]
    data["RESULT"] = [example.result_value.name for example in examples]
    data["weight"] = [example.weight for example in examples]
    return pd.DataFrame(data).fillna("*")


# def mk(tree):
#     dot = graphviz.Digraph()

#     def build_tree(node, parent_node=None, edge_label=None):
#         if isinstance(node, _DecisionNode):
#             current_node_label = str(node.attribute)
#             dot.node(str(id(node)), label=current_node_label)

#             if parent_node:
#                 dot.edge(str(id(parent_node)), str(id(node)), label=edge_label)

#             for value, child_node in node.children.items():
#                 build_tree(child_node, node, value)
#         elif isinstance(node, _LeafNode):
#             current_node_label = f"Class: {node.label}, Weight: {node.weight}"
#             dot.node(str(id(node)), label=current_node_label, shape="box")

#             if parent_node:
#                 dot.edge(str(id(parent_node)), str(id(node)), label=edge_label)
#         else:
#             for subnode in node:
#                 build_tree(subnode, parent_node)
#     build_tree(tree)
#     dot.format = 'png'
#     dot.render("./1.gv", view=False)



def create_tree(db: DataBase, method: MethodType):
    df = make_dataframe(db)
    if method == MethodType.optimize:
        model = C45Classifier()
        X = df.drop(["RESULT", "weight"], axis=1)
        y = (
            df.index.astype(str)
            + "   _   "
            + df["RESULT"].astype(str)
            + "   _   "
            + df["weight"].astype(str)
        )
        model.fit(X, y)
        tree = model.tree
    elif method == MethodType.left_to_right:
        tree = LeftToRight(df)
    else:
        raise ValueError("Invalid method. Please choose either 'c45' or 'l2r'.")

    tree_controller = TreeController.get(db)
    tree_controller.data = tree
    return tree

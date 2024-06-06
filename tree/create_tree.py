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
    factors = [
        FactorController.get_by_position(db, i)
        for i in range(FactorController.get_count(db))
    ]
    examples = [example for example in ExampleController.get_all(db) if example.active]
    ids = [example.id for example in ExampleController.get_all(db) if example.active]

    def get_value_or_none(factor: FactorController, example: ExampleController):
        val = example.get_value(factor)
        return val.name if val else val

    for factor in factors:
        data[factor.name] = [get_value_or_none(factor, example) for example in examples]
    data["RESULT"] = [example.result_value.name for example in examples]
    data["weight"] = [example.weight for example in examples]
    df = pd.DataFrame(data).fillna("*")
    df = df.set_index(pd.Index(ids))
    return df


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

from tree.C45 import C45Classifier
from tree.L2R import LeftToRight

import pandas as pd
import numpy as np
from pathlib import Path, PurePath
from data_utils.controllers.ExampleController import *
from data_utils.controllers.FactorController import *
from data_utils.controllers.TreeController import *
from data_utils.core import DataBase


def make_dataframe(db: DataBase) -> pd.DataFrame:
    data = {}
    factors = FactorController.get_all(db)
    examples = ExampleController.get_all(db)
    for factor in factors:
        data[factor.name] = [
            (
                (
                    example.get_value(factor).name
                    if example is not None and example.get_value(factor) is not None
                    else None
                )
                if example is not None
                else None
            )
            for example in examples
        ]
    data["RESULT"] = [example.result_value.name for example in examples]
    data["weight"] = [example.weight for example in examples]
    return pd.DataFrame(data).fillna("None")


def create_tree(db: DataBase, method: str):
    df = make_dataframe(db)
    if method == "c45":
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
    elif method == "l2r":
        tree = LeftToRight(df)
    else:
        raise ValueError("Invalid method. Please choose either 'c45' or 'l2r'.")

    tree_controller = TreeController.get(db)
    tree_controller.data = tree
    return tree


db = DataBase.load(
    PurePath(
        "C:\\Users\\maria\\Desktop\\KnowClass-main\\KnowClass-main\\kb_examples\\hudlit.db"
    )
)

tree = create_tree(db, "l2r")
tree_controller = TreeController.get(db)

tree1 = tree_controller.data

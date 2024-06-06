from tree.TreeClass import *
from data_utils.controllers.ExampleController import *
from data_utils.controllers.FactorController import *
from data_utils.controllers.TreeController import *
from data_utils.core import DataBase
import pandas as pd

from tree.create_tree import make_dataframe


def _all_paths(tree: TreeType, current_path=[], paths=[]) -> list:
    if not is_leaf(tree):
        current_path.append(tree.attribute)
        for key, value in tree.children.items():
            temp_path = current_path.copy()
            temp_path.append(key)
            _all_paths(value, temp_path, paths)
    else:
        for t in tree:
            _current_path = current_path.copy()
            _current_path.append("RESULT")
            _current_path.append(t.label)
            _current_path.append("weight")
            _current_path.append(t.weight)
            paths.append(_current_path)

    return paths


def all_paths(tree: TreeType):
    paths = []
    paths = _all_paths(tree, current_path=[], paths=[])
    ans = []
    for path in paths:
        tmp = []
        for i in range(1, len(path), 2):
            tmp.append([path[i - 1], path[i]])
        ans.append(tmp)
    return ans


def find_path(paths: list, rool: list) -> list:
    # paths = all_paths(tree)
    ans = []
    for path in paths:
        if (
            path[len(path) - 2] == rool[len(rool) - 2]
            and path[len(path) - 1] == rool[len(rool) - 1]
        ):
            ans.append(path)
    return ans


def find(example: list, rool: list):
    for r in rool:
        if r == example:
            return True
    return False


def running(path: list, rool: list) -> bool:
    path_ = path.copy()
    for node in path:
        if find(node, rool):
            path_.remove(node)
    if path_ == []:
        return True
    return False


def completeness(
    tree: TreeType, db: DataBase
) -> list:  # возвращает примеры, которых нет в дереве
    df = make_dataframe(db)
    tree_paths = all_paths(tree)
    cols = df.columns
    indices = []
    for index, row in df.iterrows():
        rool = []
        for col in cols:
            rool.append([col, row[col]])
        paths = find_path(tree_paths, rool)
        if paths == []:
            indices.append(index)
        else:
            for path in paths:
                if not running(rool=rool, path=path):
                    indices.append(index)
    return indices

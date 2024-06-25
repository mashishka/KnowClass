from dataclasses import dataclass
from data_utils.controllers.ExampleController import *
from data_utils.controllers.TreeController import *
from data_utils.core import DataBase
import pandas as pd

from tree.C45 import C45Classifier
from tree.L2R import LeftToRight

from tree.TreeClass import _DecisionNode, _LeafNode, TreeType, MethodType
import copy

from utils.profile_time import logtime


def is_leaf(node: TreeType):
    if isinstance(node, _DecisionNode):
        return False
    return True


# check tree
# ==============================================================================
# ==============================================================================


def _all_paths(tree: TreeType, current_path=None, paths=None) -> list:
    if current_path is None:
        current_path = []
    if paths is None:
        paths = []
    if not is_leaf(tree):
        current_path.append(tree.attribute)  # type: ignore
        for key, value in tree.children.items():  # type: ignore
            temp_path = current_path.copy()
            temp_path.append(key)
            _all_paths(value, temp_path, paths)
    else:
        for t in tree:  # type: ignore
            _current_path = current_path.copy()
            _current_path.append("RESULT")
            _current_path.append(t.label)
            _current_path.append("weight")
            _current_path.append(t.weight)
            paths.append(_current_path)

    return paths


def all_paths(tree: TreeType):
    paths = []
    paths = _all_paths(tree)
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


# возвращает список из id примеров, которых нет в дереве
def completeness(tree: TreeType, db: DataBase) -> list:  # list[int]
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
            tmp = 0
            for path in paths:
                if not running(rool=rool, path=path):
                    tmp += 1
                    # indices.append(index)
            if tmp == len(paths):
                indices.append(index)
    return indices


# TODO: оптимизировать обращение к бд
# возвращает список из id примеров, которых нет в дереве
def alt_completeness(tree: TreeType, db: DataBase) -> list[int]:  #
    def is_fit(ex: ExampleController, tree: TreeType) -> bool:
        if isinstance(tree, _LeafNode):
            return ex.result_value.name == tree.label
        if isinstance(tree, list):
            fit_res: bool = False
            for leaf in tree:
                fit_res = fit_res or is_fit(ex, leaf)
            return fit_res

        cur_factor = FactorController.get(db, tree.attribute)
        cur_val = ex.get_value(cur_factor)
        if cur_val is not None:
            return is_fit(ex, tree.children[cur_val.name])
        else:
            for name, child in tree.children.items():
                if is_fit(ex, child):
                    return True
            return False

    all_ex = ExampleController.get_all(db)
    res: list[int] = []
    for example in all_ex:
        if not is_fit(example, tree):
            res.append(example.id)

    return res


# create tree
# ==============================================================================
# ==============================================================================


@dataclass
class ExampleData:
    values: list[str | None]
    id: int


def make_dataframe(db: DataBase) -> pd.DataFrame:
    data = {}
    factors = [
        FactorController.get_by_position(db, i)
        for i in range(FactorController.get_count(db))
    ]
    factor_values = [
        [value.name for value in factor.get_values()] for factor in factors
    ]
    examples_data = {
        example.id: {"result": example.result_value.name, "weight": example.weight}
        for example in ExampleController.get_all(db)
        if example.active
    }

    def get_example_data(id: int) -> list[ExampleData]:
        ex = ExampleData(values=[], id=id)
        for factor in factors:
            val = ExampleController.get(db, ex.id).get_value(factor)
            ex.values.append(val.name if val else None)
        res = []
        q = [ex]
        while len(q) > 0:
            ex = q.pop()
            try:
                ind = ex.values.index(None)
            except ValueError:
                res.append(ex)
                continue
            for value in factor_values[ind]:
                new_ex = ExampleData(values=ex.values.copy(), id=ex.id)
                new_ex.values[ind] = value
                q.append(new_ex)

        return res

    examples: list[ExampleData] = []
    for id in examples_data:
        examples += get_example_data(id)

    for i, factor in enumerate(factors):
        data[factor.name] = [example.values[i] for example in examples]

    data["RESULT"] = [examples_data[ex.id]["result"] for ex in examples]  # type: ignore
    data["weight"] = [examples_data[ex.id]["weight"] for ex in examples]  # type: ignore
    df = pd.DataFrame(data)
    df = df.set_index(pd.Index((example.id for example in examples)))
    print(df)
    return df


def zflip_tree(tree: TreeType):
    res = zflip_tree_rec(tree)
    if res:
        # print("zflipped")
        return res
    return tree


def zflip_tree_rec(
    tree: TreeType,
    parent_data: tuple[_DecisionNode, str] | None = None,
):
    if not isinstance(tree, _DecisionNode):
        return
    if not tree.children:
        return

    for k in tree.children:
        zflip_tree_rec(tree.children[k], (tree, k))

    lists = [v for k, v in tree.children.items() if isinstance(v, list)]
    if len(lists) != len(tree.children):
        return

    first = lists[0]
    first_labels = {leaf.label for leaf in first}
    for l in lists[1:]:
        if len(first) != len(l):
            return
        value_labels = {leaf.label for leaf in l}
        if value_labels != first_labels:
            return
    if not parent_data:
        return first
    parent, pkey = parent_data
    parent.children[pkey] = first

    # print(
    #     "change",
    #     parent_data,
    #     first,
    #     tree,
    #     first_labels,
    #     pkey,
    #     parent.attribute,
    # )


def create_tree(db: DataBase, method: MethodType) -> RootTree:
    df = make_dataframe(db)
    if method == MethodType.optimize:
        model = C45Classifier()
        X = df.drop(["RESULT", "weight"], axis=1)
        y = df["RESULT"].astype(str)
        model.fit(X, y)
        tree = model.tree
    elif method == MethodType.left_to_right:
        tree = LeftToRight(df)
    else:
        raise ValueError("Invalid method. Please choose either 'c45' or 'l2r'.")

    # tree = add_nodata(tree, db)
    tree = zflip_tree(tree)
    tree = alt_add_nodata(tree, db)
    add_examples(tree, db)

    root = RootTree(actual=True, method=method, tree=tree)

    tree_controller = TreeController.get(db)
    tree_controller.data = root
    return root


# NoData
# ==============================================================================
# ==============================================================================


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


# ========================================================================================


# сравнить значение с предлагаемым
def same_value(value: ValueController | None, chosen: str):
    if value is None:
        return True
    # if chosen == "*":
    #     return False
    return value.name == chosen


# получить список id примеров для элемента дерева
# для листа фильтруем по значению результата, для узла считаем, что все нужные примеры уже пришли
def _gen_id_list(tree: TreeType, examples: list[ExampleController]) -> list[int]:
    if isinstance(tree, _LeafNode):
        return [
            example.id
            for example in examples
            if example.result_value.name == tree.label
        ]
    if isinstance(tree, _DecisionNode):
        return [example.id for example in examples]
    raise Exception("unreachable code")


# рекурсивно добавить разбиение примеров к узлам и листьям
def add_examples(tree: TreeType, db: DataBase) -> None:
    all_exam = ExampleController.get_all(db)

    def rec_add(tree: TreeType, examples: list[ExampleController]) -> None:
        if isinstance(tree, _LeafNode):
            tree.examples_list = _gen_id_list(tree, examples)
            return
        if isinstance(tree, list):
            for leaf in tree:
                leaf.examples_list = _gen_id_list(leaf, examples)
            return

        tree.examples_list = _gen_id_list(tree, examples)
        cur_factor = FactorController.get(db, tree.attribute)

        for name_child, child_node in tree.children.items():
            next_examples = [
                example
                for example in examples
                if same_value(example.get_value(cur_factor), name_child)
            ]
            rec_add(child_node, next_examples)

    rec_add(tree, all_exam)


# TODO: потенциально огромное время выполнения
# TODO: можно попробовать сделать ленивые вычисления
# сортирует детей данного узла в соответствии с порядком в определениях
def ordered_by_defin(
    tree: _DecisionNode | list[_LeafNode], db: DataBase
) -> list[tuple[str, TreeType] | _LeafNode]:
    if isinstance(tree, _DecisionNode):
        res: list[tuple[str, TreeType] | _LeafNode] = []
        vals = [
            val.name for val in FactorController.get(db, tree.attribute).get_values()
        ]
        for val in vals:
            res.append((val, tree.children[val]))
        return res
    if isinstance(tree, list):
        rc = ResultController.get(db)
        all_vals = [
            rc.get_value_by_position(pos).name for pos in range(rc.get_values_count())
        ]
        node_vals = [(leaf.label, leaf) for leaf in tree]
        res = []
        for res_val in all_vals:
            if len(res) == len(node_vals):
                break
            for label, node in node_vals:
                if res_val == label:
                    res.append(node)
        return res

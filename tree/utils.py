from dataclasses import dataclass
from typing import Any
from data_utils.controllers.ExampleController import *
from data_utils.controllers.TreeController import *
from data_utils.core import DataBase
import pandas as pd

from tree.C45 import C45Classifier

from tree.TreeClass import _DecisionNode, _LeafNode, TreeType, MethodType

from utils.profile_time import logtime


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
    # print(df)
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

    model = C45Classifier(method == MethodType.left_to_right)
    X = df.drop(["RESULT", "weight"], axis=1)
    y = df["RESULT"].astype(str)
    model.fit(X, y)
    tree = model.tree

    tree = zflip_tree(tree)  # type: ignore
    tree = alt_add_nodata(tree, get_all_factor_value_names(db))
    add_examples(tree, db)

    root = RootTree(actual=True, method=method, tree=tree)

    tree_controller = TreeController.get(db)
    tree_controller.data = root
    return root


# NoData
# ==============================================================================
# ==============================================================================


# рекурсивно добавить ко всем узлам отсутствующие значения
def alt_add_nodata(
    tree: TreeType,
    factor_values: dict[str, list[str]],
) -> TreeType:
    if isinstance(tree, (_LeafNode, list)):
        return tree

    child_names = []
    for atr, child in tree.children.items():
        child_names.append(atr)
        alt_add_nodata(child, factor_values)

    for val in factor_values[tree.attribute]:
        if val not in child_names:
            tree.add_child(
                val, [_LeafNode(label="no-data", weight=0.00, probability=0.0)]
            )

    return tree


# ========================================================================================


# сравнить значение с предлагаемым
def same_value(value: str | None, chosen: str):
    if value is None:
        return True
    return value == chosen


# получить список id примеров для элемента дерева
# для листа фильтруем по значению результата, для узла считаем, что все нужные примеры уже пришли
def _gen_id_list(tree: TreeType, examples: dict[int, Any]) -> list[int]:
    if isinstance(tree, _LeafNode):
        return [id for id, data in examples.items() if data["result"] == tree.label]
    if isinstance(tree, _DecisionNode):
        return [id for id in examples]
    raise Exception("unreachable code")


# рекурсивно добавить разбиение примеров к узлам и листьям
def add_examples(tree: TreeType, db: DataBase) -> None:
    factors = [
        FactorController.get_by_position(db, i)
        for i in range(FactorController.get_count(db))
    ]

    def name_or_none(value: ValueController | None):
        if not value:
            return None
        return value.name

    examples_data = {
        example.id: {
            "result": example.result_value.name,
            "values": {
                factor.name: name_or_none(example.get_value(factor))
                for factor in factors
            },
        }
        for example in ExampleController.get_all(db)
        if example.active
    }

    def rec_add(tree: TreeType, examples: dict[int, Any]) -> None:
        if isinstance(tree, _LeafNode):
            tree.examples_list = _gen_id_list(tree, examples)
            return
        if isinstance(tree, list):
            for leaf in tree:
                leaf.examples_list = _gen_id_list(leaf, examples)
            return

        tree.examples_list = _gen_id_list(tree, examples)
        cur_factor = tree.attribute

        for name_child, child_node in tree.children.items():
            next_examples = {
                id: data
                for id, data in examples.items()
                if same_value(data["values"][cur_factor], name_child)
            }
            rec_add(child_node, next_examples)

    rec_add(tree, examples_data)


# сортирует детей данного узла в соответствии с порядком в определениях
def ordered_by_defin(
    tree: _DecisionNode | list[_LeafNode],
    factor_values: dict[str, list[str]],
    result_values: list[str],
) -> list[tuple[str, TreeType] | _LeafNode]:
    if isinstance(tree, _DecisionNode):
        res: list[tuple[str, TreeType] | _LeafNode] = []
        for val in factor_values[tree.attribute]:
            res.append((val, tree.children[val]))
        return res
    if isinstance(tree, list):
        node_vals = [(leaf.label, leaf) for leaf in tree]
        res = []
        local_res_vals = result_values + ["no-data"]
        for res_val in local_res_vals:
            if len(res) == len(node_vals):
                break
            for label, node in node_vals:
                if res_val == label:
                    res.append(node)
        return res


def get_all_factor_value_names(db: DataBase) -> dict[str, list[str]]:
    return {
        factor.name: [
            factor.get_value_by_position(i).name
            for i in range(factor.get_values_count())
        ]
        for factor in FactorController.get_all(db)
    }


def recalc_stat(leafs: list[_LeafNode]):
    if len(leafs) == 1:
        leafs[0].probability = 1.0
        leafs[0].weight /= len(leafs[0].examples_list)
        return
    all_weight = sum([leaf.weight for leaf in leafs])
    for leaf in leafs:
        leaf.probability = leaf.weight / all_weight
        leaf.weight /= len(leaf.examples_list)

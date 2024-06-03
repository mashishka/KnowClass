from TreeClass import _DecisionNode, _LeafNode
from data_utils.controllers.ExampleController import *
from data_utils.controllers.FactorController import *
from data_utils.controllers.TreeController import *
from data_utils.core import DataBase
from pathlib import Path, PurePath

from tree.create_tree import make_dataframe


def in_tree(tree, factor, example) -> bool:
    
    if tree.attribute == factor and example in tree.children.keys():
        return True
    
    for child in tree.children.keys():
        if type(tree.children[child]) != list:
            if in_tree(tree.children[child], factor, example):
                return True
            
    return False


def in_leaf(tree, result, weight):
    if type(tree) == list:
        for child in tree:
            if child.label == result and child.weight == weight:
                return True
    else:
        if tree.children:
            for child in tree.children:
                if in_leaf(tree.children[child], result, weight):
                    return True
        else:
            if tree.label == result and tree.weight == weight:
                return True
    return False

def completeness(db: DataBase) -> dict:
    ans = {}
    tree = TreeController.get(db).data
    df = make_dataframe(db)
    for factor in df.columns:
        if factor != "RESULT":
            examples = list(set(df[factor]))
            if "*" in examples:
                examples.remove("*")
            for example in examples:
                if not in_tree(tree, factor, example):
                    ans[factor] = example
        else:
            for i in range(len(df["RESULT"])):
                result = df["RESULT"][i]
                weight = df["weight"][i]
                if not in_leaf(tree, result, weight):
                    ans["RESULT"] = result
            return ans
        
    return ans


path = PurePath("C:\\Users\\maria\\Desktop\\KnowClass-main\\KnowClass-main\\res\\kb_examples\\hudlit.db")
db = DataBase.load(path)
tree = TreeController.get(db).data

completeness(db)

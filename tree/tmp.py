from data_utils.controllers.TreeController import *
from data_utils.core import DataBase
from pathlib import Path, PurePath
from C45 import C45Classifier
from tree.tree import Tree
import pickle


db = DataBase.load(
    PurePath(
        "C:\\Users\\maria\\Desktop\\KnowClass-main\\KnowClass-main\\kb_examples\\hudlit.db"
    )
)

tree_controller = TreeController.get(db)
tree = Tree(db)
byte_tree = pickle.dumps(tree)
tree_controller.data = byte_tree

print(tree_controller.data == byte_tree)

new_tree_controller = TreeController.get(db)
print(new_tree_controller.data == byte_tree)
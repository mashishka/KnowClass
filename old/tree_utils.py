import json
import logging as log
from pathlib import PurePosixPath

# import pandas as pd
# from pandas import DataFrame
from treelib import Node, Tree  # type: ignore


def to_json(tree: Tree, filepath: str):
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(tree.to_dict(), file, ensure_ascii=False)


def LoadTreeJSON(loadpath_json: str):
    # if loadpath_json is None:
    #    loadpath_json = GetFilePathJSON()
    # if loadpath_json is None:
    #   return
    log.debug("function started")
    with open(loadpath_json, encoding="utf-8") as file:
        log.debug("file opened")
        tree = Tree()
        data: dict = json.load(file)
        log.debug("data loaded")
        for key1, value1 in data.items():
            node1 = PurePosixPath(key1)
            tree.create_node(tag=key1, identifier=str(node1), parent=None)
            for list1 in value1["children"]:
                for key2, value2 in list1.items():
                    node2 = PurePosixPath(key1, key2)
                    tree.create_node(tag=key2, identifier=str(node2), parent=str(node1))
                    for list2 in value2["children"]:
                        for key3, value3 in list2.items():
                            node3 = PurePosixPath(key1, key2, key3)
                            tree.create_node(tag=key3, identifier=str(node3), parent=str(node2))
                            for list3 in value3["children"]:
                                if isinstance(list3, dict):  # Process Only Filled Directories
                                    for key4, value4 in list3.items():
                                        node4 = PurePosixPath(key1, key2, key3, key4)
                                        tree.create_node(
                                            tag=key4, identifier=str(node4), parent=str(node3)
                                        )
                                        for list4 in value4["children"][0:]:
                                            node5 = PurePosixPath(key1, key2, key3, key4, list4)
                                            tree.create_node(
                                                tag=list4, identifier=str(node5), parent=str(node4)
                                            )
    return tree


# def save_to_xlsx(df: DataFrame, filename: str):
#     df.to_excel(filename, index=False)


# def load_from_xlsx(filename: str):
#     return pd.read_excel(filename)

import math
from typing import TypeAlias
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum


class MethodType(Enum):
    left_to_right = "l2r"
    optimize = "c45"


class _DecisionNode:
    def __init__(self, attribute):
        # Inisialisasi simpul keputusan dengan atribut yang diberikan
        self.attribute = attribute
        self.children = {}  # Menyimpan anak-anak simpul keputusan
        self.examples_list = []

    def depth(self):
        # Menghitung kedalaman simpul keputusan
        if len(self.children) == 0:
            return 1
        else:
            max_depth = 0
            for child in self.children.values():
                if isinstance(child, _DecisionNode):
                    child_depth = child.depth()
                    if child_depth > max_depth:
                        max_depth = child_depth
            return max_depth + 1

    def add_child(self, value, node):
        # Menambahkan anak ke simpul keputusan dengan nilai atribut yang diberikan
        self.children[value] = node

    def count_leaves(self):
        if len(self.children) == 0:
            return 1
        else:
            count = 0
            for child in self.children.values():
                if isinstance(child, _DecisionNode):
                    count += child.count_leaves()
                else:
                    count += 1
            return count


class _LeafNode:
    def __init__(self, label, weight=0, probability=0):
        # Inisialisasi simpul daun dengan label kelas dan bobot yang diberikan
        self.label = label
        self.weight = weight
        self.probability = probability
        self.examples_list = []


TreeType: TypeAlias = _DecisionNode | _LeafNode | list[_LeafNode]


@dataclass
class RootTree:
    actual: bool
    method: MethodType
    tree: TreeType

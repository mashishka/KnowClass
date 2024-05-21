from C45 import C45Classifier
import pandas as pd
import numpy as np
from pathlib import Path, PurePath
from data_utils.controllers.ExampleController import *
from data_utils.controllers.FactorController import *
from data_utils.controllers.TreeController import *
from data_utils.core import DataBase


class Node:
    def __init__(self, question, answer=None):
        self.question = question
        self.answer = answer
        self.children = []

    def add_child(self, child):
        self.children.append(child)


class Tree:
    def __init__(self, db: DataBase):
        self.df = self.make_dataframe(db)
        self.c45_tree = self.make_c45(self.df)
        self.name_to_text = self.get_definitions(db)
        tree_controller = TreeController.get(db)
        byte_tree = pickle.dumps(self.c45_tree)
        tree_controller.data = byte_tree

    @staticmethod
    def load(db: DataBase):
        tree = Tree(db)
        tree.df = tree.make_dataframe(db)
        tree_controller = TreeController.get(db)
        byte_tree = tree_controller.data
        tree_ = pickle.loads(byte_tree)
        tree.c45_tree = tree_
        tree.name_to_text = tree.get_definitions(db)
        return tree

    def make_dataframe(self, db: DataBase) -> pd.DataFrame:
        data = {}
        factors = FactorController.get_all(db)
        examples = ExampleController.get_all(db)
        for factor in factors:
            data[factor.name] = [
                (
                    example.get_value(factor).name
                    if example.get_value(factor) is not None
                    else None
                )
                for example in examples
            ]
        data["RESULT"] = [example.result_value.name for example in examples]
        data["weight"] = [example.weight for example in examples]
        return pd.DataFrame(data)

    def get_definitions(self, db: DataBase) -> dict:
        definitions = {}
        values = ValueController.get_all(db)
        for value in values:
            definitions[value.name] = value.text
        factors = FactorController.get_all(db)
        for factor in factors:
            definitions[factor.name] = factor.text
        results = ResultController.get(db).get_values()
        for result in results:
            definitions[result.name] = result.text
        return definitions

    def make_c45(self, df):
        X = df.drop(["RESULT", "weight"], axis=1)
        y = df["RESULT"] + ": " + df.weight.astype(str)
        model = C45Classifier()
        model.fit(X, y)
        return self.c45_to_tree(model)

    def c45_to_tree(self, model):
        root_question = model.tree.attribute
        root = Node(root_question)
        self.c45_build_subtree(root, model.tree)
        return root

    def c45_build_subtree(self, parent, tree):
        answers = list(tree.children.keys())
        # print(answers)

        for answer in answers:
            # print(answer)
            # print(tree.children[answer])
            # if type(tree.children[answer]) == C45._LeafNode:
            if type(tree.children[answer]) == list:
                child_question = "RESULT"
                child = Node(child_question, answer)
                parent.add_child(child)

                weigth_question = "weigth"
                for label in tree.children[answer]:
                    weight_answer = label.label.split(": ")[0]
                    weight_child = Node(weigth_question, weight_answer)
                    child.add_child(weight_child)

                    end_answer = label.label.split(": ")[1]
                    end_question = "end"
                    endNode = Node(end_question, end_answer)
                    weight_child.add_child(endNode)
                # return
                # print(child_question, answer)
            else:
                child_question = tree.children[answer].attribute
                child = Node(child_question, answer)
                parent.add_child(child)
                self.c45_build_subtree(child, tree.children[answer])

    def __print_tree(self, node, depth=0):
        if node.answer and node.answer != "end":
            print("|  " * depth + f"|--- {node.answer}")
        if node.question != "end":
            print("|  " * depth + f"|--- {node.question}")
        for child in node.children:
            self.__print_tree(child, depth + 1)

    def print_tree(self, depth=0):
        print(self.c45_tree.answer)
        self.__print_tree(self.c45_tree)

    def consult(self, mode: str) -> None:
        self.__consult(self.c45_tree, mode)

    def __consult(self, node, mode):
        if node.question == "RESULT":
            print("Рекомендовано:")
            answers = [
                self.name_to_text[node.children[i].answer]
                for i in range(len(node.children))
            ]
            weights = [
                float(node.children[i].children[0].answer)
                for i in range(len(node.children))
            ]
            # print("Ответ(ы):", ", ".join([node.children[i].answer for i in range(len(node.children))]))
            if mode == "prob":
                for i in range(len(answers)):
                    p = [w / np.sum(weights) for w in weights]
                    print(answers[i], " с вероятностью ", p[i])
            elif mode == "KU":
                for i in range(len(answers)):
                    print(answers[i], " с уверенностью ", weights[i])
            else:
                print(mode)
                for i in range(len(answers)):
                    print(answers[i])
            print("Консультация закончена")
            return

        print(f"Вопрос: {self.name_to_text[node.question]}")

        if not node.children:
            answer_list = [self.name_to_text[node.answer]]
            print("Ответ(ы):", ", ".join(answer_list))
            return

        for idx, child in enumerate(node.children):
            print(f"{idx+1}: {self.name_to_text[child.answer]}")

        choice = input("Выберите ответ(введите номер) или введите 'end' для выхода: ")

        if choice.lower() == "end":
            return

        try:
            choice_idx = int(choice) - 1
            self.__consult(node.children[choice_idx], mode)
        except (ValueError, IndexError):
            print("Некорректный выбор. Попробуйте еще раз.")
            self.__consult(node, mode)


db = DataBase.load(
    PurePath(
        "C:\\Users\\maria\\Desktop\\KnowClass-main\\KnowClass-main\\kb_examples\\hudlit.db"
    )
)


tree = Tree(db)
tree.print_tree()
tree.consult(mode="prob")

tree = Tree.load(db)
tree.print_tree()
tree.consult(mode="prob")

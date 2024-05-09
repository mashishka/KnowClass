import logging as log

# from pandas import DataFrame
from treelib import Node, Tree  # type: ignore

####################################### to_matrix ###########################################


# TODO: Вот это надо переписать
def question_list(tree: Tree) -> list:
    q_l = []
    nodes = [tree[node].tag for node in tree.expand_tree(mode=Tree.WIDTH)]
    for node in nodes:
        if node[-1] == "?":
            q_l.append(node)
    return q_l


# Добавляем текущий узел в путь
# Если текущий узел является листом, добавляем путь в список путей
# Рекурсивно обходим левого и правого потомков
# Удаляем текущий узел из текущего пути перед возвратом
def find_all_paths(node: str | dict, path: list, paths: list):
    if type(node) == str:  # Если текущий узел является листом, добавляем путь в список путей
        path.append(node)
        paths.append(path[:])

    # log.debug(type(tree), tree)
    if type(node) == dict:  # Добавляем текущий узел в путь
        for key, _ in node.items():
            path.append(key)

    # """if type(tree) == list:
    # for list_ in tree:
    #   path.append(list_)
    #   paths.append(path[:])
    #   path.pop()"""
    # else:
    if type(node) == dict:
        for key, value in node.items():  # Рекурсивно обходим левого и правого потомков
            for i in range(len(node[key]["children"])):
                find_all_paths(node[key]["children"][i], path, paths)

    path.pop()  # Удаляем текущий узел из текущего пути перед возвратом


####################################### to_tree ###########################################


def find_parent(column: str, df: DataFrame):
    j = list(df.columns).index(column)
    if j == 0:
        return None

    i = 0
    while df[column][i] == "*":
        i += 1
    j -= 1
    while df.iloc[i, j] == "*":
        j -= 1
    return df.iloc[i, j]


def find_parent_for_result(ans, df: DataFrame):
    i = list(df["RESULT"]).index(ans)
    j = list(df.columns).index("RESULT")
    j -= 1
    while df.iloc[i, j] == "*":
        j -= 1
    return df.iloc[i, j]


####################################### utils ###########################################


def to_matrix(tree: Tree) -> DataFrame:
    dict_matrix: dict = {}
    paths: list = []

    find_all_paths(tree.to_dict(), [], paths)

    # Список вопросов, которые будут столбцами в датафрейме
    q_l = question_list(tree)
    for i in q_l:
        dict_matrix[i] = []
    dict_matrix["RESULT"] = []

    # Перебираем все пути до ответа. Если вопроса нет, ставим *
    for path in paths:
        for q_l_i in q_l:
            if q_l_i in path:
                dict_matrix[q_l_i].append(path[path.index(q_l_i) + 1])
            else:
                dict_matrix[q_l_i].append("*")
        dict_matrix["RESULT"].append(path[len(path) - 1])

    return DataFrame(dict_matrix)


def to_tree(matrix: DataFrame):
    tree = Tree()
    # tree.create_node("Какой вид информационной литературы Вас интересует?", "raznovid")  # root node
    for column in matrix.columns:
        if column == "RESULT":
            answers = list(set(matrix[column]))
            for answer in answers:
                tree.create_node(answer, answer, parent=find_parent_for_result(answer, matrix))

        else:
            tree.create_node(column, column, parent=find_parent(column, matrix))
            answers = list(set(matrix[column]))

            for answer in answers:
                if answer != "*":
                    tree.create_node(answer, answer, parent=column)
    return tree

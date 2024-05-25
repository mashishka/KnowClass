from tree.TreeClass import _DecisionNode, _LeafNode, is_leaf


def LeftToRight(df):
    root_question = df.columns[0]
    root_answers = list(set(df[df.columns[0]]))
    root_node = _DecisionNode(root_question)
    for ans in root_answers:
        # print(root_question, ans)
        root_node.add_child(ans, __LeftToRight(cut_df(df, root_question, ans)))

    return root_node


def __LeftToRight(_df):
    # print("-")
    question = _df.columns[0]
    node = _DecisionNode(question)

    if question == "RESULT":
        answers = _df["RESULT"]
        weights = _df["weight"]
        probs = [w / sum(weights) for w in weights]
        # for ans, w, p in zip(answers, weights, probs):
        #     leaf_node = _LeafNode(ans, w, p)
        #     node.add_child(leaf_node)
        return [_LeafNode(ans, w, p) for ans, w, p in zip(answers, weights, probs)]

    answers = list(set(_df[question]))
    for answer in answers:
        # if answer == None:
        # answer = "None"
        # print(question)
        # print(_df)
        # print(cut_df(_df, question, answer))
        # print(question, answer)
        child_node = __LeftToRight(cut_df(_df, question, answer))
        node.add_child(answer, child_node)

    return node


def cut_df(df, col, ans):
    tmp_df = df.copy()
    tmp_df = tmp_df[tmp_df[col] == ans]
    tmp_df = tmp_df.loc[:, col:]
    tmp_df = tmp_df.drop(col, axis=1)
    # print(set(tmp_df[tmp_df.columns[0]]))
    while set(tmp_df[tmp_df.columns[0]]) == {"None"}:
        tmp_df = tmp_df.iloc[:, 1:]

    return tmp_df

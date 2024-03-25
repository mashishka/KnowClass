import numpy as np
import treelib
import pandas as pd
import os
import json
from pathlib import PurePosixPath, Path
from treelib import Node, Tree


def question_list(tree):  #####Вот это надо переписать
  q_l = []
  nodes = [tree[node].tag for node in tree.expand_tree(mode=Tree.WIDTH)]
  for node in nodes:
    if node[-1] == '?':
      q_l.append(node)
  return q_l

# Добавляем текущий узел в путь
# Если текущий узел является листом, добавляем путь в список путей
# Рекурсивно обходим левого и правого потомков
# Удаляем текущий узел из текущего пути перед возвратом
def find_all_paths(tree, path, paths):
  if type(tree) == str:# Если текущий узел является листом, добавляем путь в список путей
    path.append(tree)
    paths.append(path[:])

  #print(type(tree), tree)
  if type(tree) == dict: # Добавляем текущий узел в путь
    for key, _ in tree.items():
      path.append(key)

  """if type(tree) == list:
    for list_ in tree:
      path.append(list_)
      paths.append(path[:])
      path.pop()"""
  #else:
  if type(tree) == dict :
      for key, value in tree.items(): # Рекурсивно обходим левого и правого потомков
        for i in range(len(tree[key]['children'])):
          find_all_paths(tree[key]['children'][i], path, paths)

  path.pop() # Удаляем текущий узел из текущего пути перед возвратом

def tree_to_matrix(tree):
  dict_matrix = {}

  paths = []
  find_all_paths(tree.to_dict(), [], paths)

  #Список вопросов, которые будут столбцами в датафрейме
  q_l = question_list(tree)
  for i in q_l:
    dict_matrix[i] = []
  dict_matrix['RESULT'] = []

  #Перебираем все пути до ответа. Если вопроса нет, ставим *
  for path in paths:
    for q_l_i in q_l:
      if q_l_i in path:
        dict_matrix[q_l_i].append(path[path.index(q_l_i)+1])
      else:
        dict_matrix[q_l_i].append('*')
    dict_matrix['RESULT'].append(path[len(path)-1])

  return dict_matrix



from treelib import Node, Tree
def find_parent(column, df):
  j = list(df.columns).index(column)
  if j == 0:
    return None
  else:
    i=0
    while df[column][i] == '*':
      i+=1
    j-=1
    while df.iloc[i, j] == '*':
      j-=1
    return df.iloc[i, j]

def find_parent_for_result(ans, df):
  i = list(df['RESULT']).index(ans)
  j = list(df.columns).index('RESULT')
  j -=1
  while df.iloc[i, j] == '*':
    j -= 1
  return df.iloc[i, j]

def matrix_to_tree(matrix):
  from treelib import Node, Tree
  tree = Tree()
  #tree.create_node("Какой вид информационной литературы Вас интересует?", "raznovid")  # root node
  for column in matrix.columns:
    if column == 'RESULT':
      answers = list(set(matrix[column]))
      for answer in answers:
        tree.create_node(answer, answer, parent = find_parent_for_result(answer, matrix))

    else:
      tree.create_node(column, column, parent=find_parent(column, matrix))
      answers = list(set(matrix[column]))

      for answer in answers:
        if answer != '*':
          tree.create_node(answer, answer, parent=column)
          #print_save_tree(tree, 'tree1.txt')


  return tree


def save_tree_to_json(tree, filepath):
  with open(filepath, "w", encoding='utf-8') as write_file:
    json.dump(tree.to_dict(), write_file, ensure_ascii=False)

def LoadTreeJSON(loadpath_json=None):
    # if loadpath_json is None:
    #    loadpath_json = GetFilePathJSON()
    # if loadpath_json is None:
    #   return
    print("function started")
    with open(loadpath_json, encoding='utf-8') as file:
      print("file opened")
      tree = Tree()
      data = json.load(file)
      print("data loaded")
      for key1, value1 in data.items():
        node1 = PurePosixPath(key1)
        tree.create_node(tag=key1, identifier=str(node1), parent=None)
        for list1 in value1['children']:
          for key2, value2 in list1.items():
            node2 = PurePosixPath(key1, key2)
            tree.create_node(tag=key2, identifier=str(node2), parent=str(node1))
            for list2 in value2['children']:
              for key3, value3 in list2.items():
                node3 = PurePosixPath(key1, key2, key3)
                tree.create_node(tag=key3, identifier=str(node3), parent=str(node2))
                for list3 in value3['children']:
                  if isinstance(list3, dict):  # Process Only Filled Directories
                    for key4, value4 in list3.items():
                      node4 = PurePosixPath(key1, key2, key3, key4)
                      tree.create_node(tag=key4, identifier=str(node4), parent=str(node3))
                      for list4 in value4['children'][0:]:
                        node5 = PurePosixPath(key1, key2, key3, key4, list4)
                        tree.create_node(tag=list4, identifier=str(node5), parent=str(node4))
    return tree

def save_to_xlsx(df, filename):
  df.to_excel(filename, index=False)

def load_from_xlsx(filename):
  return pd.read_excel(filename)

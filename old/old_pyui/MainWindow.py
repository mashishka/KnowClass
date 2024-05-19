import codecs
import logging as log
import os
from pathlib import Path
from tempfile import TemporaryDirectory

# import pandas as pd
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi

from data_utils.core import DataBase
from old_pyui.ExamplesModel import ExamplesModel
from old_pyui.utils import error_window

# from treelib import Node, Tree  # type: ignore


# TODO: обработка ошибок валидации
# TODO: обработка отмены открытия файла/не существования файла
class MainUI(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("ui/MainWindow.ui", self)  # ui/Fake.iu

        # ui
        self.tree_open_menu: QMenu
        self.matrix_open_menu: QMenu
        self.beginConsultingButton: QPushButton
        self.matrix_tableView: QTableView
        self.tree_label: QLabel
        self.layout: QLayout

        # fields
        #### self._tree = Tree()
        self._comboboxes: list[QComboBox] = []
        self._ans: str = ""

        # connetions
        self.tree_open_menu.triggered.connect(self.treeOpenPressed)
        self.matrix_open_menu.triggered.connect(self.matrixOpenPressed)
        self.beginConsultingButton.clicked.connect(self.Consulting)

        self._data: DataBase | None = None

        # self.actionNew.triggered.connect(self.newPressed)

    @error_window
    def treeOpenPressed(self, *args):
        fname = QFileDialog.getOpenFileNames(self)[0][0]

        #### self._tree = tree_utils.LoadTreeJSON(fname)
        ####
        #### self.tree_label.setText(self._get_tree_label())
        #### self.layout = QtWidgets.QGridLayout()
        #### self.layout.addWidget(self.tree_label, 0, 0)
        #### self.setLayout(self.layout)
        ####
        #### self._matrix = utils.to_matrix(self._tree)
        #### log.debug(self._matrix)
        #### model = PandasModel(self._matrix)
        #### self.matrix_tableView.setModel(model)

    @error_window
    def matrixOpenPressed(self, *args):
        fname = QFileDialog.getOpenFileName(self)[0]
        path = Path(fname)
        log.debug(f"file was chosen {path}")
        self._data = DataBase.load(path)
        log.debug(f"loaded {self._data}")
        # ... менять модель каждый раз не надо?...
        model = ExamplesModel(self._data)
        self.matrix_tableView.setModel(model)
        # # matrix = utils.load_from_xlsx(fname)
        # # matrix = pd.read_excel(fname) #######
        # with codecs.open(fname, 'r', encoding='utf-8') as f:
        #     self._matrix = pd.read_excel(fname, engine='openpyxl')
        # log.debug('matrix was loaded')
        # log.debug(self._matrix)
        # model = PandasModel(self._matrix)
        # self.matrix_tableView.setModel(model)
        # log.debug('matrix was loaded')

        # self._tree = utils.to_tree(self._matrix)

        # self.tree_label.setText(self._get_tree_label())
        # self.layout = QtWidgets.QGridLayout()
        # self.layout.addWidget(self.tree_label, 0, 0)
        # self.setLayout(self.layout)

    @error_window
    def Consulting(self, *args):
        log.debug("ну типа начали консультацию")
        tree_dict = self._tree.to_dict()
        log.debug("сделали из дерева словарь. посмотрите какой словарь")
        log.debug(f"{tree_dict}")
        flag = True
        i = 0
        question = ""
        answers = []

        # for k, v in tree_dict.items():
        # question = k
        # answers = [list(tree_dict[question]['children'][i].keys())[0] for i in
        #           range(len(tree_dict[question]['children']))]
        # log.debug(f"{question}")
        # log.debug(f"{answears}")
        while flag:
            if type(tree_dict) != dict:  # если консультация закончилась:
                self._create_question_label(i, "Рекомендованная литература:")
                for answer in tree_dict:
                    i += 1
                    self._create_question_label(i, answer)
                i += 1
                self._create_question_label(i, "Консультация закончена")
                flag = False
            else:
                for k, v in tree_dict.items():
                    question = k
                    answers = [
                        list(tree_dict[question]["children"][i].keys())[0]
                        for i in range(len(tree_dict[question]["children"]))
                    ]
                log.debug(f"{question}")
                log.debug(f"{answers}")
                self._create_question_label(i, question)
                self._create_answer_comboBox(i, answers)
                log.debug("пытаемся получить ответ...")
                self._comboboxes[-1].currentIndexChanged.connect(
                    self.onCurrentIndexChanged
                )
                answer = self._ans
                log.debug(f"ответ получен: {answer}")

                i = answers.index(answer)
                if (
                    type(tree_dict[question]["children"][i][answer]["children"][0])
                    == dict
                ):
                    tree_dict = tree_dict[question]["children"][i][answer]["children"][
                        0
                    ]
                else:
                    tree_dict = tree_dict[question]["children"][i][answer]["children"]
                i += 1

    @pyqtSlot(int)
    @error_window
    def onCurrentIndexChanged(self, ix):
        log.debug("changed")
        text = self._comboboxes[-1].currentText()
        log.debug(f"{text}")
        self._ans = text
        # return text

    # https: // stackoverflow.com / questions / 48071926 / pyqt - combobox - print - output - upon - changed

    def _create_question_label(self, i, text):
        label = QLabel(self)
        log.debug("label сделан")
        label.setText(text)
        log.debug("текст написан")
        label.setGeometry(60, 60 + i * 120, 700, 30)
        log.debug("размер задан")
        label.show()
        log.debug("показан")

    def _create_answer_comboBox(self, i, answers):
        comboBox = QComboBox()
        comboBox.addItems(answers)
        comboBox.setGeometry(60, 120 + i * 120, 700, 30)
        comboBox.setCurrentIndex(-1)
        # log.debug("пытаемся сконнектить с onCurrentIndexChanged")

        comboBox.show()
        self._comboboxes.append(comboBox)
        log.debug("комбобокс сделан")

    def _get_tree_label(self) -> str:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "tree.txt"
            self._tree.save2file(path)
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

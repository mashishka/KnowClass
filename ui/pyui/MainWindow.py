import codecs
import logging as log
import os
from pathlib import Path, PurePath
from tempfile import TemporaryDirectory

# import pandas as pd
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QDir, QSettings, QModelIndex, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi  # type: ignore

from data_utils.controllers.TreeController import TreeController
from data_utils.core import DataBase

from tree.TreeClass import _DecisionNode, TreeType, is_leaf
from tree.create_tree import MethodType, create_tree
from ui.pyui.Consult import ConsultDialog
from ui.pyui.ExamplesModel import ExamplesModel
from ui.pyui.FactorsModel import FactorsModel
from ui.pyui.utils import error_window

# from treelib import Node, Tree  # type: ignore


# TODO: обработка ошибок валидации
# TODO: обработка отмены открытия файла/не существования файла
# TODO: сделать свои нормальные классы диалогов (с нормальными размерами)
class MainUI(QMainWindow):
    # ui
    file_open_action: QAction
    file_create_action: QAction
    file_close_action: QAction
    file_save_action: QAction
    file_last_menu: QMenu
    file_exit_action: QAction

    consult_run_action: QAction

    help_about_action: QAction

    # -------------------------------

    # definition tab
    definition_table: QTableView

    add_factor_button: QPushButton
    add_value_button: QPushButton
    change_text_button: QPushButton
    # change_name_button: QPushButton
    activate_factor_button: QPushButton
    move_factor_button: QPushButton
    delete_factor_button: QPushButton

    text_line: QLineEdit

    # example tab
    example_table: QTableView
    add_example_button: QPushButton
    clone_example_button: QPushButton
    change_example_button: QPushButton
    activate_example_button: QPushButton
    move_example_button: QPushButton
    delete_example_button: QPushButton

    # tree tab
    tree_widget: QTreeWidget
    status_label: QLabel
    actual_label: QLabel
    rebuild_tree_button: QPushButton
    test_tree_button: QPushButton
    tree_button_box: QFrame

    # -------------------------------

    # fields
    _data: DataBase | None = None
    _settings_name: str = "settings.ini"
    _count_last_kb: int = 5
    _tree_is_actual: bool = False

    sig_actual = pyqtSignal()

    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("ui/widgets/main.ui", self)  # ui/widgets/Fake.iu

        # механика активности факторов/примеров не реализуется
        self.activate_factor_button.setVisible(False)
        self.activate_example_button.setVisible(False)
        self.tree_button_box.setVisible(False)
        self.test_tree_button.setVisible(False)

        # connetions
        self._connect_all()

        # загрузить список последних баз
        self._set_last_menu()

        # активность кнопок
        self._update_definitions_buttons()
        self._update_examples_buttons()

    # слоты для пунктов меню
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------

    # Файл->Открыть
    @pyqtSlot()
    @error_window
    def on_open_kb(self):
        fname = QFileDialog.getOpenFileName(self)[0]

        if fname != "":
            path = PurePath(fname)
            self._open_kb(path)

    # Файл->Создать
    @pyqtSlot()
    @error_window
    def on_create_kb(self):
        name, done = QInputDialog.getText(
            self, "Создать базу знаний", "Введите имя новой базы знаний:"
        )
        if done and name != "":
            fname = QFileDialog.getExistingDirectory(
                self,
                "Выберите папку для сохранения базы знаний",
                QDir.currentPath(),
                QFileDialog.ShowDirsOnly,
            )

            path = PurePath(fname)
            file_path = path / (name + ".db")

            self._data = DataBase.create(file_path)
            self._open_kb(file_path)
        else:
            QMessageBox.information(self, "Создание базы знаний", "Имя не выбрано")

    # Файл->Закрыть
    @pyqtSlot()
    @error_window
    def on_close_kb(self):
        if self._data is not None:
            self._close_kb()

    # TODO: нужно ли реализовывать сохранение (например, через транзакции в бд)???
    # Файл->Сохранить
    @pyqtSlot()
    @error_window
    def on_save_kb(self):
        pass

    # Файл->Выход
    @pyqtSlot()
    @error_window
    def on_exit(self):
        self._close_kb()
        self.close()

    # Консультация->Начать консультацию
    @pyqtSlot()
    @error_window
    def on_consult(self):
        # QMessageBox.information(self, "Консультация", "В разработке")
        if self.is_actual_tree():
            ConsultDialog(self._data).exec_()
        else:
            QMessageBox.warning(
                self, "Консультация", "Текущее дерево не актуально\nПерестройте дерево"
            )

    # Справка->О программе
    @pyqtSlot()
    @error_window
    def on_about(self):
        QMessageBox.about(self, "О программе", "2ndClass v0.9 alpha")

    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------

    # слоты для Определений
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------

    # контроль кнопок определений, кроме первых двух
    @pyqtSlot(QModelIndex, QModelIndex)
    def on_def_select(self, ind: QModelIndex, prev: QModelIndex):
        if ind.isValid():
            for btn in self.__all_def_buttons([1, 2]):
                btn.setEnabled(True)
        else:
            for btn in self.__all_def_buttons([1, 2]):
                btn.setEnabled(False)

    # отображение текста текущего выделения
    @pyqtSlot(QModelIndex, QModelIndex)
    def on_text_show(self, ind: QModelIndex, prev: QModelIndex):
        mod = self.get_fact_model()
        fact_cnt = mod._factors_count()

        sel_mod = self.definition_table.selectionModel()
        col_ind_list = sel_mod.selectedColumns()

        if ind.isValid():
            if ind.column() < fact_cnt:
                # =========================================================
                if len(col_ind_list) > 0:
                    # выбран фактор (весь столбец)
                    self.text_line.setText(mod.get_fact_info(ind.column())[1])
                else:
                    # выбрано значение фактора
                    self.text_line.setText(mod.get_fact_val_info(ind.row(), ind.column())[1])
                # =========================================================
            else:
                # =========================================================
                if len(col_ind_list) > 0:
                    # выбран столбец результатов (весь)
                    self.text_line.setText(mod.get_result_text())
                else:
                    # выбрано значение результата
                    self.text_line.setText(mod.get_result_val_info(ind.row())[1])
                # =========================================================
        else:
            self.text_line.setText("")

    # Добавить фактор
    @pyqtSlot()
    @error_window
    def on_add_factor(self):
        name, done = QInputDialog.getText(self, "Создать фактор", "Введите имя нового фактора:")
        if done and name != "":
            text, done_t = QInputDialog.getMultiLineText(
                self, "Создать фактор", "Введите текст нового фактора:"
            )
            if done_t:
                mod = self.get_fact_model()
                mod.add_factor(name, text)
            else:
                QMessageBox.information(self, "Фактор", "Отмена")
        else:
            pass

    # Добавить значение
    @pyqtSlot()
    @error_window
    def on_add_value(self):
        # TODO: сделать адаптивные названия у диалогов (в зависимости от выбора)
        ind = self.definition_table.currentIndex()
        mod = self.get_fact_model()
        fact_cnt = mod._factors_count()
        # =========================================================
        if ind.isValid() and ind.column() < fact_cnt:
            name, done = QInputDialog.getText(
                self, "Создать значение фактора", "Введите имя нового значения фактора:"
            )
            if done and name != "":
                text, done_t = QInputDialog.getMultiLineText(
                    self,
                    "Создать значение фактора",
                    "Введите текст нового значения фактора:",
                )
                if done_t:
                    mod.add_factor_value(name, text, ind.column())
                else:
                    # QMessageBox.information(self, "Фактор", "Отмена")
                    pass
            else:
                # QMessageBox.information(self, "Фактор", "Имя не выбрано")
                pass
        # =========================================================
        else:
            name, done = QInputDialog.getText(
                self, "Создать результат", "Введите имя нового значения результата:"
            )
            if done and name != "":
                text, done_t = QInputDialog.getMultiLineText(
                    self,
                    "Создать результат",
                    "Введите текст нового значения результата:",
                )
                if done_t:
                    mod.add_result_value(name, text)
                else:
                    # QMessageBox.information(self, "Результат", "Отмена")
                    pass
            else:
                # QMessageBox.information(self, "Результат", "Имя не выбрано")
                pass

    # Изменить текст
    @pyqtSlot()
    @error_window
    def on_change_text(self):
        ind = self.definition_table.currentIndex()
        mod = self.get_fact_model()
        fact_cnt = mod._factors_count()

        sel_mod = self.definition_table.selectionModel()
        col_ind_list = sel_mod.selectedColumns()

        if ind.isValid():
            if ind.column() < fact_cnt:
                # =========================================================
                if len(col_ind_list) > 0:
                    # выбран фактор (весь столбец)
                    text, done_t = QInputDialog.getMultiLineText(
                        self,
                        "Изменить текст фактора",
                        "Введите новый текст фактора:",
                        mod.get_fact_info(ind.column())[1],
                    )
                    if done_t:
                        if mod.set_fact_text(ind.column(), text):
                            self.text_line.setText(text)
                    else:
                        # QMessageBox.information(self, "", "Отмена")
                        pass
                elif mod._check_model_index(ind):
                    # выбрано значение, причём с корректным индексом
                    text, done_t = QInputDialog.getMultiLineText(
                        self,
                        "Изменить текст значения",
                        "Введите новый текст значения:",
                        mod.get_fact_val_info(ind.row(), ind.column())[1],
                    )
                    if done_t:
                        if mod.set_fact_val_text(ind.row(), ind.column(), text):
                            self.text_line.setText(text)
                    else:
                        # QMessageBox.information(self, "", "Отмена")
                        pass
                # =========================================================
            else:
                # =========================================================
                if len(col_ind_list) > 0:
                    # выбран результат (весь столбец)
                    text, done_t = QInputDialog.getMultiLineText(
                        self,
                        "Изменить текст результата",
                        "Введите новый текст результата:",
                        mod.get_result_text(),
                    )
                    if done_t:
                        if mod.set_result_text(text):
                            self.text_line.setText(text)
                    else:
                        # QMessageBox.information(self, "", "Отмена")
                        pass
                elif mod._check_model_index(ind):
                    # выбрано значение результата, причём с корректным индексом
                    text, done_t = QInputDialog.getMultiLineText(
                        self,
                        "Изменить текст значения",
                        "Введите новый текст значения:",
                        mod.get_result_val_info(ind.row())[1],
                    )
                    if done_t:
                        if mod.set_result_val_text(ind.row(), text):
                            self.text_line.setText(text)
                    else:
                        # QMessageBox.information(self, "", "Отмена")
                        pass
                # =========================================================

        else:
            self.text_line.setText("")

    # Изменить имя
    # @pyqtSlot()
    # @error_window
    # def on_change_name(self):
    #     QMessageBox.information(self, "Изменить имя", "В разработке")

    # Активировать
    @pyqtSlot()
    @error_window
    def on_activate_factor(self):
        QMessageBox.information(self, "Активировать", "В разработке")

    # Переместить
    @pyqtSlot()
    @error_window
    def on_move_factor(self):
        ind = self.definition_table.currentIndex()
        mod = self.get_fact_model()
        fact_cnt = mod._factors_count()

        sel_mod = self.definition_table.selectionModel()
        col_ind_list = sel_mod.selectedColumns()

        # =========================================================
        if len(col_ind_list) > 0:
            # выбраны целые столбцы, перемещаем последний
            if ind.column() == fact_cnt:
                # столбец RESULT неперемещаемый
                return

            cur_fact_name, cur_fact_text = mod.get_fact_info(ind.column())
            pos, done_t = QInputDialog.getInt(
                self,
                f"Переместить фактор {cur_fact_name}",
                "Введите новую позицию фактора (начиная с нуля):",
                ind.column(),
                0,
            )
            if done_t:
                if not mod.move_factor_to(ind.column(), pos):
                    QMessageBox.warning(
                        self,
                        f"Переместить фактор {cur_fact_name}",
                        "Некорректная позиция",
                    )
            else:
                # QMessageBox.information(self, "", "Отмена")
                pass

        # =========================================================
        elif mod._check_model_index(ind):
            # выбраны ячейки, перемещаем последнюю
            if ind.column() == fact_cnt:
                cur_val_name, cur_val_text = mod.get_result_val_info(ind.row())
            else:
                cur_val_name, cur_val_text = mod.get_fact_val_info(ind.row(), ind.column())

            pos, done_t = QInputDialog.getInt(
                self,
                f"Переместить значение {cur_val_name}",
                "Введите новую позицию значения (начиная с нуля):",
                ind.row(),
                0,
            )
            if done_t:
                if not mod.move_value_to(ind.row(), ind.column(), pos):
                    QMessageBox.warning(
                        self,
                        f"Переместить значение {cur_val_name}",
                        "Некорректная позиция",
                    )
            else:
                # QMessageBox.information(self, "", "Отмена")
                pass

    # Удалить
    # Удаляет факторы или значения в зависимости от выбора
    @pyqtSlot()
    @error_window
    def on_delete_factor(self):
        mod = self.get_fact_model()
        sel_mod = self.definition_table.selectionModel()
        col_ind_list = sel_mod.selectedColumns()

        # =========================================================
        if len(col_ind_list) > 0:
            # выбраны целые столбцы, удаляем факторы,
            # если попался столбец результатов, всё из него сносим
            ln = len(col_ind_list)
            if ln % 10 == 1 and not 11 <= ln % 100 <= 14:
                fct_str = "фактор"
            elif 2 <= ln % 10 <= 4 and not 11 <= ln % 100 <= 14:
                fct_str = "фактора"
            else:
                fct_str = "факторов"

            res_btn = QMessageBox.warning(
                self,
                "Удаление",
                f"Вы уверены, что хотите удалить {ln} {fct_str}?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if res_btn == QMessageBox.Yes:

                # индексы должны быть отсортированы по убыванию номера столбца
                def by_index_col(ind: QModelIndex):
                    return ind.column()

                col_ind_list.sort(key=by_index_col, reverse=True)
                mod.delete_columns(col_ind_list)
            else:
                return
        # =========================================================
        else:
            # выбраны ячейки, удаляем значения
            all_ind_list = sel_mod.selectedIndexes()
            ln = len(all_ind_list)
            if ln % 10 == 1 and not 11 <= ln % 100 <= 14:
                val_str = "значение"
            elif 2 <= ln % 10 <= 4 and not 11 <= ln % 100 <= 14:
                val_str = "значения"
            else:
                val_str = "значений"
            res_btn = QMessageBox.warning(
                self,
                "Удаление",
                f"Вы уверены, что хотите удалить {ln} {val_str}?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if res_btn == QMessageBox.Yes:

                # индексы должны быть отсортированы по убыванию номера строки
                def by_index_row(ind: QModelIndex):
                    return ind.row()

                all_ind_list.sort(key=by_index_row, reverse=True)
                mod.delete_values(all_ind_list)
            else:
                return

    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------

    # слоты для Примеров
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------

    # контроль всех кнопок, кроме первой
    @pyqtSlot(QModelIndex, QModelIndex)
    def on_ex_select(self, ind: QModelIndex, prev: QModelIndex):
        if ind.isValid():
            for btn in self.__all_ex_buttons([1]):
                btn.setEnabled(True)
        else:
            for btn in self.__all_ex_buttons([1]):
                btn.setEnabled(False)

    # Добавить пример
    @pyqtSlot()
    @error_window
    def on_add_example(self):
        mod = self.get_ex_model()
        lst = mod.get_list_res_val()
        name, done = QInputDialog.getItem(
            self,
            "Создать пример",
            "Выберите значение результата для примера:",
            lst,
        )
        if done and name != "":
            mod.add_example(name)
        else:
            QMessageBox.information(self, "Результат", "Имя не выбрано")

    # Дублировать
    @pyqtSlot()
    @error_window
    def on_clone_example(self):
        mod = self.get_ex_model()
        cur_ind = self.example_table.currentIndex()
        mod.clone_ex(cur_ind.row())

    # Изменить
    @pyqtSlot()
    @error_window
    def on_change_example(self):
        mod = self.get_ex_model()
        cur_ind = self.example_table.currentIndex()
        f_cnt = mod._factors_count()
        # =========================================================
        if cur_ind.column() < f_cnt:
            # изменить значение фактора
            f_name, val_list = mod.get_list_fact_val(cur_ind.column())
            # TODO: в таких диалогах чекать возвращаемое имя -- он позволяет вернуть любую строку
            name, done = QInputDialog.getItem(
                self,
                f"Фактор {f_name}",
                "Выберите значение фактора для примера:",
                val_list,
            )
            if done:
                mod.change_factor_val(cur_ind.row(), f_name, name)
            else:
                pass
        # =========================================================
        elif cur_ind.column() == f_cnt:
            # изменить вес примера
            # TODO: изменить локаль, чтобы показывало точку
            # TODO: как-то добавить параметр steps (=0.05)
            weight, done = QInputDialog.getDouble(
                self,
                f"Вес примера",
                "Выберите значение веса для примера:",
                1.0,
                decimals=2,
            )
            if done:
                mod.change_ex_weight(cur_ind.row(), weight)
            else:
                pass
        # =========================================================
        else:
            # изменить значение результата примера
            lst = mod.get_list_res_val()
            name, done = QInputDialog.getItem(
                self,
                f"Результат",
                "Выберите значение результата для примера:",
                lst,
            )
            if done:
                mod.change_ex_result(cur_ind.row(), name)
            else:
                pass
        # =========================================================

    # Активировать
    @pyqtSlot()
    @error_window
    def on_activate_example(self):
        QMessageBox.information(self, "Активировать", "В разработке")

    # Переместить
    @pyqtSlot()
    @error_window
    def on_move_example(self):
        mod = self.get_ex_model()
        cur_ind = self.example_table.currentIndex()

        pos, done_t = QInputDialog.getInt(
            self,
            f"Переместить пример {str(cur_ind.row() + 1)}",
            "Введите новый номер примера (начиная с единицы):",
            cur_ind.row() + 1,
            1,
        )
        if done_t:
            if not mod.move_example_to(cur_ind.row(), pos - 1):
                QMessageBox.warning(
                    self,
                    f"Переместить пример {str(cur_ind.row() + 1)}",
                    "Некорректная позиция",
                )
        else:
            # QMessageBox.information(self, "", "Отмена")
            pass

    # Удалить
    @pyqtSlot()
    @error_window
    def on_delete_example(self):
        sel_mod = self.example_table.selectionModel()
        row_ind_list = sel_mod.selectedRows()

        correct_ind_list: list[QModelIndex] = []  # type: ignore

        # =========================================================
        if len(row_ind_list) > 0:
            # выбраны целые строки
            correct_ind_list = list(reversed(row_ind_list))

        # =========================================================
        else:
            # выбраны ячейки, удаляем целиком строки, где выделены значения
            all_ind_list = sel_mod.selectedIndexes()
            tmp_s: set[int] = set()  # type: ignore

            def non_repeat_ind(ind: QModelIndex):
                if ind.row() not in tmp_s:
                    tmp_s.add(ind.row())
                    return True
                else:
                    return False

            correct_ind_list = list(filter(non_repeat_ind, reversed(all_ind_list)))

        # =========================================================

        ln = len(correct_ind_list)

        # индексы должны быть отсортированы по убыванию номера строки
        def by_index_row(ind: QModelIndex):
            return ind.row()

        correct_ind_list.sort(key=by_index_row, reverse=True)

        if ln % 10 == 1 and not 11 <= ln % 100 <= 14:
            rw_str = "строку"
        elif 2 <= ln % 10 <= 4 and not 11 <= ln % 100 <= 14:
            rw_str = "строки"
        else:
            rw_str = "строк"

        res_btn = QMessageBox.warning(
            self,
            "Удаление",
            f"Вы уверены, что хотите удалить {ln} {rw_str}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if res_btn == QMessageBox.Yes:
            mod = self.get_ex_model()
            mod.delete_examples(correct_ind_list)
        else:
            return

    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------

    # слоты для Дерева
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------

    def load_tree(self):
        tree = TreeController.get(self._data).data
        if tree is not None:
            self.show_tree(tree)
            self.sig_actual.emit()

    def show_tree(self, tree: _DecisionNode):
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(["Rules", "Results"])

        # это простой метод обхода
        def tree_print(root_item: QTreeWidgetItem, tree: TreeType):

            if is_leaf(tree):
                # print(tree.label)
                widg_item = QTreeWidgetItem(root_item)

                widg_item.setText(1, tree.label)  # type: ignore
                root_item.addChild(widg_item)
            else:
                # print(tree)
                # print(tree.children)
                for atr, child in tree.children.items():
                    widg_item = QTreeWidgetItem(root_item)

                    if isinstance(child, list):
                        widg_item.setText(0, f"{atr}: ")
                        root_item.addChild(widg_item)
                        for node in child:
                            # print("type node", type(node))
                            tree_print(widg_item, node)

                    else:
                        # print(child, type(child))
                        widg_item.setText(0, f"{atr}: {child.attribute}??")

                        tree_print(widg_item, child)
                        root_item.addChild(widg_item)

        root_item = QTreeWidgetItem(self.tree_widget)
        root_item.setText(0, tree.attribute)

        tree_print(root_item, tree)

        self.tree_widget.expandAll()

    @pyqtSlot()
    @error_window
    def on_rebuild_tree_button_clicked(self, *args, **kwargs):
        name, done = QInputDialog.getItem(
            self,
            f"Режим",
            "Выберите способ построения дерева:",
            ["Optimize", "Left-toRight"],
            editable=False,
        )
        if done:
            if name == "Optimize":
                meth = MethodType.optimize
            else:
                meth = MethodType.left_to_right
        else:
            return

        self.tree_widget.clear()
        create_tree(self._data, meth)
        tree = TreeController.get(self._data).data
        self.sig_actual.emit()
        self.show_tree(tree)
        self.actual_label.setText(f"{self.actual_label.text()}; метод {name}")

    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------

    # все коннекты главного окна
    def _connect_all(self):
        # connect File menu
        self.file_open_action.triggered.connect(self.on_open_kb)
        self.file_create_action.triggered.connect(self.on_create_kb)
        self.file_close_action.triggered.connect(self.on_close_kb)
        self.file_save_action.triggered.connect(self.on_save_kb)
        self.file_exit_action.triggered.connect(self.on_exit)

        # connect Consult menu
        self.consult_run_action.triggered.connect(self.on_consult)

        # connect Help menu
        self.help_about_action.triggered.connect(self.on_about)

        # connect Definitions buttons
        self.add_factor_button.clicked.connect(self.on_add_factor)
        self.add_value_button.clicked.connect(self.on_add_value)
        self.change_text_button.clicked.connect(self.on_change_text)
        # self.change_name_button.clicked.connect(self.on_change_name)
        self.activate_factor_button.clicked.connect(self.on_activate_factor)
        self.move_factor_button.clicked.connect(self.on_move_factor)
        self.delete_factor_button.clicked.connect(self.on_delete_factor)

        # connect Examples buttons
        self.add_example_button.clicked.connect(self.on_add_example)
        self.clone_example_button.clicked.connect(self.on_clone_example)
        self.change_example_button.clicked.connect(self.on_change_example)
        self.activate_example_button.clicked.connect(self.on_activate_example)
        self.move_example_button.clicked.connect(self.on_move_example)
        self.delete_example_button.clicked.connect(self.on_delete_example)

        # TODO: connect Tree buttons

    # безопасно закрыть текущую базу
    def _close_kb(self):
        self.definition_table.setModel(None)
        self.example_table.setModel(None)
        self._data.close()
        self._data = None

        self._update_buttons()

        self.status_label.setText("База знаний не задана")
        self.actual_label.setText("")
        self.text_line.setText("")
        self.tree_widget.clear()

    # открыть новую базу (старая закрывается)
    def _open_kb(self, path: PurePath):
        if self._data is not None:
            self._close_kb()

        log.debug(f"file was chosen {path}")
        try:
            self._data = DataBase.load(path)
        except Exception as err:
            QMessageBox.critical(self, "Внимание!", f"Ошибка при открытии базы знаний!")
            return
        log.debug(f"loaded {self._data}")
        # ... менять модель каждый раз не надо?...

        self._update_models()

        self.status_label.setText("База знаний: " + path.name)

        self._update_last_kb(path)
        self._update_buttons()

        self.load_tree()

    # обновить список последних открытых баз
    def _update_last_kb(self, kb_path: PurePath):
        sett = QSettings(self._settings_name, QSettings.Format.IniFormat)

        lst: list[str] | None = sett.value("last")
        str_path: str = str(kb_path)

        if lst is not None:
            if str_path in lst:
                lst.remove(str_path)
            else:
                if len(lst) == self._count_last_kb:
                    lst.pop(-1)
            lst.insert(0, str_path)
        else:
            lst = []
            lst.append(str_path)

        sett.setValue("last", lst)

        # установить обновлённый список
        self._set_last_menu()

    # установить новый список последних открытых баз
    def _set_last_menu(self):
        sett = QSettings(self._settings_name, QSettings.Format.IniFormat)
        lst: list[str] | None = sett.value("last")  # type: ignore

        if not self.file_last_menu.isEmpty():
            for act in self.file_last_menu.actions():
                act.disconnect()
            self.file_last_menu.clear()

        if lst is not None:
            for str_path in lst:
                act = QAction(str_path, self)
                act.triggered.connect(
                    # имитация захвата по значению в лямбде
                    lambda magic, p=str_path: self._open_kb(PurePath(p))
                )
                self.file_last_menu.addAction(act)
        else:
            return

    # создать и подключить модели
    def _update_models(self):
        # модели и коннекты к ним
        modelf = FactorsModel(self._data)
        modele = ExamplesModel(self._data)

        # некоторые изменения в факторах влияют на примеры
        modelf.sig_add_factor.connect(modele.on_add_factor)
        modelf.sig_delete_factor.connect(modele.on_delete_factor)
        modelf.sig_before_delete_result.connect(modele.on_before_delete)
        modelf.sig_after_delete_result.connect(modele.on_after_delete)
        modelf.sig_invalidate.connect(modele.sig_invalidate)
        modelf.sig_invalidate.connect(self.set_non_actual_tree)
        modele.sig_invalidate.connect(self.set_non_actual_tree)
        self.sig_actual.connect(self.set_actual_tree)

        # таблица факторов
        self.definition_table.setModel(None)
        self.definition_table.setModel(modelf)
        self.definition_table.selectionModel().currentChanged.connect(self.on_def_select)
        self.definition_table.selectionModel().currentChanged.connect(self.on_text_show)

        # таблица примеров
        self.example_table.setModel(None)
        self.example_table.setModel(modele)
        self.example_table.selectionModel().currentChanged.connect(self.on_ex_select)

        # TODO: отображение дерева тоже здесь

        self._update_buttons()

    # обновить состояние кнопок Определений в зависимости от состояния текущей базы
    def _update_definitions_buttons(self):
        if self._data is None:
            for btn in self.__all_def_buttons():
                btn.setEnabled(False)
        else:
            for btn in self.__all_def_buttons([i for i in range(3, 7)]):
                btn.setEnabled(True)

    # получить список кнопок Определений
    # exclude_list -- список номеров (с 1) кнопок, которые не надо возвращать
    def __all_def_buttons(self, exclude_list: list[int] = []) -> list[QPushButton]:
        lst: list[QPushButton] = []

        if 1 not in exclude_list:
            lst.append(self.add_factor_button)
        if 2 not in exclude_list:
            lst.append(self.add_value_button)
        if 3 not in exclude_list:
            lst.append(self.change_text_button)
        # if 4 not in exclude_list:
        #     lst.append(self.change_name_button)
        if 4 not in exclude_list:
            lst.append(self.activate_factor_button)
        if 5 not in exclude_list:
            lst.append(self.move_factor_button)
        if 6 not in exclude_list:
            lst.append(self.delete_factor_button)

        return lst

    # обновить состояние кнопок Примеров в зависимости от состояния текущей базы
    def _update_examples_buttons(self):
        if self._data is None:
            for btn in self.__all_ex_buttons():
                btn.setEnabled(False)
        else:
            for btn in self.__all_ex_buttons([i for i in range(2, 7)]):
                btn.setEnabled(True)

    def _update_tree_buttons(self):
        self.rebuild_tree_button.setDisabled(self._data is None)

    def _update_buttons(self):
        self._update_definitions_buttons()
        self._update_examples_buttons()
        self._update_tree_buttons()

    # получить список кнопок Примеров
    # exclude_list -- список номеров (с 1) кнопок, которые не надо возвращать
    def __all_ex_buttons(self, exclude_list: list[int] = []) -> list[QPushButton]:
        lst: list[QPushButton] = []

        if 1 not in exclude_list:
            lst.append(self.add_example_button)
        if 2 not in exclude_list:
            lst.append(self.clone_example_button)
        if 3 not in exclude_list:
            lst.append(self.change_example_button)
        if 4 not in exclude_list:
            lst.append(self.activate_example_button)
        if 5 not in exclude_list:
            lst.append(self.move_example_button)
        if 6 not in exclude_list:
            lst.append(self.delete_example_button)

        return lst

    def get_fact_model(self) -> FactorsModel:
        return self.definition_table.model()  # type: ignore

    def get_ex_model(self) -> ExamplesModel:
        return self.example_table.model()  # type: ignore

    def is_actual_tree(self):
        return self._tree_is_actual and TreeController.get(self._data).data is not None

    @pyqtSlot()
    def set_actual_tree(self):
        self._tree_is_actual = True
        self.actual_label.setText("Дерево актуально")

    @pyqtSlot()
    def set_non_actual_tree(self):
        self._tree_is_actual = False
        self.actual_label.setText("Дерево не актуально")

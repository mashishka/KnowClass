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

from ui.pyui.dialogs.AskNameText import AskNameText, AskType
from ui.pyui.dialogs.AskNumber import AskNumber
from ui.pyui.dialogs.AskItems import AskItems
from ui.pyui.dialogs.AskWorkMode import AskWorkMode

from data_utils.controllers.TreeController import TreeController
from data_utils.core import DataBase

from tree.TreeClass import _DecisionNode, _LeafNode, TreeType, MethodType
from tree.utils import create_tree, completeness

from ui.pyui.Consult import ConsultDialog
from ui.pyui.ExamplesModel import ExamplesModel
from ui.pyui.FactorsModel import FactorsModel
from ui.pyui.utils import error_window, ExtendedTreeItem

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
    mark_button: QPushButton
    expand_button: QPushButton
    collapse_button: QPushButton
    delete_tree_button: QPushButton

    # -------------------------------

    # fields
    _data: DataBase | None = None
    _settings_name: str = "settings.ini"
    _count_last_kb: int = 5

    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("ui/widgets/main.ui", self)  # ui/widgets/Fake.iu

        # механика активности факторов/примеров не реализуется
        self.activate_factor_button.setVisible(False)
        self.activate_example_button.setVisible(False)

        # connetions
        self._connect_all()

        # загрузить список последних баз
        self._set_last_menu()

        # активность кнопок
        self._update_buttons()

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

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Выберите имя для базы знаний", QDir.currentPath()
        )

        if file_path != "":
            file_path = PurePath(file_path + ".db")

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
            mode, done, val = AskWorkMode.get_mode(self)
            if done:
                ConsultDialog(self, self._data, mode, val).exec_()

        else:
            QMessageBox.warning(
                self, "Консультация", "Текущее дерево не актуально\nПерестройте дерево"
            )

    # Справка->О программе
    @pyqtSlot()
    @error_window
    def on_about(self):
        QMessageBox.about(self, "О программе", "2ndClass v0.9.4 alpha")

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

    # отображение текста текущего фактора
    @pyqtSlot(int)
    def on_col_text_show(self, col_pos: int):
        mod = self.get_fact_model()
        fact_cnt = mod._factors_count()

        if col_pos < fact_cnt:
            self.text_line.setText(mod.get_fact_info(col_pos)[1])
        else:
            self.text_line.setText(mod.get_result_text())

    # отображение текста текущего выделения
    @pyqtSlot(QModelIndex, QModelIndex)
    def on_item_text_show(self, ind: QModelIndex, prev: QModelIndex):
        mod = self.get_fact_model()
        fact_cnt = mod._factors_count()

        if not ind.isValid():
            self.text_line.setText("")
            return

        if ind.column() < fact_cnt:
            self.text_line.setText(mod.get_fact_val_info(ind.row(), ind.column())[1])
        else:
            self.text_line.setText(mod.get_result_val_info(ind.row())[1])

    # Добавить фактор
    @pyqtSlot()
    @error_window
    def on_add_factor(self):
        name, text, done = AskNameText.get_info(
            self, "Создать фактор", "Введите текст фактора:", AskType.all
        )
        if done:
            mod = self.get_fact_model()
            mod.add_factor(name, text)

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
            name, text, done = AskNameText.get_info(
                self,
                "Создать значение фактора",
                "Введите текст нового значения фактора:",
                AskType.all,
            )
            if done:
                mod.add_factor_value(name, text, ind.column())
        # =========================================================
        else:
            name, text, done = AskNameText.get_info(
                self,
                "Создать результат",
                "Введите текст нового значения результата:",
                AskType.all,
            )
            if done:
                mod.add_result_value(name, text)

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
                    text, done = AskNameText.get_info(
                        self,
                        "Изменить текст фактора",
                        "Введите новый текст фактора:",
                        AskType.only_text,
                        mod.get_fact_info(ind.column())[1],
                    )

                    if done:
                        if mod.set_fact_text(ind.column(), text):
                            self.text_line.setText(text)
                    else:
                        pass

                elif mod._check_model_index(ind):
                    # выбрано значение, причём с корректным индексом
                    text, done = AskNameText.get_info(
                        self,
                        "Изменить текст значения",
                        "Введите новый текст значения:",
                        AskType.only_text,
                        mod.get_fact_val_info(ind.row(), ind.column())[1],
                    )

                    if done:
                        if mod.set_fact_val_text(ind.row(), ind.column(), text):
                            self.text_line.setText(text)
                    else:
                        pass
                # =========================================================
            else:
                # =========================================================
                if len(col_ind_list) > 0:
                    # выбран результат (весь столбец)
                    text, done = AskNameText.get_info(
                        self,
                        "Изменить текст результата",
                        "Введите новый текст результата:",
                        AskType.only_text,
                        mod.get_result_text(),
                    )
                    if done:
                        if mod.set_result_text(text):
                            self.text_line.setText(text)
                    else:
                        # QMessageBox.information(self, "", "Отмена")
                        pass
                elif mod._check_model_index(ind):
                    # выбрано значение результата, причём с корректным индексом
                    text, done = AskNameText.get_info(
                        self,
                        "Изменить текст значения",
                        "Введите новый текст значения:",
                        AskType.only_text,
                        mod.get_result_val_info(ind.row())[1],
                    )
                    if done:
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

            pos, done = AskNumber.get_int(
                self,
                f"Переместить фактор {cur_fact_name}",
                "Введите новую позицию фактора (начиная с нуля):",
                ind.column(),
                0,
            )

            if done:
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
                cur_val_name, cur_val_text = mod.get_fact_val_info(
                    ind.row(), ind.column()
                )

            pos, done = AskNumber.get_int(
                self,
                f"Переместить значение {cur_val_name}",
                "Введите новую позицию значения (начиная с нуля):",
                ind.row(),
                0,
            )
            if done:
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

        name, done = AskItems.get_item(
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

            name, done = AskItems.get_item(
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
            weight, done = AskNumber.get_double(
                self,
                f"Вес примера",
                "Выберите значение веса для примера:",
                1.0,
            )
            if done:
                mod.change_ex_weight(cur_ind.row(), weight)
            else:
                pass
        # =========================================================
        else:
            # изменить значение результата примера
            lst = mod.get_list_res_val()

            name, done = AskItems.get_item(
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

        pos, done_t = AskNumber.get_int(
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

    # загрузить дерево и отобразить
    def load_tree(self):
        root = TreeController.get(self._data).data
        if root is not None:
            self.show_tree(root.tree)
            self.set_actual_status(root.actual, root.method)
            self._update_buttons()
        else:
            self.set_none_status()

    # TODO: tree -- какой именно тип?
    # показать дерево
    def show_tree(self, tree: _DecisionNode):
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(["Rules", "Results"])

        # это простой метод обхода
        def tree_print(root_item: ExtendedTreeItem, tree: TreeType):
            if isinstance(tree, _LeafNode):
                widg_item = ExtendedTreeItem(tree.examples_list, root_item)

                widg_item.setText(1, tree.label)
                root_item.addChild(widg_item)
            else:
                for atr, child in tree.children.items():
                    if isinstance(child, list):
                        tmp_lst = []
                        for node in child:
                            tmp_lst += node.examples_list
                        widg_item = ExtendedTreeItem(tmp_lst, root_item)
                        widg_item.setText(0, f"{atr}: ")
                        root_item.addChild(widg_item)
                        for node in child:
                            tree_print(widg_item, node)

                    else:
                        widg_item = ExtendedTreeItem(child.examples_list, root_item)
                        widg_item.setText(0, f"{atr}: {child.attribute}??")

                        tree_print(widg_item, child)
                        root_item.addChild(widg_item)

        root_item = ExtendedTreeItem(tree.examples_list, self.tree_widget)
        root_item.setText(0, tree.attribute)

        tree_print(root_item, tree)

        self.tree_widget.expandAll()

    # Перестроить дерево
    @pyqtSlot()
    @error_window
    def on_rebuild_tree_button_clicked(self, *args, **kwargs):
        name, done = AskItems.get_item(
            self,
            f"Режим",
            "Выберите способ построения дерева:",
            ["Optimize", "Left-to-Right"],
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
        root = TreeController.get(self._data).data

        self.show_tree(root.tree)
        self.set_actual_status(root.actual, root.method)

        mod = self.get_ex_model()
        mod.mark_examples([])

        self._update_buttons()

    # Тест
    @pyqtSlot()
    @error_window
    def on_test_tree_button_clicked(self, *args, **kwargs):
        root = TreeController.get(self._data).data
        marked_list = completeness(root.tree, self._data)

        if len(marked_list) > 0:
            add_str = "\n\nНеподходящие примеры помечены на вкладке Примеры"
        else:
            add_str = ""

        QMessageBox.information(
            self,
            "Тест на полноту",
            f"Количество примеров, не подходящих дереву: {len(marked_list)}. {add_str}",
        )

        mod = self.get_ex_model()
        mod.mark_examples(marked_list)

    # Пометить пример
    @pyqtSlot()
    @error_window
    def on_mark_button_clicked(self):
        marked_list = self.tree_widget.currentItem().node_examples

        mod = self.get_ex_model()
        mod.mark_examples([])
        mod.mark_examples(marked_list)
        QMessageBox.information(
            self,
            "Пометить пример",
            "Соответствующие примеры выделены на вкладке Примеры",
        )

    # TODO: добавить кнопку Снять выделение

    # Развернуть дерево
    @pyqtSlot()
    @error_window
    def on_expand_button_clicked(self):
        self.tree_widget.expandAll()

    # Свернуть дерево
    @pyqtSlot()
    @error_window
    def on_collapse_button_clicked(self):
        self.tree_widget.collapseAll()

    # Удалить дерево
    @pyqtSlot()
    @error_window
    def on_delete_tree_button_clicked(self):
        TreeController.get(self._data).data = None
        self.tree_widget.clear()
        self.set_none_status()
        self._update_buttons()

        mod = self.get_ex_model()
        mod.mark_examples([])

    @pyqtSlot(QModelIndex, QModelIndex)
    @error_window
    def mark_button_select(self, ind: QModelIndex, prev: QModelIndex):
        if ind.isValid():
            self.mark_button.setEnabled(True)
        else:
            self.mark_button.setEnabled(False)

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

        # таблица факторов
        self.definition_table.setModel(None)
        self.definition_table.setModel(modelf)
        self.definition_table.selectionModel().currentChanged.connect(
            self.on_def_select
        )
        self.definition_table.selectionModel().currentChanged.connect(
            self.on_item_text_show
        )
        self.definition_table.horizontalHeader().sectionClicked.connect(
            self.on_col_text_show
        )

        # таблица примеров
        self.example_table.setModel(None)
        self.example_table.setModel(modele)
        self.example_table.selectionModel().currentChanged.connect(self.on_ex_select)

        # TODO: отображение дерева тоже здесь
        self.tree_widget.selectionModel().currentChanged.connect(
            self.mark_button_select
        )

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
        def check_cond():
            return self._data is None or TreeController.get(self._data).data is None

        self.rebuild_tree_button.setDisabled(self._data is None)
        self.test_tree_button.setDisabled(check_cond())
        self.mark_button.setDisabled(
            check_cond() or not self.tree_widget.currentIndex().isValid()
        )
        self.expand_button.setDisabled(check_cond())
        self.collapse_button.setDisabled(check_cond())
        self.delete_tree_button.setDisabled(check_cond())

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
        root = TreeController.get(self._data).data
        return root is not None and root.actual

    @pyqtSlot()
    def set_actual_status(self, act: bool, method: MethodType):
        name = "Optimize" if method == MethodType.optimize else "Left-to-Right"
        if act:
            self.actual_label.setText(f"Дерево актуально; метод {name}")
        else:
            self.actual_label.setText(f"Дерево не актуально; метод {name}")

    @pyqtSlot()
    def set_non_actual_tree(self):
        root = TreeController.get(self._data).data
        if root is not None:
            root.actual = False
            TreeController.get(self._data).data = root
            self.set_actual_status(
                TreeController.get(self._data).data.actual,
                TreeController.get(self._data).data.method,
            )
        else:
            self.set_none_status()

    @pyqtSlot()
    def set_none_status(self):
        self.actual_label.setText("Дерево не построено")

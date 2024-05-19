import codecs
import logging as log
import os
from pathlib import Path, PurePath
from tempfile import TemporaryDirectory

# import pandas as pd
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QDir, QSettings, QModelIndex
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi  # type: ignore

from data_utils.core import DataBase
from data_utils.controllers.ExampleController import ExampleController
from data_utils.controllers.FactorController import FactorController
from data_utils.controllers.ResultController import ResultController
from data_utils.controllers.ValueController import ValueController

from pyui.ExamplesModel import ExamplesModel
from pyui.FactorsModel import FactorsModel
from pyui.utils import error_window

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
    change_name_button: QPushButton
    activate_factor_button: QPushButton
    move_factor_button: QPushButton
    delete_factor_button: QPushButton

    # example tab
    example_table: QTableView
    add_example_button: QPushButton
    clone_example_button: QPushButton
    change_example_button: QPushButton
    activate_example_button: QPushButton
    move_example_button: QPushButton
    delete_example_button: QPushButton

    # tree tab
    tree_view: QTreeView
    status_label: QLabel

    # -------------------------------

    # fields
    _data: DataBase | None = None
    _settings_name: str = "settings.ini"
    _count_last_kb: int = 5

    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("ui/main.ui", self)  # ui/Fake.iu

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

    # TODO: консультация
    # Консультация->Начать консультацию
    @pyqtSlot()
    @error_window
    def on_consult(self):
        QMessageBox.information(self, "Консультация", "В разработке")

    # Справка->О программе
    @pyqtSlot()
    @error_window
    def on_about(self):
        QMessageBox.about(self, "О программе", "2ndClass v0.1 alpha")

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

    # Добавить фактор
    @pyqtSlot()
    @error_window
    def on_add_factor(self):
        name, done = QInputDialog.getText(
            self, "Создать фактор", "Введите имя нового фактора:"
        )
        if done and name != "":
            text, done_t = QInputDialog.getMultiLineText(
                self, "Создать фактор", "Введите текст нового фактора:"
            )
            if done_t:
                res = FactorController.make(self._data, name)
                res.text = text

                cur_ind = self.definition_table.currentIndex()
                tmp_row, tmp_col = cur_ind.row(), cur_ind.column()
                # TODO: невероятный костыль, сделать
                # нормальное обновление количества столбцов при изменении в бд,
                # а не полное переподключение моделей
                self._update_models()
                self.definition_table.setCurrentIndex(
                    self.definition_table.model().createIndex(tmp_row, tmp_col)
                )
            else:
                QMessageBox.information(self, "Фактор", "Отмена")
        else:
            QMessageBox.information(self, "Фактор", "Имя не выбрано")

    # Добавить значение
    @pyqtSlot()
    @error_window
    def on_add_value(self):
        # TODO: сделать адаптивные названия у диалогов (в зависимости от выбора)
        ind = self.definition_table.currentIndex()
        fact_cnt: int = FactorController.get_count(self._data)  # type: ignore
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
                    res = FactorController.get_by_position(self._data, ind.column())
                    v_res = res.make_value(name)
                    v_res.text = text

                    cur_ind = self.definition_table.currentIndex()
                    tmp_row, tmp_col = cur_ind.row(), cur_ind.column()
                    # TODO: невероятный костыль аналогично
                    self._update_models()
                    # TODO: тоже костыль
                    self.definition_table.setCurrentIndex(
                        self.definition_table.model().createIndex(tmp_row, tmp_col)
                    )
                else:
                    QMessageBox.information(self, "Фактор", "Отмена")
            else:
                QMessageBox.information(self, "Фактор", "Имя не выбрано")
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
                    res = ResultController.get(self._data).make_value(name)
                    res.text = text
                    # TODO: невероятный костыль аналогично
                    self._update_models()
                else:
                    QMessageBox.information(self, "Результат", "Отмена")
            else:
                QMessageBox.information(self, "Результат", "Имя не выбрано")

    # Изменить текст
    @pyqtSlot()
    @error_window
    def on_change_text(self):
        QMessageBox.information(self, "Изменить текст", "В разработке")

    # Изменить имя
    @pyqtSlot()
    @error_window
    def on_change_name(self):
        QMessageBox.information(self, "Изменить имя", "В разработке")

    # Активировать
    @pyqtSlot()
    @error_window
    def on_activate_factor(self):
        QMessageBox.information(self, "Активировать", "В разработке")

    # Переместить
    @pyqtSlot()
    @error_window
    def on_move_factor(self):
        QMessageBox.information(self, "Переместить", "В разработке")

    # Удалить
    # Удаляет факторы или значения в зависимости от выбора
    @pyqtSlot()
    @error_window
    def on_delete_factor(self):
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
                for ind in reversed(col_ind_list):
                    self.__delete_by_column(ind.column())
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
                for ind in reversed(all_ind_list):
                    self.__delete_by_index(ind)
            else:
                return
        self._update_models()

    # удалить значения по индексам
    def __delete_by_index(self, index: QModelIndex):
        if index.column() < FactorController.get_count(self._data):  # type: ignore
            # удалить значение фактора
            factor = FactorController.get_by_position(self._data, index.column())  # type: ignore
            if index.row() < factor.get_values_count():
                factor.remove_value_by_position(index.row())  # type: ignore
        else:
            # удалить значение результата
            res_contr = ResultController.get(self._data)  # type: ignore
            if index.row() < res_contr.get_values_count():
                res_contr.remove_value_by_position(index.row())  # type: ignore

    # удалить столбцы по номеру
    def __delete_by_column(self, col: int):
        if col < FactorController.get_count(self._data):  # type: ignore
            # удалить весь фактор
            FactorController.remove_by_position(self._data, col)  # type: ignore
        else:
            # удалить все результаты
            res_contr = ResultController.get(self._data)  # type: ignore
            res_contr.remove_values()

    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------

    # слоты для Примеров
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------

    # онтроль всех кнопок, кроме первой
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
        res_contr = ResultController.get(self._data)
        name, done = QInputDialog.getItem(
            self,
            "Создать пример",
            "Выберите значение результата для примера:",
            [res_val.name for res_val in res_contr.get_values()],
        )
        if done and name != "":
            ExampleController.make(self._data, 1.0, res_contr.get_value(name))
        else:
            QMessageBox.information(self, "Результат", "Имя не выбрано")
        self._update_models()

    # Дублировать
    @pyqtSlot()
    @error_window
    def on_clone_example(self):
        QMessageBox.information(self, "Дублировать", "В разработке")

    # Изменить
    @pyqtSlot()
    @error_window
    def on_change_example(self):
        cur_ind = self.example_table.currentIndex()
        cur_ex = ExampleController.get_by_position(self._data, cur_ind.row())
        f_cnt = FactorController.get_count(self._data)
        # =========================================================
        if cur_ind.column() < f_cnt:
            # изменить значение фактора
            factor = FactorController.get_by_position(self._data, cur_ind.column())
            val_list: list[str] = []  # type: ignore
            val_list.append("")
            val_list += [res_val.name for res_val in factor.get_values()]
            # TODO: в таких диалогах чекать возвращаемое имя -- он позволяет вернуть любую строку
            name, done = QInputDialog.getItem(
                self,
                f"Фактор {factor.name}",
                "Выберите значение фактора для примера:",
                val_list,
            )
            if done:
                if name == "":
                    # выбрали "неважно" (*)
                    if cur_ex.get_value(factor) is not None:
                        cur_ex.remove_value(factor)
                else:
                    # выбрали значение фактора
                    cur_ex.add_value(factor.get_value(name))
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
                cur_ex.weight = weight
            else:
                pass
        # =========================================================
        else:
            # изменить значение результата примера
            res_contr = ResultController.get(self._data)
            name, done = QInputDialog.getItem(
                self,
                f"Результат",
                "Выберите значение результата для примера:",
                [res_val.name for res_val in res_contr.get_values()],
            )
            if done:
                cur_ex.result_value = res_contr.get_value(name)
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
        QMessageBox.information(self, "Переместить", "В разработке")

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
            for ind in correct_ind_list:
                ExampleController.remove_by_position(self._data, ind.row())
        else:
            return
        self._update_models()

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
        self.change_name_button.clicked.connect(self.on_change_name)
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

        self._update_definitions_buttons()
        self._update_examples_buttons()

        self.status_label.setText("База знаний не задана")

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
        self._update_definitions_buttons()
        self._update_examples_buttons()

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
        # таблица факторов
        self.definition_table.setModel(None)
        model = FactorsModel(self._data)
        self.definition_table.setModel(model)
        self.definition_table.selectionModel().currentChanged.connect(
            self.on_def_select
        )
        self._update_definitions_buttons()

        # таблица примеров
        self.example_table.setModel(None)
        model = ExamplesModel(self._data)  # type: ignore
        self.example_table.setModel(model)
        self.example_table.selectionModel().currentChanged.connect(self.on_ex_select)
        self._update_examples_buttons()

        # TODO: отображение дерева тоже здесь

    # обновить состояние кнопок Определений в зависимости от состояния текущей базы
    def _update_definitions_buttons(self):
        if self._data is None:
            for btn in self.__all_def_buttons():
                btn.setEnabled(False)
        else:
            for btn in self.__all_def_buttons([i for i in range(3, 8)]):
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
        if 4 not in exclude_list:
            lst.append(self.change_name_button)
        if 5 not in exclude_list:
            lst.append(self.activate_factor_button)
        if 6 not in exclude_list:
            lst.append(self.move_factor_button)
        if 7 not in exclude_list:
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

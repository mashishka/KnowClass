import logging as log

from PyQt5.QtCore import (
    QAbstractTableModel,
    Qt,
    QVariant,
    QModelIndex,
    pyqtSignal,
)
from PyQt5.QtWidgets import *

from data_utils.controllers.ExampleController import ExampleController
from data_utils.controllers.FactorController import FactorController
from data_utils.controllers.ResultController import ResultController
from data_utils.controllers.ValueController import ValueController
from data_utils.core import DataBase


# NOTE: простая модель для факторов (определений), может работать медленно
# TODO: попробовать сделать кэширование (мб обновлять кэш по таймеру)
# TODO: загружать названия столбцов один раз и использовать их
class FactorsModel(QAbstractTableModel):
    sig_add_factor = pyqtSignal()
    sig_delete_factor = pyqtSignal(int)
    sig_before_delete_result = pyqtSignal()
    sig_after_delete_result = pyqtSignal()

    def __init__(self, db: DataBase, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._db = db

    def rowCount(self, parent=None):
        res_val_cnt = self._res_controller().get_values_count()

        if FactorController.get_count(self._db) == 0:
            # обработка пустой базы
            if res_val_cnt == 0:
                return 0
            else:
                return res_val_cnt
        else:
            # в базе что-то есть; длина всех столбцов разная
            return max(
                max(
                    fact.get_values_count()
                    for fact in FactorController.get_all(self._db)
                ),
                res_val_cnt,
            )

    def columnCount(self, parent=None):
        # factors count + result
        return self._factors_count() + 1

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            row = index.row()
            column = index.column()
            # отображение
            if role == Qt.DisplayRole:
                # отображение всех факторов и результата с учётом кол-ва элементов в столбце
                columns = self._factors_count()

                if column < columns:
                    factor = FactorController.get_by_position(self._db, column)
                    if row < factor.get_values_count():
                        value = factor.get_value_by_position(row)
                        return QVariant(str("*" if value is None else value.name))
                    else:
                        return QVariant()
                if column == columns:
                    rc = self._res_controller()
                    if row < rc.get_values_count():
                        return QVariant(rc.get_value_by_position(row).name)
                    else:
                        return QVariant()
            # выравнивание
            if role == Qt.TextAlignmentRole:
                return Qt.AlignVCenter + Qt.AlignHCenter
        return QVariant()

    def headerData(self, col, orientation, role):
        # названия столбцов
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            columns = self._factors_count()
            if col < columns:
                factor = FactorController.get_by_position(self._db, col)
                return QVariant(factor.name)
            if col == columns:
                return QVariant(self._res_controller().name)
        return None

    # def flags(self, index: QModelIndex):
    #     log.debug("\n\nogo flags\n\n")
    #     flags = self.flags(index)
    #     if index.isValid():
    #         return flags | Qt.ItemIsEditable
    #     else:
    #         return flags

    # def setData(self, index: QModelIndex, value: QVariant, role=Qt.EditRole):
    #     log.debug("\n\nogo\n\n")
    #     if index.isValid():
    #         if role == Qt.EditRole:

    #             self.dataChanged.emit(index, index, value)
    #             return True
    #     return False

    def _factors_count(self):
        return FactorController.get_count(self._db)

    def _res_controller(self) -> ResultController:
        return ResultController.get(self._db)

    # логика работы с бд
    # =========================================================================
    # =========================================================================

    # TODO: обернуть в try добавление (мб удаление),
    # чтобы отлавливать создание существующих значений

    # добавить фактор
    # name -- имя фактора, text -- текст фактора
    def add_factor(self, name: str, text: str):
        col = self._factors_count()

        self.beginInsertColumns(QModelIndex(), col, col)
        res = FactorController.make(self._db, name)
        res.text = text
        self.endInsertColumns()

        # сигнал таблице примеров, чтобы тоже вставила столбец
        self.sig_add_factor.emit()

    # добавить значение фактору с позицией col
    # name -- имя значения, text -- текст значения
    def add_factor_value(self, name: str, text: str, col: int):
        res = FactorController.get_by_position(self._db, col)
        res_count = res.get_values_count()
        r_cnt = self.rowCount()

        if res_count == r_cnt:
            self.beginInsertRows(QModelIndex(), res_count, res_count)
        v_res = res.make_value(name)
        v_res.text = text
        if res_count == r_cnt:
            self.endInsertRows()

    # добавить значение результату
    # name -- имя значения, text -- текст значения
    def add_result_value(self, name: str, text: str):
        res = self._res_controller()
        res_count = res.get_values_count()
        r_cnt = self.rowCount()

        if res_count == r_cnt:
            self.beginInsertRows(QModelIndex(), res_count, res_count)
        res.make_value(name)
        res.text = text
        if res_count == r_cnt:
            self.endInsertRows()

    # удалить столбцы целиком
    # lst -- список индексов столбцов (во всех номер строки == 0)
    def delete_columns(self, lst: list[QModelIndex]):
        # NOTE: иногда ругается на endRemoveColumns, но без ошибок
        start_row_count = self.rowCount()
        ln = len(lst)

        if lst[-1].column() == self._factors_count():
            # среди столбцов есть столбец результатов,
            # его отображение не убираем
            last_ind = lst[-1].column() - 1
            ln -= 1
            # сигнал для таблицы примеров -- обработка удаления результатов
            self.sig_before_delete_result.emit()
        else:
            # только факторы
            last_ind = lst[-1].column()
            # сигнал для таблицы примеров, чтобы убрала столбец фактора
            self.sig_delete_factor.emit(ln)

        self.beginRemoveColumns(QModelIndex(), lst[0].column(), last_ind)
        for ind in reversed(lst):
            self.__delete_by_column(ind.column())
        self.endRemoveColumns()

        if lst[-1].column() == self._factors_count():
            self.sig_after_delete_result.emit()

        end_row_count = self.rowCount()
        self.beginRemoveRows(QModelIndex(), end_row_count, start_row_count - 1)
        self.endRemoveRows()

    # удалить отдельные значения
    # lst -- список всех удаляемых ячеек
    def delete_values(self, lst: list[QModelIndex]):
        start_row_count = self.rowCount()

        # сигнал для таблицы примеров,
        # чтобы убирала строки без результатов (бд сама их удаляет);
        # даже если среди ячеек нет из RESULT, всё норм
        self.sig_before_delete_result.emit()
        for ind in reversed(lst):
            self.__delete_by_index(ind)
        self.sig_after_delete_result.emit()

        end_row_count = self.rowCount()

        self.beginRemoveRows(QModelIndex(), end_row_count, start_row_count - 1)
        self.endRemoveRows()

    # удалить значения по индексам
    def __delete_by_index(self, index: QModelIndex):
        if index.column() < self._factors_count():
            # удалить значение фактора
            factor = FactorController.get_by_position(self._db, index.column())
            if index.row() < factor.get_values_count():
                factor.remove_value_by_position(index.row())
        else:
            # удалить значение результата
            res_contr = self._res_controller()
            if index.row() < res_contr.get_values_count():
                res_contr.remove_value_by_position(index.row())

    # удалить столбцы по номеру
    def __delete_by_column(self, col: int):
        if col < self._factors_count():
            # удалить весь фактор
            FactorController.remove_by_position(self._db, col)
        else:
            # удалить все результаты
            res_contr = self._res_controller()
            res_contr.remove_values()

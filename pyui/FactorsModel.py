import logging as log

from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QModelIndex
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
    def __init__(self, db: DataBase, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._db = db

    def rowCount(self, parent=None):
        res_val_cnt: int = ResultController.get(  # type: ignore
            self._db
        ).get_values_count()

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
                    rc = ResultController.get(self._db)
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
                return QVariant(ResultController.get(self._db).name)
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

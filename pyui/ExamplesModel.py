import logging as log

from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant
from PyQt5.QtWidgets import *

from data_utils.controllers.ExampleController import ExampleController
from data_utils.controllers.FactorController import FactorController
from data_utils.controllers.ResultController import ResultController
from data_utils.core import DataBase


# NOTE: простая модель для примеров, может работать медленно
class ExamplesModel(QAbstractTableModel):
    def __init__(self, db: DataBase, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._db = db

    def rowCount(self, parent=None):
        # examples count
        return ExampleController.get_count(self._db)

    def columnCount(self, parent=None):
        # factors count + result + weight
        return self._factors_count() + 2

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            row = index.row()
            column = index.column()
            if role == Qt.DisplayRole:
                columns = self._factors_count()

                example = ExampleController.get_by_position(self._db, row)
                if column < columns:
                    factor = FactorController.get_by_position(self._db, column)
                    value = example.get_value(factor)
                    return QVariant(str("*" if value is None else value.name))
                if column == columns + 1:
                    return QVariant(str(example.result_value.name))
                return QVariant(str(example.weight))
        return QVariant()

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            columns = self._factors_count()
            if col < columns:
                factor = FactorController.get_by_position(self._db, col)
                return QVariant(str(factor.name))
            if col == columns + 1:
                return QVariant(ResultController.get(self._db).name)
            return QVariant("Weight")
        return None

    def _factors_count(self):
        return FactorController.get_count(self._db)

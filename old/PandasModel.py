# import logging as log

# from pandas import DataFrame
# from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant
# from PyQt5.QtWidgets import *


# class PandasModel(QAbstractTableModel):
#     def __init__(self, data: DataFrame, parent=None):
#         QAbstractTableModel.__init__(self, parent)
#         self._data = data

#     def rowCount(self, parent=None):
#         return len(self._data.values)

#     def columnCount(self, parent=None):
#         return self._data.columns.size

#     def data(self, index, role=Qt.DisplayRole):
#         if index.isValid():
#             if role == Qt.DisplayRole:
#                 return QVariant(str(
#                     self._data.iloc[index.row()][index.column()]))
#         return QVariant()

#     def headerData(self, col, orientation, role):
#         if orientation == Qt.Horizontal and role == Qt.DisplayRole:
#             return self._data.columns[col]
#         return None

import logging as log

from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, pyqtSlot, QModelIndex
from PyQt5.QtWidgets import *

from data_utils.controllers.ExampleController import ExampleController
from data_utils.controllers.FactorController import FactorController
from data_utils.controllers.ResultController import ResultController
from data_utils.core import DataBase

# kek_counter: int = 0


# NOTE: простая модель для примеров, может работать медленно
# TODO: попробовать сделать кэширование (мб обновлять кэш по таймеру)
# TODO: загружать названия столбцов один раз и использовать их
class ExamplesModel(QAbstractTableModel):
    # промежуточная переменная на случай удаления столбца результатов (например)
    __start_row_count: int = 0

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
            # отображение
            if role == Qt.DisplayRole:
                columns = self._factors_count()

                example = ExampleController.get_by_position(self._db, row)
                if column < columns:
                    factor = FactorController.get_by_position(self._db, column)
                    value = example.get_value(factor)
                    return QVariant("*" if value is None else value.name)
                if column == columns + 1:
                    return QVariant(example.result_value.name)
                return QVariant(str(example.weight))
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
            if col == columns + 1:
                return QVariant(self._res_controller().name)
            return QVariant("Weight")
        # названия строк
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return QVariant(str(col + 1) + ":")
        return None

    def _factors_count(self):
        return FactorController.get_count(self._db)

    def _res_controller(self) -> ResultController:
        return ResultController.get(self._db)

    # логика работы с бд
    # =========================================================================
    # =========================================================================

    # сигналы для реагирования на таблицу Определений

    # добавлен фактор -> нужно добавить столбец
    @pyqtSlot()
    def on_add_factor(self):
        col = self._factors_count()

        self.beginInsertColumns(QModelIndex(), col, col)
        self.endInsertColumns()

    # удалены count факторов -> убрать столбцы
    @pyqtSlot(int)
    def on_delete_factor(self, count: int):
        col = self._factors_count()

        self.beginRemoveColumns(QModelIndex(), col - count, col - 1)
        self.endRemoveColumns()

    # оболочка для изменения кол-ва строк; всегда даёт актуальный результат
    # должны использоваться в паре
    @pyqtSlot()
    def on_before_delete(self):
        self.__start_row_count = self.rowCount()

    @pyqtSlot()
    def on_after_delete(self):
        end_row_count = self.rowCount()

        self.beginRemoveRows(QModelIndex(), end_row_count, self.__start_row_count - 1)
        self.endRemoveRows()

    # =========================================================================

    # получить список значений результатов (их имена)
    def get_list_res_val(self):
        res_contr = self._res_controller()
        return [res_val.name for res_val in res_contr.get_values()]

    # получить список значений фактора с позицией col
    # возвращает имя фактора и список его значений (их имена)
    def get_list_fact_val(self, col: int):
        factor = FactorController.get_by_position(self._db, col)
        val_list: list[str] = []  # type: ignore
        val_list.append("")
        val_list += [res_val.name for res_val in factor.get_values()]
        return factor.name, val_list

    # добавить пример, name -- имя результата, вес по умолчанию == 1.0
    def add_example(self, name: str):
        res_contr = self._res_controller()
        row_cnt = self.rowCount()

        self.beginInsertRows(QModelIndex(), row_cnt, row_cnt)
        ExampleController.make(self._db, 1.0, res_contr.get_value(name))
        self.endInsertRows()

    # удалить примеры, lst -- список индексов
    # строка удаляется, если был выделен хотя бы один её элемент
    def delete_examples(self, lst: list[QModelIndex]):
        self.on_before_delete()
        for ind in lst:
            ExampleController.remove_by_position(self._db, ind.row())
        self.on_after_delete()

    # изменить значение фактора примера
    # ex_position -- позиция примера,
    # fact_name -- имя фактора
    # val_name -- имя значения
    def change_factor_val(self, ex_position: int, fact_name: str, val_name: str):
        cur_ex = ExampleController.get_by_position(self._db, ex_position)
        factor = FactorController.get(self._db, fact_name)
        if val_name == "":
            # выбрали "неважно" (*)
            if cur_ex.get_value(factor) is not None:
                cur_ex.remove_value(factor)
        else:
            # выбрали значение фактора
            cur_ex.add_value(factor.get_value(val_name))

    # изменить вес примера
    # ex_position -- позиция примера,
    # val -- вес
    def change_ex_weight(self, ex_position: int, val: float):
        cur_ex = ExampleController.get_by_position(self._db, ex_position)
        cur_ex.weight = val

    # изменить результат примера
    # ex_position -- позиция примера,
    # val_name -- имя значения результата
    def change_ex_result(self, ex_position: int, val_name: str):
        cur_ex = ExampleController.get_by_position(self._db, ex_position)
        cur_ex.result_value = self._res_controller().get_value(val_name)

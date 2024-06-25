import logging as log

from PyQt5.QtCore import (
    QAbstractTableModel,
    Qt,
    QVariant,
    pyqtSlot,
    QModelIndex,
    pyqtSignal,
)
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor

from data_utils.controllers.ExampleController import ExampleController
from data_utils.controllers.FactorController import FactorController
from data_utils.controllers.ResultController import ResultController
from data_utils.core import DataBase
from ui.pyui.SimpleGroupCache import SimpleGroupCache, cached

# kek_counter: int = 0


class ExamplesModel(QAbstractTableModel):
    # промежуточная переменная на случай удаления столбца результатов (например)
    __start_row_count: int = 0

    sig_invalidate = pyqtSignal()

    # стандартный цвет
    default_color: QColor = QColor(255, 255, 255)
    # цвет помеченного примера
    ex_color: QColor = QColor(155, 155, 255)
    # список позиций для разметки примеров
    color_list: list[int] = []

    def __init__(self, db: DataBase, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._db = db
        self._cache = SimpleGroupCache()

        # кеширование данных для интерфейса
        self._display_data = cached(self._cache, "_display_data")(self._display_data)
        self._display_horisontal_header = cached(
            self._cache, "_display_horisontal_header"
        )(self._display_horisontal_header)
        self.rowCount = cached(self._cache, "rowCount")(self.rowCount)
        self.columnCount = cached(self._cache, "columnCount")(self.columnCount)

        # инвалидация кеша при изменении
        invalidate_signals = [
            self.dataChanged,
            self.headerDataChanged,
            self.sig_invalidate,
            # self.sig_add_factor,
            # self.sig_delete_factor,
            # self.sig_delete_factor,
            # self.sig_after_delete_result,
        ]

        def invalidate(*args, **kwargs):
            self.color_list = []
            self._cache.invalidate_all()

        for signal in invalidate_signals:
            signal.connect(invalidate)

    def rowCount(self, parent=None):
        # examples count
        return ExampleController.get_count(self._db)

    def columnCount(self, parent=None):
        # factors count + result + weight
        return self._factors_count() + 2

    def _display_data(self, cached_index: tuple[int, int]) -> QVariant:
        row, column = cached_index

        columns = self._factors_count()
        example = ExampleController.get_by_position(self._db, row)
        if column < columns:
            factor = FactorController.get_by_position(self._db, column)
            value = example.get_value(factor)
            return QVariant("*" if value is None else value.name)
        if column == columns + 1:
            return QVariant(example.result_value.name)
        return QVariant(str(example.weight))

    def _display_horisontal_header(self, cached_index: int):
        col = cached_index

        columns = self._factors_count()
        if col < columns:
            factor = FactorController.get_by_position(self._db, col)
            return QVariant(factor.name)
        if col == columns + 1:
            return QVariant(self._res_controller().name)
        return QVariant("Weight")

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            row, column = index.row(), index.column()
            # отображение
            if role == Qt.DisplayRole:
                return self._display_data(cached_index=(row, column))
            # выравнивание
            if role == Qt.TextAlignmentRole:
                return Qt.AlignVCenter + Qt.AlignHCenter
            if role == Qt.BackgroundRole:
                if index.row() in self.color_list:
                    return self.ex_color
                # return self.default_color
                return QVariant()
        return QVariant()

    def headerData(self, col, orientation, role):
        # названия столбцов
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._display_horisontal_header(cached_index=col)
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
    # возвращает экземпляр созданного примера
    def add_example(self, name: str) -> ExampleController:
        res_contr = self._res_controller()
        row_cnt = self.rowCount()

        self.beginInsertRows(QModelIndex(), row_cnt, row_cnt)
        ex = ExampleController.make(self._db, 1.0, res_contr.get_value(name))
        self.endInsertRows()

        self.sig_invalidate.emit()

        return ex

    # удалить примеры, lst -- список индексов
    # строка удаляется, если был выделен хотя бы один её элемент
    def delete_examples(self, lst: list[QModelIndex]):
        self.on_before_delete()
        for ind in lst:
            ExampleController.remove_by_position(self._db, ind.row())
        self.sig_invalidate.emit()
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

        self.sig_invalidate.emit()

    # изменить вес примера
    # ex_position -- позиция примера,
    # val -- вес
    def change_ex_weight(self, ex_position: int, val: float):
        cur_ex = ExampleController.get_by_position(self._db, ex_position)
        cur_ex.weight = val
        self.sig_invalidate.emit()

    # изменить результат примера
    # ex_position -- позиция примера,
    # val_name -- имя значения результата
    def change_ex_result(self, ex_position: int, val_name: str):
        cur_ex = ExampleController.get_by_position(self._db, ex_position)
        cur_ex.result_value = self._res_controller().get_value(val_name)
        self.sig_invalidate.emit()

    # переместить пример prev_pos в позицию dest_pos
    # позиции начинаются с 0, в интерфейсе с единицы
    def move_example_to(self, prev_pos: int, dest_pos: int) -> bool:
        ex = ExampleController.get_by_position(self._db, prev_pos)
        if 0 <= dest_pos < ExampleController.get_count(self._db):
            ex.position = dest_pos
            self.sig_invalidate.emit()
            return True
        return False

    # дублировать пример с позицией pos (настоящая позиция, начинается с 0)
    def clone_ex(self, pos: int):
        ex = ExampleController.get_by_position(self._db, pos)
        new_ex = self.add_example(ex.result_value.name)

        for val in ex.get_values():
            new_ex.add_value(val)

        new_ex.weight = ex.weight

        self.move_example_to(new_ex.position, pos + 1)
        self.sig_invalidate.emit()

    # пометить примеры цветом;
    # lst -- список id примеров (например, из функции completeness), которые нужно раскрасить
    def mark_examples(self, lst: list[int]):
        self.color_list = [
            ExampleController.get(self._db, ex_id).position for ex_id in lst
        ]

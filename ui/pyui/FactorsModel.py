from PyQt5.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    QVariant,
    pyqtSignal,
)
from PyQt5.QtWidgets import *

from data_utils.controllers.ExampleController import ExampleController
from data_utils.controllers.FactorController import FactorController
from data_utils.controllers.ResultController import ResultController
from data_utils.controllers.ValueController import ValueController
from data_utils.core import DataBase
from ui.pyui.SimpleGroupCache import SimpleGroupCache, cached


class FactorsModel(QAbstractTableModel):
    sig_add_factor = pyqtSignal()
    sig_delete_factor = pyqtSignal(int)
    sig_before_delete_result = pyqtSignal()
    sig_after_delete_result = pyqtSignal()

    sig_local_invalidate = pyqtSignal()
    sig_invalidate = pyqtSignal()

    def __init__(self, db: DataBase, parent=None):
        QAbstractTableModel.__init__(self, parent)

        self._db = db
        self._cache = SimpleGroupCache()

        # кеширование данных для интерфейса
        self._display_data = cached(self._cache, "_display_data")(self._display_data)
        self._display_header = cached(self._cache, "_display_header")(
            self._display_header
        )
        self.rowCount = cached(self._cache, "rowCount")(self.rowCount)
        self.columnCount = cached(self._cache, "columnCount")(self.columnCount)

        # инвалидация кеша при изменении
        # TODO: не только эти? (например, добавление значения, всякие изменения)
        invalidate_signals = [
            self.dataChanged,
            self.headerDataChanged,
            self.sig_add_factor,
            self.sig_delete_factor,
            self.sig_after_delete_result,
            self.sig_local_invalidate,
        ]

        def invalidate(*args, **kwargs):
            self._cache.invalidate_all()

        for signal in invalidate_signals:
            signal.connect(invalidate)
            signal.connect(self.sig_invalidate)

    def rowCount(self, parent=None):
        res_val_cnt = ResultController.get(self._db).get_values_count()

        if FactorController.get_count(self._db) == 0:
            # обработка пустой базы
            return res_val_cnt

        # в базе что-то есть; длина всех столбцов разная
        return max(FactorController.get_max_value_count(self._db), res_val_cnt)

    def columnCount(self, parent=None):
        return self._factors_count() + 1

    def _display_data(self, cached_index: tuple[int, int]) -> QVariant:
        row, column = cached_index
        # отображение всех факторов и результата с учётом кол-ва элементов в столбце

        columns = self._factors_count()

        if column < columns:
            factor = FactorController.get_by_position(self._db, column)
            if row < factor.get_values_count():
                value = factor.get_value_by_position(row)
                return QVariant("*" if value is None else value.name)
        elif column == columns:
            rc = ResultController.get(self._db)
            if row < self._result_values_count(rc):
                return QVariant(rc.get_value_by_position(row).name)
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            return self._display_data(cached_index=(index.row(), index.column()))

        # выравнивание
        if role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter + Qt.AlignHCenter
        return QVariant()

    def _display_header(self, cached_index: int):
        col = cached_index
        columns = self._factors_count()
        if col < columns:
            factor = FactorController.get_by_position(self._db, col)
            return QVariant(factor.name)
        if col == columns:
            return QVariant(ResultController.get(self._db).name)

    def headerData(self, col, orientation, role):
        # названия столбцов
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._display_header(cached_index=col)
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

    def _factors_count(self) -> int:
        return FactorController.get_count(self._db)

    def _result_values_count(self, result: ResultController) -> int:
        return result.get_values_count()

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
        self.sig_local_invalidate.emit()

    # добавить значение результату
    # name -- имя значения, text -- текст значения
    def add_result_value(self, name: str, text: str):
        res = ResultController.get(self._db)
        res_count = res.get_values_count()
        r_cnt = self.rowCount()

        if res_count == r_cnt:
            self.beginInsertRows(QModelIndex(), res_count, res_count)
        val = res.make_value(name)
        val.text = text
        if res_count == r_cnt:
            self.endInsertRows()
        self.sig_local_invalidate.emit()

    # удалить столбцы целиком
    # lst -- список индексов столбцов (во всех номер строки == 0)
    def delete_columns(self, lst: list[QModelIndex]):
        # NOTE: иногда ругается на endRemoveColumns, но без ошибок
        start_row_count = self.rowCount()
        start_col_count = self.columnCount()
        ln = len(lst)
        fact_count = self._factors_count()

        # флаг, есть ли среди удаляемых столбцов RESULT
        has_result_col: bool = fact_count in [ind.column() for ind in lst]

        if has_result_col:
            # среди столбцов есть столбец результатов,
            # его отображение не убираем
            ln -= 1
            # сигнал для таблицы примеров -- обработка удаления результатов
            self.sig_before_delete_result.emit()

        for ind in lst:
            self.__delete_by_column(ind.column())

        if has_result_col:
            self.sig_after_delete_result.emit()

        # сигнал для таблицы примеров, чтобы убрала ln столбцов факторов
        self.sig_delete_factor.emit(ln)

        self.sig_local_invalidate.emit()
        end_row_count = self.rowCount()
        end_col_count = self.columnCount()

        self.beginRemoveRows(QModelIndex(), end_row_count, start_row_count - 1)
        self.endRemoveRows()

        self.beginRemoveColumns(QModelIndex(), end_col_count, start_col_count - 1)
        self.endRemoveColumns()

    # удалить отдельные значения
    # lst -- список всех удаляемых ячеек
    def delete_values(self, lst: list[QModelIndex]):
        start_row_count = self.rowCount()

        # сигнал для таблицы примеров,
        # чтобы убирала строки без результатов (бд сама их удаляет);
        # даже если среди ячеек нет из RESULT, всё норм
        self.sig_before_delete_result.emit()
        for ind in lst:
            self.__delete_by_index(ind)
        self.sig_after_delete_result.emit()

        self.sig_local_invalidate.emit()
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
            res = ResultController.get(self._db)
            if index.row() < res.get_values_count():
                res.remove_value_by_position(index.row())

    # удалить столбцы по номеру
    def __delete_by_column(self, col: int):
        if col < self._factors_count():
            # удалить весь фактор
            FactorController.remove_by_position(self._db, col)
        else:
            # удалить все результаты
            res = ResultController.get(self._db)
            res.remove_values()

    # получить имя и текст фактора с позицией col
    def get_fact_info(self, col: int) -> tuple[str, str]:
        fact = FactorController.get_by_position(self._db, col)
        return fact.name, fact.text

    # получить имя и текст значения с позицией row-col
    def get_fact_val_info(self, row: int, col: int) -> tuple[str, str]:
        fact = FactorController.get_by_position(self._db, col)
        if row < fact.get_values_count():
            val = fact.get_value_by_position(row)
            return val.name, val.text
        return "", ""

    # получить текст RESULT
    def get_result_text(self) -> str:
        res = ResultController.get(self._db)
        return res.text

    # получить имя и текст значения результата
    def get_result_val_info(self, row: int) -> tuple[str, str]:
        res = ResultController.get(self._db)
        if row < res.get_values_count():
            val = res.get_value_by_position(row)
            return val.name, val.text
        return "", ""

    # возвращают признак успеха установки (корректность индекса)
    # установить текст фактора с позицией col
    def set_fact_text(self, col: int, txt: str) -> bool:
        fact = FactorController.get_by_position(self._db, col)
        fact.text = txt
        self.sig_local_invalidate.emit()
        return True

    # установить текст значения с позицией row-col
    def set_fact_val_text(self, row: int, col: int, txt: str) -> bool:
        fact = FactorController.get_by_position(self._db, col)
        if row < fact.get_values_count():
            fact.get_value_by_position(row).text = txt
            self.sig_local_invalidate.emit()
            return True
        return False

    # установить текст RESULT
    def set_result_text(self, txt: str) -> bool:
        res = ResultController.get(self._db)
        res.text = txt
        self.sig_local_invalidate.emit()
        return True

    # установить текст значения результата
    def set_result_val_text(self, row: int, txt: str) -> bool:
        res = ResultController.get(self._db)
        if row < res.get_values_count():
            res.get_value_by_position(row).text = txt
            self.sig_local_invalidate.emit()
            return True
        return False

    # проверка на корректность индекса модели -- индекс показывает на значение
    def _check_model_index(self, ind: QModelIndex) -> bool:
        if ind.isValid():
            fct_cnt = self._factors_count()
            if ind.column() < fct_cnt:
                fact = FactorController.get_by_position(self._db, ind.column())
                if ind.row() < fact.get_values_count():
                    return True
                return False
            elif ind.column() == fct_cnt:
                res = ResultController.get(self._db)
                if ind.row() < res.get_values_count():
                    return True
                return False  # мб можно лесенку поменьше, но пока ладно
            return False
        return False

    # возвращают признак успеха перемещения (корректность индекса)
    # переместить фактор с позицией prev_pos на позицию dest_pos (остальные сдвигаются)
    def move_factor_to(self, prev_pos: int, dest_pos: int) -> bool:
        fact = FactorController.get_by_position(self._db, prev_pos)
        if 0 <= dest_pos < self._factors_count():
            fact.position = dest_pos
            self.sig_local_invalidate.emit()
            return True
        return False

    # переместить значение с позицией prev_row из фактора с позицией col
    # на позицию dest_pos (остальные сдвигаются)
    def move_value_to(self, prev_row: int, col: int, dest_row: int) -> bool:
        fact_cnt = self._factors_count()
        if col < fact_cnt:
            fact = FactorController.get_by_position(self._db, col)
            val = fact.get_value_by_position(prev_row)
            if 0 <= dest_row < fact.get_values_count():
                val.position = dest_row
                self.sig_local_invalidate.emit()
                return True
            return False
        else:
            res = ResultController.get(self._db)
            val = res.get_value_by_position(prev_row)
            if 0 <= dest_row < res.get_values_count():
                val.position = dest_row
                self.sig_local_invalidate.emit()
                return True
            return False

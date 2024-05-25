from __future__ import annotations

from typing import Union

from sqlalchemy.orm import Session

from data_utils.core import DataBase
from data_utils.imp.position import TablePosition
from data_utils.imp.rerased import reraised_class
from data_utils.imp.tables import Value


# класс для работы со свойствами значений фактора
# у значения фактора уникальные (в рамках одного фактора) - имя  и позиция
@reraised_class()
class ValueController:
    # количество всех значений
    @staticmethod
    def get_count(db: DataBase) -> int:
        with db.session as session:
            return DataBase.get_count(session, Value)

    # получение всех значений по всем факторам
    @staticmethod
    def get_all(db: DataBase) -> list[ValueController]:
        with db.session as session:
            all = DataBase.get_all_field(session, Value.value_id)
        # NOTE: эффективнее полный запрос?
        return [ValueController(db, id) for id in all]

    # удаление всех значений по всем факторам
    @staticmethod
    def remove_all(db: DataBase) -> None:
        with db.session as session:
            DataBase.delete_all(session, Value)
            session.commit()

    # оператор сравнения
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ValueController):
            return False
        return self._id == other._id

    # получени фактора по значению
    @property
    def factor(self):
        # cyclic dep
        from data_utils.controllers.FactorController import FactorController

        with self._db.session as session:
            factor_id = DataBase.get_field_by_id(session, Value, self._id, Value.factor_id)
        return FactorController.get(self._db, factor_id)

    # атрибут имени (нельзя изменить)
    @property
    def name(self) -> str:
        with self._db.session as session:
            return DataBase.get_field_by_id(session, Value, self._id, Value.name)

    # атрибут теста
    @property
    def text(self) -> str:
        with self._db.session as session:
            return DataBase.get_field_by_id(session, Value, self._id, Value.text_)

    @text.setter
    def text(self, value: str) -> None:
        with self._db.session as session:
            factor = self.get_db_table(session)
            factor.text_ = value
            session.commit()

    # атрибут позиции
    @property
    def position(self) -> int:
        with self._db.session as session:
            return TablePosition.get_position(session, self.get_db_table(session))

    # изменение позиции путём вставки
    @position.setter
    def position(self, value: int) -> None:
        with self._db.session as session:
            TablePosition.change_insert(session, self.get_db_table(session), value)
            session.commit()

    # изменение позиции путём перестановки
    def swap_position(self, other: ValueController) -> None:
        with self._db.session as session:
            TablePosition.change_swap(
                session, self.get_db_table(session), other.get_db_table(session)
            )
            session.commit()

    def __init__(self, db: DataBase, names_or_id: Union[tuple[str, str], int]) -> None:
        """Не использовать напрямую"""

        self._db = db
        if isinstance(names_or_id, int):
            self._id = names_or_id
        else:
            with self._db.session as session:
                self._id = DataBase.get_value_by_names(session, *names_or_id).value_id

    def get_db_table(self, session: Session) -> Value:
        return DataBase.get_table_by_id(session, Value, self._id)

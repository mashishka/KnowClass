from __future__ import annotations

from sqlalchemy.orm import Session

from data_utils.core import DataBase
from data_utils.imp.position import TablePosition
from data_utils.imp.rerased import reraised_class
from data_utils.imp.tables import Value


# класс для работы со свойствами значений фактора
# у значения фактора уникальные (в рамках одного фактора) - имя  и позиция
@reraised_class()
class ValueController:
    # получение всех значений по всем факторам
    @staticmethod
    def get_all(db: DataBase) -> list[ValueController]:
        with db.session as session:
            all = DataBase.get_all(session, Value)
        return [
            ValueController(db, DataBase.get_factor_by_id(session, val.factor_id).name, val.name)
            for val in all
        ]

    # удаление всех значений по всем факторам
    @staticmethod
    def remove_all(db: DataBase) -> None:
        with db.session as session:
            all = DataBase.get_all(session, Value)
            for value in all:
                session.delete(value)
            session.commit()

    # оператор сравнения
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ValueController):
            return False
        return self._name == other._name

    # получени фактора по значению
    @property
    def factor(self):
        # cyclic dep
        from data_utils.controllers.FactorController import FactorController

        return FactorController.get(self._db, self._factor_name)

    # атрибут имени (нельзя изменить)
    @property
    def name(self) -> str:
        return self._name

    # атрибут теста
    @property
    def text(self) -> str:
        with self._db.session as session:
            return self.get_db_table(session).text_

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

    def __init__(self, db: DataBase, factor_name: str, name: str) -> None:
        """Не использовать напрямую"""

        self._db = db
        self._factor_name = factor_name
        self._name = name

        # check existance
        with self._db.session as session:
            self.get_db_table(session)

    def get_db_table(self, session: Session) -> Value:
        return DataBase.get_value_by_names(session, self._factor_name, self.name)

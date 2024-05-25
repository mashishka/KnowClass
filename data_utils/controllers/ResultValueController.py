from __future__ import annotations

from typing import Union

from sqlalchemy.orm import Session

from data_utils.core import DataBase
from data_utils.imp.position import TablePosition
from data_utils.imp.rerased import reraised_class
from data_utils.imp.tables import ResultValue


# класс для работы со свойствами значений результата
# у значения результата уникальные - имя и позиция
@reraised_class()
class ResultValueController:
    # оператор сравнения
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ResultValueController):
            return False
        return self._id == other._id

    # атрибут имени (нельзя изменять)
    @property
    def name(self) -> str:
        with self._db.session as session:
            return DataBase.get_field_by_id(session, ResultValue, self._id, ResultValue.name)

    # атрибут теста
    @property
    def text(self) -> str:
        with self._db.session as session:
            return DataBase.get_field_by_id(session, ResultValue, self._id, ResultValue.text_)

    @text.setter
    def text(self, value: str) -> None:
        with self._db.session as session:
            result_value = self.get_db_table(session)
            result_value.text_ = value
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
    def swap_position(self, other: ResultValueController) -> None:
        with self._db.session as session:
            TablePosition.change_swap(
                session, self.get_db_table(session), other.get_db_table(session)
            )
            session.commit()

    def __init__(self, db: DataBase, name_or_id: Union[str, int]) -> None:
        """Не использовать напрямую"""

        self._db = db
        if isinstance(name_or_id, int):
            self._id = name_or_id
        else:
            with self._db.session as session:
                self._id = DataBase.get_result_value_by_name(session, name_or_id).result_value_id

    def get_db_table(self, session: Session) -> ResultValue:
        return DataBase.get_table_by_id(session, ResultValue, self._id)

from __future__ import annotations

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
        return self._name == other._name

    # атрибут имени (нельзя изменять)
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

    # атрибут коэффициента правдоподобия
    # NOTE: None == не указан
    @property
    def likelihood(self) -> float | None:
        with self._db.session as session:
            return self.get_db_table(session).likelihood

    # NOTE: None == не указан
    @likelihood.setter
    def likelihood(self, value: float | None) -> None:
        with self._db.session as session:
            factor = self.get_db_table(session)
            factor.likelihood = value
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

    def __init__(self, db: DataBase, name: str) -> None:
        """Не использовать напрямую"""

        self._db = db
        self._name = name

        # check existance
        with self._db.session as session:
            self.get_db_table(session)

    def get_db_table(self, session: Session) -> ResultValue:
        return DataBase.get_result_value_by_name(session, self.name)

from __future__ import annotations

from sqlalchemy.orm import Session

from data_utils.controllers.ResultValueController import ResultValueController
from data_utils.core import DataBase
from data_utils.imp.position import TablePosition
from data_utils.imp.rerased import reraised_class
from data_utils.imp.tables import AdditionalData, ResultValue
from data_utils.ResultMethodType import ResultMethodType


# класс для работы с результатом и его значениями
# результат уникален сам по себе (один столбец) и всегда существует
# он имеет фиксированное имя RESULT
@reraised_class()
class ResultController:
    # получение результата
    @staticmethod
    def get(db: DataBase) -> ResultController:
        return ResultController(db)

    # атрибут имени (нельзя изменять)
    @property
    def name(self) -> str:
        with self._db.session as session:
            return self.get_db_table(session).result_name

    # атрибут теста
    @property
    def text(self) -> str:
        with self._db.session as session:
            return self.get_db_table(session).result_text

    @text.setter
    def text(self, value: str) -> None:
        with self._db.session as session:
            data = self.get_db_table(session)
            data.result_text = value
            session.commit()

    # атрибут метода обработки результата
    # NOTE: None == не задан
    @property
    def type(self) -> ResultMethodType | None:
        with self._db.session as session:
            value = self.get_db_table(session).result_type
            if value is None:
                return None
            return ResultMethodType(value)

    # NOTE: None == не задан
    @type.setter
    def type(self, value: ResultMethodType | None) -> None:
        with self._db.session as session:
            data = self.get_db_table(session)
            data.result_type = value.value if value else None
            session.commit()

    # создание значения результата по уникальному имени
    def make_value(self, name: str) -> ResultValueController:
        with self._db.session as session:
            value = ResultValue(name=name)
            session.add(value)
            session.commit()
        return ResultValueController(self._db, name)

    # получение значения результата по уникальному имени
    def get_value(self, name: str) -> ResultValueController:
        return ResultValueController(self._db, name)

    # удаление значения результата по уникальному имени
    def remove_value(self, name: str) -> None:
        with self._db.session as session:
            value = DataBase.get_result_value_by_name(session, name)
            session.delete(value)
            session.commit()

    # получение значения результата по позиции
    def get_value_by_position(self, position: int) -> ResultValueController:
        with self._db.session as session:
            name = TablePosition.get_by_position(session, ResultValue, position).name
        return ResultValueController(self._db, name)

    # удаление значения результата по позиции
    # TODO: тест
    def remove_value_by_position(self, position: int) -> None:
        with self._db.session as session:
            value = TablePosition.get_by_position(session, ResultValue, position)
            session.delete(value)
            session.commit()

    # получение всех значений результата
    def get_values(self) -> list[ResultValueController]:
        with self._db.session as session:
            raw = DataBase.get_result_values(session)
        return [ResultValueController(self._db, val.name) for val in raw]

    # удаление всех значений результата
    def remove_values(self) -> None:
        with self._db.session as session:
            values = DataBase.get_result_values(session)
            for value in values:
                session.delete(value)
            session.commit()

    def __init__(self, db: DataBase) -> None:
        """Не использовать напрямую"""

        self._db = db

        # check existance
        with self._db.session as session:
            self.get_db_table(session)

    def get_db_table(self, session: Session) -> AdditionalData:
        return DataBase.get_addition_data(session)

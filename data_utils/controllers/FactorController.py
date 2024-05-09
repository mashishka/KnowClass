from __future__ import annotations

from sqlalchemy.orm import Session

from data_utils.controllers.ValueController import ValueController
from data_utils.core import DataBase
from data_utils.imp.position import TablePosition
from data_utils.imp.rerased import reraised_class
from data_utils.imp.tables import Factor, Value


# класс для работы с факторами и их значениями
# у фактора уникальные - имя и позиция
@reraised_class()
class FactorController:
    # создание из уникального имени
    @staticmethod
    def make(db: DataBase, name: str) -> FactorController:
        with db.session as session:
            factor = Factor(name=name)
            session.add(factor)
            session.commit()
        return FactorController(db, name)

    # получение по имени
    @staticmethod
    def get(db: DataBase, name: str) -> FactorController:
        return FactorController(db, name)

    # удаление по позиции
    @staticmethod
    def remove(db: DataBase, name: str) -> None:
        with db.session as session:
            factor = DataBase.get_factor_by_name(session, name)
            session.delete(factor)
            session.commit()

    # получение по позиции
    @staticmethod
    def get_by_position(db: DataBase, position: int) -> FactorController:
        with db.session as session:
            name = TablePosition.get_by_position(session, Factor, position).name
        return FactorController(db, name)

    # удаление по позиции
    @staticmethod
    def remove_by_position(db: DataBase, position: int) -> None:
        with db.session as session:
            factor = TablePosition.get_by_position(session, Factor, position)
            session.delete(factor)
            session.commit()

    # количество факторов
    @staticmethod
    def get_count(db: DataBase) -> int:
        with db.session as session:
            return DataBase.get_count(session, Factor)

    # получение всех факторов
    @staticmethod
    def get_all(db: DataBase) -> list[FactorController]:
        with db.session as session:
            all = DataBase.get_all(session, Factor)
        return [FactorController(db, val.name) for val in all]

    # удаление всех факторов
    @staticmethod
    def remove_all(db: DataBase) -> None:
        with db.session as session:
            all = DataBase.get_all(session, Factor)
            for factor in all:
                session.delete(factor)
            session.commit()

    # оператор сравнения
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FactorController):
            return False
        return self._name == other._name

    # атрибут имени (нельзя изменить)
    @property
    def name(self) -> str:
        return self._name

    # атрибут текста
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

    # атрибут активности фактора
    @property
    def active(self) -> bool:
        with self._db.session as session:
            return bool(self.get_db_table(session).active)

    @active.setter
    def active(self, value: bool) -> None:
        with self._db.session as session:
            example = self.get_db_table(session)
            example.active = value
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
    def swap_position(self, other: FactorController) -> None:
        with self._db.session as session:
            TablePosition.change_swap(
                session, self.get_db_table(session), other.get_db_table(session)
            )
            session.commit()

    # создание значения фактора по уникальному (в рамках одного фактора) имени
    def make_value(self, name: str) -> ValueController:
        with self._db.session as session:
            db_factor = self.get_db_table(session)
            value = Value(factor_id=db_factor.factor_id, name=name)
            session.add(value)
            session.commit()
        return ValueController(self._db, self.name, name)

    # получение значения фактора по имени
    def get_value(self, name: str) -> ValueController:
        return ValueController(self._db, self.name, name)

    # получение значения фактора по имени
    def remove_value(self, name: str) -> None:
        with self._db.session as session:
            value = DataBase.get_value_by_names(session, self.name, name)
            session.delete(value)
            session.commit()

    # получение значения фактора по позиции
    def get_value_by_position(self, position: int) -> ValueController:
        with self._db.session as session:
            name = TablePosition.get_Value_by_position(
                session, self.get_db_table(session), position
            ).name
        return ValueController(self._db, self.name, name)

    # получение значения фактора по позиции
    def remove_value_by_position(self, position: int) -> None:
        with self._db.session as session:
            factor = TablePosition.get_Value_by_position(
                session, self.get_db_table(session), position
            )
            session.delete(factor)
            session.commit()

    # количество значений фактора
    def get_values_count(self) -> int:
        with self._db.session as session:
            db_factor = self.get_db_table(session)
            return DataBase.get_count(session, Value, {"factor_id": db_factor.factor_id})

    # получение всех значений фактора
    def get_values(self) -> list[ValueController]:
        with self._db.session as session:
            raw = DataBase.get_values_by_factor_name(session, self.name)
        return [ValueController(self._db, self.name, val.name) for val in raw]

    # удаление всех значений фактора
    def remove_values(self) -> None:
        with self._db.session as session:
            values = DataBase.get_values_by_factor_name(session, self.name)
            for value in values:
                session.delete(value)
            session.commit()

    def __init__(self, db: DataBase, name: str) -> None:
        """Не использовать напрямую"""

        self._db = db
        self._name = name

        # check existance
        with self._db.session as session:
            self.get_db_table(session)

    def get_db_table(self, session: Session) -> Factor:
        return DataBase.get_factor_by_name(session, self.name)

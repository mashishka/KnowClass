from __future__ import annotations

import json
from typing import Union

from sqlalchemy.orm import Session

from data_utils.controllers.ValueController import ValueController
from data_utils.core import DataBase
from data_utils.imp.position import TablePosition
from data_utils.imp.rerased import reraised_class
from data_utils.imp.tables import AdditionalData, Factor, Value


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

    # удаление по имени
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
            factor_id = TablePosition.get_field_by_position(
                session, Factor, position, Factor.factor_id
            )
        return FactorController(db, factor_id)

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
            return json.loads(
                DataBase.get_additional_data_field(session, AdditionalData.count)
            )["factors"]

    # максимальное количество значений среди всех факторов
    @staticmethod
    def get_max_value_count(db: DataBase) -> int:
        with db.session as session:
            return max(
                json.loads(
                    DataBase.get_additional_data_field(session, AdditionalData.count)
                )["values"].values()
            )

    # получение всех факторов
    @staticmethod
    def get_all(db: DataBase) -> list[FactorController]:
        with db.session as session:
            all = DataBase.get_all_field(session, Factor.factor_id)
        return [FactorController(db, val) for val in all]

    # удаление всех факторов
    @staticmethod
    def remove_all(db: DataBase) -> None:
        with db.session as session:
            DataBase.delete_all(session, Factor)
            session.commit()

    # оператор сравнения
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FactorController):
            return False
        return self._id == other._id

    # атрибут имени (нельзя изменить)
    @property
    def name(self) -> str:
        with self._db.session as session:
            return DataBase.get_field_by_id(session, Factor, self._id, Factor.name)

    # атрибут текста
    @property
    def text(self) -> str:
        with self._db.session as session:
            return DataBase.get_field_by_id(session, Factor, self._id, Factor.text_)

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
            return bool(
                DataBase.get_field_by_id(session, Factor, self._id, Factor.active)
            )

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
                session,
                self.get_db_table(session),
                other.get_db_table(session),
            )
            session.commit()

    # создание значения фактора по уникальному (в рамках одного фактора) имени
    def make_value(self, name: str) -> ValueController:
        with self._db.session as session:
            value = Value(factor_id=self._id, name=name)
            session.add(value)
            session.commit()
            return ValueController(self._db, value.value_id)

    # получение значения фактора по имени
    def get_value(self, name: str) -> ValueController:
        return ValueController(self._db, (self.name, name))

    # удаление значения фактора по имени
    def remove_value(self, name: str) -> None:
        with self._db.session as session:
            value = DataBase.get_value_by_names(session, self.name, name)
            session.delete(value)
            session.commit()

    # получение значения фактора по позиции
    def get_value_by_position(self, position: int) -> ValueController:
        with self._db.session as session:
            value_id = TablePosition.get_Value_field_by_position(
                session, self._id, position, Value.value_id
            )
        return ValueController(self._db, value_id)

    # удаление значения фактора по позиции
    def remove_value_by_position(self, position: int) -> None:
        with self._db.session as session:
            factor = TablePosition.get_Value_by_position(
                session,
                self._id,
                position,
            )
            session.delete(factor)
            session.commit()

    # количество значений фактора
    def get_values_count(self) -> int:
        with self._db.session as session:
            return json.loads(
                DataBase.get_additional_data_field(session, AdditionalData.count)
            )["values"][str(self._id)]

    # получение всех значений фактора
    def get_values(self) -> list[ValueController]:
        with self._db.session as session:
            raw = DataBase.get_value_ids_by_factor_id(session, self._id)
        return [ValueController(self._db, val) for val in raw]

    # удаление всех значений фактора
    def remove_values(self) -> None:
        with self._db.session as session:
            values = DataBase.get_values_by_factor_id(session, self._id)
            for value in values:
                session.delete(value)
            session.commit()

    def __init__(self, db: DataBase, name_or_id: Union[str, int]) -> None:
        """Не использовать напрямую"""

        self._db = db
        if isinstance(name_or_id, int):
            self._id = name_or_id
        else:
            with self._db.session as session:
                self._id = DataBase.get_factor_by_name(session, name_or_id).factor_id

    def get_db_table(self, session: Session) -> Factor:
        return DataBase.get_table_by_id(session, Factor, self._id)

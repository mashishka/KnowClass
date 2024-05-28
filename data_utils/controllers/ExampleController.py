from __future__ import annotations

from typing import TypeVar

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute

from data_utils.controllers.FactorController import FactorController
from data_utils.controllers.ResultController import (
    ResultController,
    ResultValueController,
)
from data_utils.controllers.ValueController import ValueController
from data_utils.core import DataBase
from data_utils.imp.position import TablePosition
from data_utils.imp.rerased import reraised_class
from data_utils.imp.tables import Example, ExampleFactorValue, ResultValue, Value

_T = TypeVar("_T")


# класс для работы с примерами
# у примера уникальные - id и позиция
@reraised_class()
class ExampleController:
    # создание с обязательными параметрами
    @staticmethod
    def make(
        db: DataBase, weight: float, result_value: ResultValueController
    ) -> ExampleController:
        with db.session as session:
            example = Example(weight=weight, result_value_id=result_value._id)
            session.add(example)
            session.commit()

            return ExampleController(db, example.example_id)

    # получение по id
    @staticmethod
    def get(db: DataBase, id: int) -> ExampleController:
        # check existance
        res = ExampleController(db, id)
        with db.session as session:
            res.get_db_table(session)
        return res

    # удаление по id
    @staticmethod
    def remove(db: DataBase, id: int) -> None:
        with db.session as session:
            example = DataBase.get_table_by_id(session, Example, id)
            session.delete(example)
            session.commit()

    # получение по позиции
    @staticmethod
    def get_by_position(db: DataBase, position: int) -> ExampleController:
        with db.session as session:
            example_id = TablePosition.get_field_by_position(
                session, Example, position, Example.example_id
            )
        return ExampleController(db, example_id)

    # удаление по позиции
    @staticmethod
    def remove_by_position(db: DataBase, position: int) -> None:
        with db.session as session:
            example = TablePosition.get_by_position(session, Example, position)
            session.delete(example)
            session.commit()

    # количество примеров
    @staticmethod
    def get_count(db: DataBase) -> int:
        with db.session as session:
            return DataBase.get_count(session, Example)

    # получение всех примеров
    @staticmethod
    def get_all(db: DataBase) -> list[ExampleController]:

        with db.session as session:
            all = DataBase.get_all_field(session, Example.example_id)
        return [ExampleController(db, val) for val in all]

    # удаление всех примеров
    @staticmethod
    def remove_all(db: DataBase) -> None:
        with db.session as session:
            DataBase.delete_all(session, Example)
            session.commit()

    # оператор сравнения
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExampleController):
            return False
        return self._id == other._id

    # атрибут id
    @property
    def id(self) -> int:
        return self._id

    # атрибут веса
    @property
    def weight(self) -> float:
        with self._db.session as session:
            return DataBase.get_field_by_id(session, Example, self._id, Example.weight)

    @weight.setter
    def weight(self, value: float) -> None:
        with self._db.session as session:
            example = self.get_db_table(session)
            example.weight = value
            session.commit()

    # атрибут активности примера
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
    def swap_position(self, other: ExampleController) -> None:
        with self._db.session as session:
            TablePosition.change_swap(
                session, self.get_db_table(session), other.get_db_table(session)
            )
            session.commit()

    # атрибут значения результата
    # NOTE: можно оптимизировать
    @property
    def result_value(self) -> ResultValueController:
        with self._db.session as session:
            db_result_value = DataBase.get_table_by_id(
                session,
                ResultValue,
                DataBase.get_field_by_id(
                    session, Example, self._id, Example.result_value_id
                ),
            )
            # можно одним запросом?
            return ResultController.get(self._db).get_value(db_result_value.name)

    @result_value.setter
    def result_value(self, result_value: ResultValueController) -> None:
        with self._db.session as session:
            example = self.get_db_table(session)
            example.result_value_id = result_value.get_db_table(session).result_value_id
            session.commit()

    # получение значения на факторе
    # NOTE: None если * в таблице
    def get_value(self, factor: FactorController) -> ValueController | None:
        with self._db.session as session:
            example_value = (
                session.query(
                    ExampleFactorValue.example_id, ExampleFactorValue.value_id
                )
                .filter_by(example_id=self._id)
                .join(Value)
                .filter(Value.factor_id == factor._id)
                .one_or_none()
            )
            if example_value is None:
                return None
            value = DataBase.get_table_by_id(session, Value, example_value.value_id)
            return factor.get_value(value.name)

    # установка значения на факторе (с перезаписью)
    def add_value(self, value: ValueController) -> None:
        with self._db.session as session:
            values = self.get_values()
            factor_ids = [
                value.factor.get_db_table(session).factor_id
                for value in values
                if value is not None
            ]
            try:
                ind = factor_ids.index(value.factor.get_db_table(session).factor_id)
                # замена значения на новое
                self._remove_value(session, factor_ids[ind])
            except ValueError:
                pass

            db_value = value.get_db_table(session)
            new_value = ExampleFactorValue(
                example_id=self._id, value_id=db_value.value_id
            )
            session.add(new_value)
            session.commit()

    # удаление значения на факторе
    # NOTE: делает * в таблице
    def remove_value(self, factor: FactorController) -> None:
        with self._db.session as session:
            self._remove_value(session, factor.get_db_table(session).factor_id)
            session.commit()

    # количество значений по факторам
    def get_values_count(self) -> int:
        with self._db.session as session:
            return DataBase.get_count(
                session, ExampleFactorValue, {"example_id": self._id}
            )

    # получение значений на всех факторах
    # NOTE: только те, не *
    # NOTE: можно оптимизировать
    def get_values(self) -> list[ValueController]:
        factors = FactorController.get_all(self._db)
        res = []
        for factor in factors:
            value = self.get_value(factor)
            if value is not None:
                res.append(value)
        return res

    # удаление значений на всех факторах
    # NOTE: можно оптимизировать
    def remove_values(self):
        factors = FactorController.get_all(self._db)
        for factor in factors:
            if self.get_value(factor):
                self.remove_value(factor)

    def __init__(self, db: DataBase, id: int) -> None:
        """Не использовать напрямую"""

        self._db = db
        self._id = id

    def get_db_table(self, session: Session) -> Example:
        return DataBase.get_table_by_id(session, Example, self._id)

    def _remove_value(self, session: Session, factor_id: int) -> None:
        example_value = (
            session.query(ExampleFactorValue)
            .filter_by(example_id=self._id)
            .join(Value)
            .filter(Value.factor_id == factor_id)
            .one()
        )
        session.delete(example_value)

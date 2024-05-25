import json
from typing import Sequence, TypeAlias, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute

from data_utils.core import DataBase
from data_utils.errors import InvalidPosition
from data_utils.imp.table_mappers import GetByPosTable, table_to_id_name, table_to_position_name
from data_utils.imp.tables import AdditionalData, Example, Factor, ResultValue, Value

PosTableGlobalIndex: TypeAlias = Example | Factor | ResultValue
PosTable: TypeAlias = PosTableGlobalIndex | Value
_T = TypeVar("_T")


# реализация изменения/получения позиций
class TablePosition:

    # NOTE: don't work for Value
    @staticmethod
    def get_by_position(
        session: Session,
        table: type[_T],  # NOTE: _T is GetByPosTable
        position: int,
    ) -> _T:  # same as table
        # NOTE: наверное, можно лучше реализовать
        _table: type[GetByPosTable] = table  # type: ignore
        positions = TablePosition._get_positions_global(session, _table)

        try:
            return (
                session.query(table)
                .filter_by(**{table_to_id_name[_table]: positions[position]})
                .one()
            )
        except IndexError as ex:
            raise InvalidPosition() from ex

    @staticmethod
    def get_field_by_position(
        session: Session,
        table: type[GetByPosTable],
        position: int,
        field: InstrumentedAttribute[_T],
    ) -> _T:
        positions = TablePosition._get_positions_global(session, table)

        try:
            return session.scalars(
                select(field).filter_by(**{table_to_id_name[table]: positions[position]})
            ).one()
        except IndexError as ex:
            raise InvalidPosition() from ex

    @staticmethod
    def get_Value_field_by_position(
        session: Session,
        factor_id: int,
        position: int,
        field: InstrumentedAttribute[_T],
    ) -> _T:
        positions = json.loads(
            DataBase.get_field_by_id(session, Factor, factor_id, Factor.value_positions)
        )

        try:
            return session.scalars(
                select(field).filter_by(**{table_to_id_name[Value]: positions[position]})
            ).one()
        except IndexError as ex:
            raise InvalidPosition() from ex

    @staticmethod
    def get_Value_by_position(session: Session, factor_id: int, position: int) -> Value:
        positions = json.loads(
            DataBase.get_field_by_id(session, Factor, factor_id, Factor.value_positions)
        )

        try:
            return (
                session.query(Value)
                .filter_by(**{table_to_id_name[Value]: positions[position]})
                .one()
            )
        except IndexError as ex:
            raise InvalidPosition() from ex

    @staticmethod
    def get_position(session: Session, elem: PosTable) -> int:
        id = TablePosition._get_id(elem)

        positions = TablePosition._get_positions(session, elem)
        return positions.index(id)

    @staticmethod
    def change_insert(session: Session, elem: PosTable, new_position: int):
        id = TablePosition._get_id(elem)

        positions = TablePosition._get_positions(session, elem)

        if new_position < 0 or new_position >= len(positions):
            raise InvalidPosition()

        positions.remove(id)
        positions.insert(new_position, id)

        TablePosition._set_positions(session, elem, positions)

    @staticmethod
    def change_swap(session: Session, elem: PosTable, swap_with_elem: PosTable):
        id = TablePosition._get_id(elem)
        swap_with_id = TablePosition._get_id(swap_with_elem)

        positions = TablePosition._get_positions(session, elem)

        index_id = positions.index(id)
        index_swap_with_id = positions.index(swap_with_id)

        positions[index_id], positions[index_swap_with_id] = (
            positions[index_swap_with_id],
            positions[index_id],
        )

        TablePosition._set_positions(session, elem, positions)

    @staticmethod
    def _get_positions(session: Session, elem: PosTable) -> list[int]:
        if isinstance(elem, Value):
            return json.loads(elem.factor.value_positions)
        table = type(elem)
        return TablePosition._get_positions_global(session, table)

    @staticmethod
    def _get_positions_global(session: Session, table: type[PosTableGlobalIndex]) -> list[int]:
        pos_data = DataBase.get_additional_data_field(
            session,
            getattr(AdditionalData, table_to_position_name[table]),
        )
        return json.loads(pos_data)

    @staticmethod
    def _set_positions(session: Session, elem: PosTable, positions: list[int]):
        if isinstance(elem, Value):
            elem.factor.value_positions = json.dumps(positions)
            return
        table = type(elem)
        data = DataBase.get_table_by_id(
            session,
            AdditionalData,
            DataBase.get_additional_data_field(session, AdditionalData.id),
        )
        setattr(data, table_to_position_name[table], json.dumps(positions))

    @staticmethod
    def _get_id(elem: PosTable) -> int:
        table = type(elem)
        return getattr(elem, table_to_id_name[table])

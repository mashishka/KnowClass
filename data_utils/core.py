from __future__ import annotations

from pathlib import Path, PurePath
from typing import Any, Sequence, TypeAlias, TypeVar

from sqlalchemy import MetaData, create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.attributes import InstrumentedAttribute

from data_utils.imp.assert_scheme import assert_addition_data, assert_scheme
from data_utils.imp.rerased import reraised_class
from data_utils.imp.table_mappers import GetByIdTables, table_to_id_name, table_to_position_name
from data_utils.imp.tables import (
    AdditionalData,
    Base,
    Example,
    ExampleFactorValue,
    Factor,
    ResultValue,
    Value,
)

metadata = Base.metadata

_T = TypeVar("_T")
AllTables: TypeAlias = Example | Factor | ResultValue | Value | ExampleFactorValue | AdditionalData
Table_T = TypeVar(
    "Table_T", Example, Factor, ResultValue, Value, ExampleFactorValue, AdditionalData
)


# Класс для создания хранения и загрузки бд
@reraised_class()
class DataBase:
    # создаёт файл path (перезаписывает, если существует)
    @staticmethod
    def create(path: PurePath) -> DataBase:
        return DataBase(path, False)

    # загружает бд из файла path
    @staticmethod
    def load(path: PurePath) -> DataBase:
        return DataBase(path, True)

    # возвращает текущий путь к файлу бд
    @property
    def path(self) -> str:
        return self._save_path.as_posix()

    # закрывает соединение с бд, дальнейшее использование существуюзих контроллеров и DataBase не будет работать
    def close(self):
        self._sessions = None
        self._engine.dispose(True)
        self._engine = None

    # NOTE: не предполагается для использования напрямую (использовать create/load)
    def __init__(self, path: PurePath, load: bool) -> None:
        self._save_path = Path(path).absolute()
        # , poolclass=SingletonThreadPool
        self._engine = create_engine(f"sqlite+pysqlite:///{path}")
        self._sessions = sessionmaker(
            bind=self._engine,
            autoflush=False,  # NOTE: может не нужно
        )
        if load:
            loaded_meta = MetaData()
            loaded_meta.reflect(self._engine)
            assert_scheme(metadata, loaded_meta)
            with self._sessions() as session:
                assert_addition_data(session)
        else:
            if self._save_path.exists():
                self._save_path.unlink()

            with self._engine.begin() as conn:
                conn.connection.executescript(  # type: ignore
                    (Path(__file__).parent / "imp" / "all.sql").read_text()
                )

    # Общие функции, не входящие в контроллеры, предназначены для их реализации
    @property
    def session(self):
        return self._sessions()

    @staticmethod
    def get_additional_data_field(session: Session, field: InstrumentedAttribute[_T]) -> Any:
        return session.scalar(select(field))

    @staticmethod
    def get_count(
        session: Session,
        table_type: type[AllTables],
        filter_by_args: dict | None = None,
    ) -> int:
        if filter_by_args is None:
            return session.query(table_type).count()
        return session.query(table_type).filter_by(**filter_by_args).count()

    @staticmethod
    def get_all_field(
        session: Session,
        field: InstrumentedAttribute[_T],
    ) -> Sequence[_T]:
        return session.scalars(select(field)).all()

    @staticmethod
    def delete_all(session: Session, table_type: type[AllTables]) -> None:
        session.query(table_type).delete()

    @staticmethod
    def get_table_by_id(session: Session, table: type[Table_T], id: int) -> Table_T:
        return session.query(table).filter_by(**{table_to_id_name[table]: id}).one()

    @staticmethod
    def get_factor_by_name(session: Session, name: str) -> Factor:
        return session.query(Factor).filter_by(name=name).one()

    @staticmethod
    def get_value_by_names(session: Session, factor_name: str, name: str) -> Value:
        factor = DataBase.get_factor_by_name(session, factor_name)
        return session.query(Value).filter_by(factor_id=factor.factor_id, name=name).one()

    @staticmethod
    def get_value_ids_by_factor_id(session: Session, factor_id: int) -> Sequence[int]:
        return session.scalars(select(Value.value_id).filter_by(factor_id=factor_id)).all()

    @staticmethod
    def get_values_by_factor_id(session: Session, factor_id: int) -> Sequence[Value]:
        return session.scalars(select(Value).filter_by(factor_id=factor_id)).all()

    @staticmethod
    def get_result_value_by_name(session: Session, name: str) -> ResultValue:
        return session.scalars(select(ResultValue).filter_by(name=name)).one()

    @staticmethod
    def get_field_by_id(
        session: Session,
        table: type[AllTables],
        id: int,
        field: InstrumentedAttribute[_T],
    ) -> _T:
        return session.scalars(select(field).filter_by(**{table_to_id_name[table]: id})).one()

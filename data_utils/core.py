from __future__ import annotations

import re
from pathlib import Path, PurePath
from typing import Any, Type, TypeVar

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.attributes import InstrumentedAttribute

from data_utils.imp.assert_scheme import assert_addition_data, assert_scheme
from data_utils.imp.rerased import reraised_class
from data_utils.imp.tables import AdditionalData, Base, Example, Factor, ResultValue, Value

metadata = Base.metadata

_T = TypeVar("_T")


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
        self._engine = create_engine(f"sqlite:///{path}")
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

            with self._sessions() as session:
                # NOTE: парсим sql-выражения (на ; заканчиваются), спец случай - триггеры (; + END;)
                for statement in re.findall(
                    "([^;]+;([^E]*END;)*)", (Path(__file__).parent / "imp" / "all.sql").read_text()
                ):
                    session.execute(text(statement[0]))
                session.commit()

    # Общие функции, не входящие в контроллеры, предназначены для их реализации
    @property
    def session(self):
        return self._sessions()

    @staticmethod
    def get_count(
        session: Session, table_type: Type[_T], filter_by_args: dict | None = None
    ) -> int:
        if filter_by_args is None:
            return session.query(table_type).count()
        return session.query(table_type).filter_by(**filter_by_args).count()

    @staticmethod
    def get_all(session: Session, table_type: Type[_T]) -> list[_T]:
        return session.query(table_type).all()

    @staticmethod
    def get_factor_by_id(session: Session, id: int) -> Factor:
        return session.query(Factor).filter_by(factor_id=id).one()

    @staticmethod
    def get_factor_by_name(session: Session, name: str) -> Factor:
        return session.query(Factor).filter_by(name=name).one()

    @staticmethod
    def get_value_by_id(session: Session, id: int) -> Value:
        return session.query(Value).filter_by(value_id=id).one()

    @staticmethod
    def get_value_by_names(session: Session, factor_name: str, name: str) -> Value:
        factor = DataBase.get_factor_by_name(session, factor_name)
        return session.query(Value).filter_by(factor_id=factor.factor_id, name=name).one()

    @staticmethod
    def get_values_by_factor_name(session: Session, factor_name: str) -> list[Value]:
        factor = DataBase.get_factor_by_name(session, factor_name)
        return session.query(Value).filter_by(factor_id=factor.factor_id).all()

    @staticmethod
    def get_result_value_by_name(session: Session, name: str) -> ResultValue:
        return session.query(ResultValue).filter_by(name=name).one()

    @staticmethod
    def get_result_value_by_id(session: Session, id: int) -> ResultValue:
        return session.query(ResultValue).filter_by(result_value_id=id).one()

    @staticmethod
    def get_result_values(session: Session) -> list[ResultValue]:
        return session.query(ResultValue).all()

    @staticmethod
    def get_addition_data(session: Session) -> AdditionalData:
        return session.query(AdditionalData).one()

    @staticmethod
    def get_example_by_id(session: Session, example_id: int) -> Example:
        return session.query(Example).filter_by(example_id=example_id).one()

    @staticmethod
    def get_example_filed_by_id(
        session: Session, example_id: int, field: InstrumentedAttribute[_T]
    ) -> _T:
        return session.query(field).filter_by(example_id=example_id).one()._tuple()[0]

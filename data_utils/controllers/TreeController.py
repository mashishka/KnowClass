from __future__ import annotations

from sqlalchemy.orm import Session

from data_utils.core import DataBase
from data_utils.imp.tables import AdditionalData
from tree.TreeClass import _DecisionNode, _LeafNode

import pickle


# класс для работы с деревом правил
# NOTE: здесь (например) можно в дальнейшем реализовать методы для конкретного типа предствления дерева
class TreeController:
    @staticmethod
    def get(db: DataBase) -> TreeController:
        return TreeController(db)

    # байтовое представление дерева правил
    # NOTE: None == не задано
    @property
    def data(self) -> _DecisionNode | None:
        with self._db.session as session:
            byte_tree = DataBase.get_field_by_id(
                session,
                AdditionalData,
                self._id,
                AdditionalData.tree_data,
            )
            if isinstance(byte_tree, bytes):
                tree = pickle.loads(byte_tree)
                return tree
            return None

    # NOTE: None == не задано
    @data.setter
    def data(self, value: _DecisionNode | None) -> None:
        with self._db.session as session:
            data = self.get_db_table(session)
            data.tree_data = pickle.dumps(value)
            session.commit()

    def __init__(self, db: DataBase) -> None:
        """Не использовать напрямую"""

        self._db = db
        with self._db.session as session:
            self._id = DataBase.get_additional_data_field(session, AdditionalData.id)

    def get_db_table(self, session: Session) -> AdditionalData:
        return DataBase.get_table_by_id(session, AdditionalData, self._id)

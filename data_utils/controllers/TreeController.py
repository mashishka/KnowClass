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

    def __init__(self, db: DataBase) -> None:
        """Не использовать напрямую"""

        self._db = db

        # check existance
        with self._db.session as session:
            self.get_db_table(session)

    # байтовое представление дерева правил
    # NOTE: None == не задано
    @property
    def data(self) -> _DecisionNode | None:
        with self._db.session as session:
            byte_tree = self.get_db_table(session).tree_data
            if isinstance(byte_tree, bytes):
                if byte_tree is not None:  # проверка на None
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

    def get_db_table(self, session: Session) -> AdditionalData:
        return DataBase.get_addition_data(session)

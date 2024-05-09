from data_utils.controllers.TreeController import TreeController
from data_utils.core import DataBase


class TestData:
    def test_get_default(self, new_db: DataBase):
        tree = TreeController.get(new_db)

        tree.data == None

    def test_get(self, new_db: DataBase):
        tree = TreeController.get(new_db)

        tree.data = "tree".encode()
        assert tree.data.decode() == "tree"

    def test_reset(self, new_db: DataBase):
        tree = TreeController.get(new_db)

        tree.data = "tree".encode()
        tree.data = None
        assert tree.data == None

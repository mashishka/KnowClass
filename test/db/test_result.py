from random import shuffle

import pytest
from db.db_fixtures import default_factor, make_default_result_values

from data_utils.controllers.ResultController import ResultController
from data_utils.core import DataBase
from data_utils.errors import DataBaseError
from data_utils.ResultMethodType import ResultMethodType


class TestGet:
    def test_get(self, new_db: DataBase):
        result = ResultController.get(new_db)


class TestName:
    def test_get(self, new_db: DataBase):
        result = ResultController.get(new_db)

        assert result.name == "RESULT"

    def test_set_error(self, new_db: DataBase):
        result = ResultController.get(new_db)

        with pytest.raises(AttributeError):
            result.name = "new_name"  # type: ignore


class TestText:
    def test_get(self, new_db: DataBase):
        result = ResultController.get(new_db)

        assert result.text == ""

    def test_set(self, new_db: DataBase):
        result = ResultController.get(new_db)

        result.text = "new_text"
        assert result.text == "new_text"


class TestType:
    def test_get(self, new_db: DataBase):
        result = ResultController.get(new_db)

        assert result.type == None

    def test_set(self, new_db: DataBase):
        result = ResultController.get(new_db)

        for value in ResultMethodType:
            result.type = value
            assert result.type == value

        result.type = None
        assert result.type == None

    def test_set_error(self, new_db: DataBase):
        result = ResultController.get(new_db)

        with pytest.raises(AttributeError):
            result.type = "new_type"  # type: ignore


class TestGetValues:
    def test_get(self, new_db: DataBase):
        result = ResultController.get(new_db)
        values_data = make_default_result_values(new_db)
        added_values_names = [data.result_value.name for data in values_data]

        values = result.get_values()
        values_names = [value.name for value in values]

        assert sorted(added_values_names) == sorted(values_names)


class TestRemoveValues:
    def test_remove(self, new_db: DataBase):
        result = ResultController.get(new_db)
        values_data = make_default_result_values(new_db)

        result.remove_values()

        all = result.get_values()
        assert all == []

    def test_remove_empty(self, new_db: DataBase):
        result = ResultController.get(new_db)

        result.remove_values()

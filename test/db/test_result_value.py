from random import shuffle

import pytest
from db.db_fixtures import make_default_result_value, make_default_result_values

from data_utils.controllers.ResultController import ResultController
from data_utils.controllers.ResultValueController import ResultValueController
from data_utils.core import DataBase
from data_utils.errors import DataBaseError, InvalidPosition


class TestMake:
    def test_make(self, new_db: DataBase):
        result = ResultController.get(new_db)
        value_name = "name"

        value = result.make_value(value_name)

        assert value.name == value_name
        assert value.text == ""

    def test_make_same_name_error(self, new_db: DataBase):
        result = ResultController.get(new_db)
        [value_name, value_text, value] = make_default_result_value(new_db).unpack()

        with pytest.raises(DataBaseError):
            value = result.make_value(value_name)


class TestGet:
    def test_get(self, new_db: DataBase):
        result = ResultController.get(new_db)
        [value_name, value_text, value] = make_default_result_value(new_db).unpack()

        get_value = result.get_value(value_name)

        assert get_value.name == value_name
        assert get_value.text == value_text

    def test_get_error(self, new_db: DataBase):
        result = ResultController.get(new_db)

        with pytest.raises(DataBaseError):
            get_value = result.get_value("name")


class TestRemove:
    def test_remove(self, new_db: DataBase):
        result = ResultController.get(new_db)
        [value_name, value_text, value] = make_default_result_value(new_db).unpack()

        result.remove_value(value_name)
        with pytest.raises(DataBaseError):
            get_value = result.get_value(value_name)

    def test_remove_error(self, new_db: DataBase):
        result = ResultController.get(new_db)

        with pytest.raises(DataBaseError):
            result.remove_value("name")


class TestName:
    def test_get(self, new_db: DataBase):
        [value_name, value_text, value] = make_default_result_value(new_db).unpack()

        assert value.name == value_name

    def test_set_error(self, new_db: DataBase):
        [value_name, value_text, value] = make_default_result_value(new_db).unpack()

        with pytest.raises(AttributeError):
            value.name = "new_name"  # type: ignore


class TestText:
    def test_get(self, new_db: DataBase):
        [value_name, value_text, value] = make_default_result_value(new_db).unpack()

        assert value.text == value_text

    def test_set(self, new_db: DataBase):
        [value_name, value_text, value] = make_default_result_value(new_db).unpack()

        value.text = "new_text"
        assert value.text == "new_text"


class TestLikelihood:
    def test_get(self, new_db: DataBase):
        [value_name, value_text, value] = make_default_result_value(new_db).unpack()

        assert value.likelihood == None

    def test_set(self, new_db: DataBase):
        [value_name, value_text, value] = make_default_result_value(new_db).unpack()

        value.likelihood = 5.5
        assert value.likelihood == 5.5

        value.likelihood = None
        assert value.likelihood == None


class TestPosition:
    def _ordered_names(self, result: ResultController):
        return [result.get_value_by_position(i).name for i in range(len(result.get_values()))]

    def _compare_positions(self, names: list[str], result: ResultController):
        actual_names = self._ordered_names(result)
        assert actual_names == names

    def test_get(self, new_db: DataBase):
        [value_name, value_text, value] = make_default_result_value(new_db).unpack()

        assert value.position == 0

    def test_get_more(self, new_db: DataBase):
        result = ResultController.get(new_db)
        values_data = make_default_result_values(new_db)

        start_names = [value.name for value in values_data]
        self._compare_positions(start_names, result)

    def test_set_error(self, new_db: DataBase):
        [value_name, value_text, value] = make_default_result_value(new_db).unpack()

        with pytest.raises(DataBaseError):
            value.position = 2

        with pytest.raises(DataBaseError):
            value.position = -1

    def test_set(self, new_db: DataBase):
        result = ResultController.get(new_db)
        values_data = make_default_result_values(new_db)

        new_positions = list(range(len(values_data)))
        names = [values_data[i].name for i in new_positions]
        shuffle(new_positions)
        print(new_positions)
        for new_position, i in zip(new_positions, range(len(new_positions))):
            result.get_value_by_position(i).position = new_position
            name = names[i]
            names.remove(name)
            names.insert(new_position, name)
        self._compare_positions(names, result)

    def test_set_swap(self, new_db: DataBase):
        result = ResultController.get(new_db)
        values_data = make_default_result_values(new_db)

        names = [data.name for i, data in enumerate(values_data)]
        positions = list(range(len(values_data) - 1))
        swap_with = positions.copy()
        shuffle(swap_with)

        for pos, swap_with_position in zip(positions, swap_with):
            a = result.get_value_by_position(pos)
            b = result.get_value_by_position(swap_with_position)
            a.swap_position(b)
            names[pos], names[swap_with_position] = (
                names[swap_with_position],
                names[pos],
            )
        self._compare_positions(names, result)

    def test_get_by_position(self, new_db: DataBase):
        result = ResultController.get(new_db)
        values_data = make_default_result_values(new_db)

        positions = [i for i, data in enumerate(values_data)]
        shuffle(positions)

        for pos in positions:
            assert result.get_value_by_position(pos).position == pos

    def test_remove_by_position(self, new_db: DataBase):
        result = ResultController.get(new_db)
        [value_name, value_text, value] = make_default_result_value(new_db).unpack()
        position = value.position

        result.remove_value_by_position(position)

        with pytest.raises(InvalidPosition):
            result.get_value_by_position(position)

        with pytest.raises(DataBaseError):
            result.get_value(value_name)


class TestEqual:
    def test_equal(self, new_db: DataBase):
        values_data = make_default_result_values(new_db)
        result = ResultController.get(new_db)
        value1 = values_data[0].result_value
        value2 = values_data[1].result_value

        assert value1 == value1
        assert value1 != value2
        assert value1 != 5

    def test_get_equal(self, new_db: DataBase):
        values_data = make_default_result_values(new_db)
        result = ResultController.get(new_db)
        value1 = values_data[0].result_value
        value2 = values_data[1].result_value

        assert result.get_value(value1.name) == value1
        assert result.get_value(value1.name) != value2

        assert result.get_value(value1.name) == result.get_value(value1.name)

    def test_get_by_position_equal(self, new_db: DataBase):
        values_data = make_default_result_values(new_db)
        result = ResultController.get(new_db)
        value1 = values_data[0].result_value
        value2 = values_data[1].result_value

        assert result.get_value_by_position(value1.position) == value1
        assert result.get_value_by_position(value1.position) != value2
        assert result.get_value_by_position(value1.position) == result.get_value_by_position(
            value1.position
        )

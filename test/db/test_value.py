from random import shuffle

import pytest
from db.db_fixtures import (
    default_value,
    make_default_factor,
    make_default_factor_and_values,
    make_default_factors,
    make_default_factors_and_values,
    make_default_value,
)

from data_utils.controllers.FactorController import FactorController
from data_utils.controllers.ValueController import ValueController
from data_utils.core import DataBase
from data_utils.errors import DataBaseError, InvalidPosition


class TestMake:
    def test_make(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()
        value_name = "name"

        value = factor.make_value(value_name)

        assert value.name == value_name
        assert value.text == ""

    def test_make_same_name_in_diff_factors(self, new_db: DataBase):
        factors = make_default_factors(new_db)
        value_name = "name"

        for factor_data in factors:
            factor = factor_data.factor
            value = factor.make_value(value_name)

            assert value.name == value_name
            assert value.text == ""

    def test_make_same_name_in_factor_error(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()
        [value_name, value_text, value] = make_default_value(factor).unpack()

        with pytest.raises(DataBaseError):
            value = factor.make_value(value_name)


class TestGet:
    def test_get(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()
        [value_name, value_text, value] = make_default_value(factor).unpack()

        get_value = factor.get_value(value_name)

        assert get_value.name == value_name
        assert get_value.text == value_text

    def test_get_error(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()

        with pytest.raises(DataBaseError):
            get_value = factor.get_value("name")


class TestRemove:
    def test_remove(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()
        [value_name, value_text, value] = make_default_value(factor).unpack()

        factor.remove_value(value_name)
        with pytest.raises(DataBaseError):
            get_value = factor.get_value(value_name)

    def test_remove_error(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()

        with pytest.raises(DataBaseError):
            factor.remove_value("name")


class TestGetAll:
    def test_get_all(self, new_db: DataBase):
        factors_and_values = make_default_factors_and_values(new_db)
        added_value_pairs = []
        for factor_data, values in factors_and_values:
            added_value_pairs.extend([(factor_data.name, data.value.name) for data in values])

        all = ValueController.get_all(new_db)
        all_name_pairs = [(value.factor.name, value.name) for value in all]

        assert sorted(added_value_pairs) == sorted(all_name_pairs)

    def test_get_all_empty(self, new_db: DataBase):
        all = ValueController.get_all(new_db)

        assert all == []


class TestRemoveAll:
    def test_remove_all(self, new_db: DataBase):
        factors_and_values = make_default_factors_and_values(new_db)

        ValueController.remove_all(new_db)

        all = ValueController.get_all(new_db)
        assert all == []

    def test_remove_all_empty(self, new_db: DataBase):
        ValueController.remove_all(new_db)


class TestName:
    def test_get(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()
        [value_name, value_text, value] = make_default_value(factor).unpack()

        assert value.name == value_name

    def test_set_error(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()
        [value_name, value_text, value] = make_default_value(factor).unpack()

        with pytest.raises(AttributeError):
            value.name = "new_name"  # type: ignore


class TestText:
    def test_get(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()
        [value_name, value_text, value] = make_default_value(factor).unpack()

        assert value.text == value_text

    def test_set(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()
        [value_name, value_text, value] = make_default_value(factor).unpack()

        value.text = "new_text"
        assert value.text == "new_text"


class TestPosition:
    def _ordered_names(self, factor: FactorController):
        return [factor.get_value_by_position(i).name for i in range(len(factor.get_values()))]

    def _compare_positions(self, names: list[str], factor: FactorController):
        actual_names = self._ordered_names(factor)
        assert actual_names == names

    def test_get(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()
        [value_name, value_text, value] = make_default_value(factor).unpack()

        assert value.position == 0

    def test_get_more(self, new_db: DataBase):
        factors_and_values = make_default_factors_and_values(new_db)
        factor1 = factors_and_values[0][0].factor
        factor1_values = factors_and_values[0][1]

        start_names = [value.name for value in factor1_values]
        self._compare_positions(start_names, factor1)

    def test_set_error(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()
        [value_name, value_text, value] = make_default_value(factor).unpack()

        with pytest.raises(DataBaseError):
            value.position = 2

        with pytest.raises(DataBaseError):
            value.position = -1

    def test_set(self, new_db: DataBase):
        factors_and_values = make_default_factors_and_values(new_db)
        factor1_values = factors_and_values[0][1]
        factor1 = factors_and_values[0][0].factor

        new_positions = list(range(len(factor1_values)))
        names = [factor1_values[i].name for i in new_positions]
        shuffle(new_positions)
        print(new_positions)
        for new_position, i in zip(new_positions, range(len(new_positions))):
            factor1.get_value_by_position(i).position = new_position
            name = names[i]
            names.remove(name)
            names.insert(new_position, name)
        self._compare_positions(names, factor1)

    def test_set_swap(self, new_db: DataBase):
        factors_and_values = make_default_factors_and_values(new_db)
        factor1_values = factors_and_values[0][1]
        factor1 = factors_and_values[0][0].factor

        names = [data.name for i, data in enumerate(factor1_values)]
        positions = list(range(len(factor1_values) - 1))
        swap_with = positions.copy()
        shuffle(swap_with)

        for pos, swap_with_position in zip(positions, swap_with):
            a = factor1.get_value_by_position(pos)
            b = factor1.get_value_by_position(swap_with_position)
            a.swap_position(b)
            names[pos], names[swap_with_position] = (
                names[swap_with_position],
                names[pos],
            )
        self._compare_positions(names, factor1)

    def test_get_by_position(self, new_db: DataBase):
        factors_and_values = make_default_factors_and_values(new_db)
        factor1_values = factors_and_values[0][1]
        factor1 = factors_and_values[0][0].factor

        positions = [i for i, data in enumerate(factor1_values)]
        shuffle(positions)

        for pos in positions:
            assert factor1.get_value_by_position(pos).position == pos

    def test_remove_by_position(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()
        [value_name, value_text, value] = make_default_value(factor).unpack()
        position = value.position

        factor.remove_value_by_position(position)

        with pytest.raises(InvalidPosition):
            factor.get_value_by_position(position)

        with pytest.raises(DataBaseError):
            factor.get_value(value_name)


class TestFactor:
    def test_get(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()
        [value_name, value_text, value] = make_default_value(factor).unpack()

        assert value.factor.name == name

    def test_set_error(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()
        [value_name, value_text, value] = make_default_value(factor).unpack()

        with pytest.raises(AttributeError):
            value.factor = factor  # type: ignore


class TestEqual:
    def test_equal(self, new_db: DataBase):
        [factor_data, values_data] = make_default_factor_and_values(new_db)
        value1 = values_data[0].value
        value2 = values_data[1].value

        assert value1 == value1
        assert value1 != value2
        assert value1 != 5

    def test_get_equal(self, new_db: DataBase):
        [factor_data, values_data] = make_default_factor_and_values(new_db)
        factor = factor_data.factor
        value1 = values_data[0].value
        value2 = values_data[1].value

        assert factor.get_value(value1.name) == value1
        assert factor.get_value(value1.name) != value2

        assert factor.get_value(value1.name) == factor.get_value(value1.name)

    def test_get_by_position_equal(self, new_db: DataBase):
        [factor_data, values_data] = make_default_factor_and_values(new_db)
        factor = factor_data.factor
        value1 = values_data[0].value
        value2 = values_data[1].value

        assert factor.get_value_by_position(value1.position) == value1
        assert factor.get_value_by_position(value1.position) != value2
        assert factor.get_value_by_position(value1.position) == factor.get_value_by_position(
            value1.position
        )

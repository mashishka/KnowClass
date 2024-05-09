from random import shuffle

import pytest
from db.db_fixtures import (
    default_factor,
    make_default_factor,
    make_default_factor_and_values,
    make_default_factors,
)

from data_utils.controllers.FactorController import FactorController
from data_utils.core import DataBase
from data_utils.errors import DataBaseError, InvalidPosition


class TestMake:
    def test_make(self, new_db: DataBase):
        name = "name"

        factor = FactorController.make(new_db, name)

        assert factor.name == name
        assert factor.text == ""

    def test_make_error(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()

        with pytest.raises(DataBaseError):
            factor = FactorController.make(new_db, name)


class TestGet:
    def test_get(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()

        get_factor = FactorController.get(new_db, name)

        assert get_factor.name == name
        assert get_factor.text == text

    def test_get_error(self, new_db: DataBase):
        with pytest.raises(DataBaseError):
            get_factor = FactorController.get(new_db, "name")


class TestRemove:
    def test_remove(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()

        FactorController.remove(new_db, name)
        with pytest.raises(DataBaseError):
            get_factor = FactorController.get(new_db, name)

    def test_remove_error(self, new_db: DataBase):
        with pytest.raises(DataBaseError):
            FactorController.remove(new_db, "name")


class TestGetAll:
    def test_get_all(self, new_db: DataBase):
        factors = make_default_factors(new_db)

        all = FactorController.get_all(new_db)

        assert len(all) == len(factors)

        for db_factor, factor in zip(all, factors):
            assert db_factor.name == factor.name
            assert db_factor.text == factor.text

    def test_get_all_empty(self, new_db: DataBase):
        all = FactorController.get_all(new_db)

        assert all == []


class TestRemoveAll:
    def test_remove_all(self, new_db: DataBase):
        factors = make_default_factors(new_db)

        FactorController.remove_all(new_db)

        all = FactorController.get_all(new_db)
        assert all == []

    def test_remove_all_empty(self, new_db: DataBase):
        FactorController.remove_all(new_db)


class TestName:
    def test_get(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()

        assert factor.name == name

    def test_set_error(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()

        with pytest.raises(AttributeError):
            factor.name = "new_name"  # type: ignore


class TestText:
    def test_get(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()

        assert factor.text == text

    def test_set(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()

        factor.text = "new_text"
        assert factor.text == "new_text"


class TestActive:
    def test_get(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()

        assert factor.active == active

    def test_set(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()

        factor.active = False
        assert factor.active == False


class TestPosition:
    def _ordered_names(self, db: DataBase, factors: list[default_factor]):
        return [FactorController.get_by_position(db, i).name for i in range(len(factors))]

    def _compare_positions(self, db: DataBase, names: list[str], factors: list[default_factor]):
        # actual_positions = [data.value.position for data in values]
        actual_names = self._ordered_names(db, factors)
        assert actual_names == names

    def test_get(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()

        assert factor.position == 0

    def test_get_more(self, new_db: DataBase):
        factors = make_default_factors(new_db)
        start_names = [factor.name for factor in factors]
        self._compare_positions(new_db, start_names, factors)

    def test_set_error(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()

        with pytest.raises(DataBaseError):
            factor.position = 2

        with pytest.raises(DataBaseError):
            factor.position = -1

    def test_set(self, new_db: DataBase):
        factors = make_default_factors(new_db)

        new_positions = list(range(len(factors)))
        names = [factors[i].name for i in new_positions]
        shuffle(new_positions)
        print(new_positions)
        for new_position, i in zip(new_positions, range(len(new_positions))):
            FactorController.get_by_position(new_db, i).position = new_position
            name = names[i]
            names.remove(name)
            names.insert(new_position, name)
        self._compare_positions(new_db, names, factors)

    def test_set_swap(self, new_db: DataBase):
        factors = make_default_factors(new_db)

        names = [data.name for i, data in enumerate(factors)]
        positions = list(range(len(factors) - 1))
        swap_with = positions.copy()
        shuffle(swap_with)

        for pos, swap_with_position in zip(positions, swap_with):
            a = FactorController.get_by_position(new_db, pos)
            b = FactorController.get_by_position(new_db, swap_with_position)
            a.swap_position(b)
            names[pos], names[swap_with_position] = (
                names[swap_with_position],
                names[pos],
            )
        self._compare_positions(new_db, names, factors)

    def test_get_by_position(self, new_db: DataBase):
        factors = make_default_factors(new_db)

        positions = [i for i, data in enumerate(factors)]
        shuffle(positions)

        for pos in positions:
            assert FactorController.get_by_position(new_db, pos).position == pos

    def test_remove_by_position(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()
        position = factor.position

        FactorController.remove_by_position(new_db, position)

        with pytest.raises(InvalidPosition):
            FactorController.remove_by_position(new_db, position)

        with pytest.raises(DataBaseError):
            FactorController.get(new_db, name)


class TestGetValues:
    def test_get(self, new_db: DataBase):
        [factor_data, values_data] = make_default_factor_and_values(new_db)
        added_values_names = [data.value.name for data in values_data]

        values = factor_data.factor.get_values()
        values_names = [value.name for value in values]

        assert sorted(added_values_names) == sorted(values_names)


class TestRemoveValues:
    def test_remove(self, new_db: DataBase):
        [factor_data, values] = make_default_factor_and_values(new_db)
        [name, text, active, factor] = factor_data.unpack()

        factor.remove_values()

        all = factor.get_values()
        assert all == []

    def test_remove_empty(self, new_db: DataBase):
        [name, text, active, factor] = make_default_factor(new_db).unpack()

        factor.remove_values()


class TestEqual:
    def test_equal(self, new_db: DataBase):
        factors = make_default_factors(new_db)
        factor1 = factors[0].factor
        factor2 = factors[1].factor

        assert factor1 == factor1
        assert factor1 != factor2
        assert factor1 != 5

    def test_get_equal(self, new_db: DataBase):
        factors = make_default_factors(new_db)
        factor1 = factors[0].factor
        factor2 = factors[1].factor

        assert FactorController.get(new_db, factor1.name) == factor1
        assert FactorController.get(new_db, factor1.name) != factor2

        assert FactorController.get(new_db, factor1.name) == FactorController.get(
            new_db, factor1.name
        )

    def test_get_by_position_equal(self, new_db: DataBase):
        factors = make_default_factors(new_db)
        factor1 = factors[0].factor
        factor2 = factors[1].factor

        assert FactorController.get_by_position(new_db, factor1.position) == factor1
        assert FactorController.get_by_position(new_db, factor1.position) != factor2
        assert FactorController.get_by_position(
            new_db, factor1.position
        ) == FactorController.get_by_position(new_db, factor1.position)


class TestAllCount:
    def test_get(self, new_db: DataBase):
        factors = make_default_factors(new_db)

        count = FactorController.get_count(new_db)

        assert count == len(factors)

    def test_get_count_empty(self, new_db: DataBase):
        count = FactorController.get_count(new_db)

        assert count == 0

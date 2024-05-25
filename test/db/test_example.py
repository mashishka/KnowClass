from random import shuffle
from test.db.db_fixtures import (
    default_example,
    default_example_config,
    default_result_value_config,
    make_default_example,
    make_default_examples,
    make_default_factor_and_values,
    make_default_factors_and_values,
    make_default_result_value,
)

import pytest

from data_utils.controllers.ExampleController import ExampleController
from data_utils.controllers.ResultController import ResultController
from data_utils.core import DataBase
from data_utils.errors import DataBaseError, InvalidPosition


class TestMake:
    def test_make(self, new_db: DataBase):
        [value_name, value_text, value] = make_default_result_value(new_db).unpack()
        weight = 0.5

        example = ExampleController.make(new_db, weight, value)

        assert example.weight == weight
        assert example.result_value.name == value.name


class TestGet:
    def test_get(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(new_db).unpack()
        id = example.id

        get_example = ExampleController.get(new_db, id)

        assert get_example.id == id
        assert get_example.weight == weight
        assert get_example.result_value.name == res_value.name
        assert get_example.active == active

    def test_get_error(self, new_db: DataBase):
        with pytest.raises(DataBaseError):
            get_example = ExampleController.get(new_db, 0)


class TestRemove:
    def test_remove(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(new_db).unpack()
        id = example.id

        ExampleController.remove(new_db, id)
        with pytest.raises(DataBaseError):
            get_example = ExampleController.get(new_db, id)

    def test_remove_error(self, new_db: DataBase):
        with pytest.raises(DataBaseError):
            ExampleController.remove(new_db, 0)


class TestGetAll:
    def test_get_all(self, new_db: DataBase):
        examples = make_default_examples(new_db)

        all = ExampleController.get_all(new_db)

        assert len(all) == len(examples)

        for db_example, example_data in zip(all, examples):
            assert db_example.position == example_data.example.position

    def test_get_all_empty(self, new_db: DataBase):
        all = ExampleController.get_all(new_db)

        assert all == []


class TestRemoveAll:
    def test_remove_all(self, new_db: DataBase):
        examples = make_default_examples(new_db)

        ExampleController.remove_all(new_db)

        all = ExampleController.get_all(new_db)
        assert all == []

    def test_remove_all_empty(self, new_db: DataBase):
        ExampleController.remove_all(new_db)


class TestId:
    def test_get(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(new_db).unpack()

        example.id

    def test_set_error(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(new_db).unpack()

        with pytest.raises(AttributeError):
            example.id = 5  # type: ignore


class TestWeight:
    def test_get(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(new_db).unpack()

        assert example.weight == weight

    def test_set(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(new_db).unpack()

        example.weight = 5
        assert example.weight == 5


class TestResultValue:
    def test_get(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(new_db).unpack()

        assert example.result_value.name == res_value.name

    def test_set(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(new_db).unpack()
        res_value2 = make_default_result_value(
            new_db, default_result_value_config(name="rv2", text="")
        ).result_value

        example.result_value = res_value2
        assert example.result_value.name == res_value2.name


class TestActive:
    def test_get(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(new_db).unpack()

        assert example.active == active

    def test_set(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(new_db).unpack()

        example.active = False
        assert example.active == False


class TestPosition:
    def _ordered_ids(self, db: DataBase, factors: list[default_example]):
        return [ExampleController.get_by_position(db, i).id for i in range(len(factors))]

    def _compare_positions(self, db: DataBase, names: list[int], factors: list[default_example]):
        actual_names = self._ordered_ids(db, factors)
        assert actual_names == names

    def test_get(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(new_db).unpack()

        assert example.position == 0

    def test_last_position_make(self, new_db: DataBase):
        examples = make_default_examples(new_db)

        new_example = ExampleController.make(
            new_db, 0.5, ResultController.get(new_db).get_values()[0]
        )

        assert new_example.position == len(examples)

    def test_get_more(self, new_db: DataBase):
        examples = make_default_examples(new_db)
        expected_positions = list(range(len(examples)))

        actual_positions = [data.example.position for data in examples]
        assert expected_positions == actual_positions

    def test_set_error(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(new_db).unpack()

        with pytest.raises(DataBaseError):
            example.position = 2

        with pytest.raises(DataBaseError):
            example.position = -1

    def test_set(self, new_db: DataBase):
        examples = make_default_examples(new_db)

        new_positions = list(range(len(examples)))
        ids = [examples[i].example.id for i, data in enumerate(examples)]
        shuffle(new_positions)
        print(new_positions)
        for new_position, i in zip(new_positions, range(len(new_positions))):
            ExampleController.get_by_position(new_db, i).position = new_position
            name = ids[i]
            ids.remove(name)
            ids.insert(new_position, name)
        self._compare_positions(new_db, ids, examples)

    def test_set_swap(self, new_db: DataBase):
        examples = make_default_examples(new_db)

        ids = [examples[i].example.id for i, data in enumerate(examples)]
        positions = list(range(len(examples) - 1))
        swap_with = positions.copy()
        shuffle(swap_with)

        for pos, swap_with_position in zip(positions, swap_with):
            a = ExampleController.get_by_position(new_db, pos)
            b = ExampleController.get_by_position(new_db, swap_with_position)
            a.swap_position(b)
            ids[pos], ids[swap_with_position] = (
                ids[swap_with_position],
                ids[pos],
            )
        self._compare_positions(new_db, ids, examples)

    def test_get_by_position(self, new_db: DataBase):
        examples = make_default_examples(new_db)

        positions = list(range(len(examples)))
        shuffle(positions)

        for pos in positions:
            assert ExampleController.get_by_position(new_db, pos).position == pos

    def test_remove_by_position(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(new_db).unpack()
        id = example.position
        position = example.position

        ExampleController.remove_by_position(new_db, position)

        with pytest.raises(InvalidPosition):
            ExampleController.get_by_position(new_db, position)

        with pytest.raises(DataBaseError):
            ExampleController.get(new_db, id)


class TestGetValue:
    def test_get(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(new_db).unpack()
        added_values_names = [data.name for data in factor_values]

        values = example.get_values()
        values_names = [value.name for value in values]

        assert sorted(added_values_names) == sorted(values_names)

    def test_get_only_some_values(self, new_db: DataBase):
        result_value = make_default_result_value(new_db).result_value
        factors_and_values = make_default_factors_and_values(new_db)
        factor1_values = factors_and_values[0][1]
        [weight, res_value, active, factor_values, example] = make_default_example(
            new_db,
            default_example_config(
                weight=0.5,
                active=True,
                result_value=result_value,
                factor_values=[factor1_values[1].value],
            ),
        ).unpack()

        values = example.get_values()
        assert len(values) == 1

        assert values[0].name == factor1_values[1].value.name


class TestValues:
    def config_wo_values(self, db: DataBase):
        result_value = make_default_result_value(db).result_value
        return default_example_config(
            weight=0.5, active=True, result_value=result_value, factor_values=[]
        )

    def test_get_none(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(
            new_db, self.config_wo_values(new_db)
        ).unpack()
        factor_data, values_data = make_default_factor_and_values(new_db)
        factor = values_data[0].value

        assert example.get_value(factor) == None

    def test_set_get(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(
            new_db, self.config_wo_values(new_db)
        ).unpack()
        factor_data, values_data = make_default_factor_and_values(new_db)
        factor = factor_data.factor
        value = values_data[0].value

        example.add_value(value)

        assert example.get_value(factor).name == value.name

    def test_override(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(
            new_db, self.config_wo_values(new_db)
        ).unpack()
        factor_data, values_data = make_default_factor_and_values(new_db)
        factor = factor_data.factor
        value1 = values_data[0].value
        value2 = values_data[1].value

        example.add_value(value1)
        example.add_value(value2)

        assert example.get_value(factor).name == value2.name

    def test_reset(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(
            new_db, self.config_wo_values(new_db)
        ).unpack()
        factor_data, values_data = make_default_factor_and_values(new_db)
        factor = factor_data.factor
        value = values_data[0].value

        example.add_value(value)
        example.remove_value(factor)

        assert example.get_value(factor) == None


class TestRemoveValues:
    def test_remove(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(new_db).unpack()

        example.remove_values()

        all = example.get_values()
        assert all == []

    def test_remove_empty(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(new_db).unpack()

        example.remove_values()


class TestEqual:
    def test_equal(self, new_db: DataBase):
        examples_data = make_default_examples(new_db)
        example1 = examples_data[0].example
        example2 = examples_data[1].example

        assert example1 == example1
        assert example1 != example2
        assert example1 != 5

    def test_get_equal(self, new_db: DataBase):
        examples_data = make_default_examples(new_db)
        example1 = examples_data[0].example
        example2 = examples_data[1].example

        assert ExampleController.get(new_db, example1.id) == example1
        assert ExampleController.get(new_db, example1.id) != example2

        assert ExampleController.get(new_db, example1.id) == ExampleController.get(
            new_db, example1.id
        )

    def test_get_by_position_equal(self, new_db: DataBase):
        examples_data = make_default_examples(new_db)
        example1 = examples_data[0].example
        example2 = examples_data[1].example

        assert ExampleController.get_by_position(new_db, example1.position) == example1
        assert ExampleController.get_by_position(new_db, example1.position) != example2
        assert ExampleController.get_by_position(
            new_db, example1.position
        ) == ExampleController.get_by_position(new_db, example1.position)


class TestAllCount:
    def test_get(self, new_db: DataBase):
        examples_data = make_default_examples(new_db)

        count = ExampleController.get_count(new_db)

        assert count == len(examples_data)

    def test_get_count_empty(self, new_db: DataBase):
        count = ExampleController.get_count(new_db)

        assert count == 0


class TestValueCount:
    def test_get(self, new_db: DataBase):
        [weight, res_value, active, factor_values, example] = make_default_example(new_db).unpack()
        count = example.get_values_count()

        assert count == len(factor_values)

    def test_get_empty(self, new_db: DataBase):
        [value_name, value_text, value] = make_default_result_value(new_db).unpack()
        weight = 0.5

        example = ExampleController.make(new_db, weight, value)

        count = example.get_values_count()

        assert count == 0

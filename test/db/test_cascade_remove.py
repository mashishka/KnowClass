from test.db.db_fixtures import make_default_examples, make_default_factor_and_values

from data_utils.controllers.ExampleController import ExampleController
from data_utils.controllers.FactorController import FactorController
from data_utils.controllers.ResultController import ResultController
from data_utils.controllers.ValueController import ValueController
from data_utils.core import DataBase


class TestCascadeFactor:
    def test_remove_values(self, new_db: DataBase):
        [factor_data, values_data] = make_default_factor_and_values(new_db)
        factor = factor_data.factor

        FactorController.remove(new_db, factor.name)

        assert ValueController.get_all(new_db) == []

    def test_remove_examples(self, new_db: DataBase):
        examples_data = make_default_examples(new_db)
        factors = FactorController.get_all(new_db)
        factor = factors[0]
        name = factor.name

        FactorController.remove(new_db, name)
        examples = ExampleController.get_all(new_db)
        values: list[ValueController] = []
        for example in examples:
            values.extend(example.get_values())

        assert name not in {value.factor.name for value in values}


class TestCascadeFactorValue:
    def test_remove_examples(self, new_db: DataBase):
        examples_data = make_default_examples(new_db)
        factors = FactorController.get_all(new_db)
        factor = factors[0]
        for value in factor.get_values():
            factor.remove_value(value.name)
        name = factor.name

        examples = ExampleController.get_all(new_db)
        values = [example.result_value.name for example in examples]

        assert name not in values


class TestCascadeResultValue:
    def test_remove_examples(self, new_db: DataBase):
        examples_data = make_default_examples(new_db)
        result_value = ResultController.get(new_db).get_values()
        value = result_value[0]
        name = value.name

        ResultController.get(new_db).remove_value(name)
        examples = ExampleController.get_all(new_db)
        values = [example.result_value.name for example in examples]

        assert name not in values

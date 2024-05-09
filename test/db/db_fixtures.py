from dataclasses import dataclass
from pathlib import Path

import pytest

from data_utils.controllers.ExampleController import ExampleController
from data_utils.controllers.FactorController import FactorController
from data_utils.controllers.ResultController import ResultController
from data_utils.controllers.ResultValueController import ResultValueController
from data_utils.controllers.ValueController import ValueController
from data_utils.core import DataBase


@pytest.fixture
def new_db(tmp_path: Path):
    db = DataBase.create(tmp_path / "database.db")
    return db


@dataclass
class default_factor:
    name: str
    text: str
    active: bool
    factor: FactorController

    def unpack(self):
        return self.name, self.text, self.active, self.factor


@dataclass
class default_factor_config:
    name: str
    text: str
    active: bool


def make_default_factor(db: DataBase, config: default_factor_config | None = None):
    if config is None:
        config = default_factor_config(name="factor1", text="text1", active=True)
    name = config.name
    text = config.text
    active = config.active

    factor = FactorController.make(db, name)
    factor.text = text
    factor.active = active
    return default_factor(name, text, active, factor)


def make_default_factors(
    db: DataBase,
    configs: list[default_factor_config | None] | None = None,
) -> list[default_factor]:
    if configs is None:
        configs = [
            default_factor_config(name="factor1", text="text1", active=True),
            default_factor_config(name="factor2", text="text2", active=True),
            default_factor_config(name="factor3", text="text3", active=True),
            default_factor_config(name="factor4", text="text4", active=True),
            default_factor_config(name="factor5", text="text5", active=True),
        ]

    return [make_default_factor(db, config) for config in configs]


@dataclass
class default_value:
    name: str
    text: str
    value: ValueController

    def unpack(self):
        return self.name, self.text, self.value


@dataclass
class default_value_config:
    name: str
    text: str


def make_default_value(
    factor: FactorController,
    config: default_value_config | None = None,
):
    if config is None:
        config = default_value_config(name="value1", text="text1")
    name = config.name
    text = config.text

    value = factor.make_value(name)
    value.text = text
    return default_value(name, text, value)


def make_default_values(
    factor: FactorController,
    configs: list[default_value_config | None] | None = None,
) -> list[default_value]:
    if configs is None:
        configs = [
            default_value_config(name="value1", text="text1"),
            default_value_config(name="value2", text="text2"),
            default_value_config(name="value3", text="text3"),
            default_value_config(name="value4", text="text4"),
            default_value_config(name="value5", text="text5"),
        ]

    return [make_default_value(factor, config) for config in configs]


def make_default_factor_and_values(
    db: DataBase,
    config: default_factor_config | None = None,
    value_configs: list[default_value_config | None] | None = None,
) -> tuple[default_factor, list[default_value]]:
    factor_data = make_default_factor(db, config)

    values = make_default_values(factor_data.factor, value_configs)
    return (factor_data, values)


def make_default_factors_and_values(
    db: DataBase,
    configs: list[default_factor_config | None] | None = None,
    value_configs: list[list[default_value_config | None] | None] | None = None,
) -> list[tuple[default_factor, list[default_value]]]:
    res: list[tuple[default_factor, list[default_value]]] = []

    factors = make_default_factors(db, configs)

    if value_configs is None:
        value_configs = [None] * len(factors)

    for factor_data, value_config in zip(factors, value_configs):
        values = make_default_values(factor_data.factor, value_config)
        res.append((factor_data, values))
    return res


@dataclass
class default_result_value:
    name: str
    text: str
    result_value: ResultValueController

    def unpack(self):
        return self.name, self.text, self.result_value


@dataclass
class default_result_value_config:
    name: str
    text: str


def make_default_result_value(
    db: DataBase,
    config: default_result_value_config | None = None,
) -> default_result_value:
    if config is None:
        config = default_result_value_config(name="result_value1", text="text1")
    name = config.name
    text = config.text

    value = ResultController.get(db).make_value(name)
    value.text = text
    return default_result_value(name, text, value)


def make_default_result_values(
    db: DataBase,
    configs: list[default_result_value_config | None] | None = None,
) -> list[default_result_value]:
    if configs is None:
        configs = [
            default_result_value_config(name="result_value1", text="text1"),
            default_result_value_config(name="result_value2", text="text2"),
            default_result_value_config(name="result_value3", text="text3"),
            default_result_value_config(name="result_value4", text="text4"),
            default_result_value_config(name="result_value5", text="text5"),
        ]

    return [make_default_result_value(db, config) for config in configs]


@dataclass
class default_example:
    weight: float
    result_value: ResultValueController
    active: bool
    factor_values: list[ValueController]
    example: ExampleController

    def unpack(self):
        return self.weight, self.result_value, self.active, self.factor_values, self.example


@dataclass
class default_example_config:
    weight: float
    active: bool
    result_value: ResultValueController
    factor_values: list[ValueController]


def make_default_example(
    db: DataBase,
    config: default_example_config | None = None,
) -> default_example:
    if config is None:
        res_value = make_default_result_value(db).result_value
        factor1 = make_default_factor(db).factor
        factor_value = make_default_value(factor1).value

        config = default_example_config(
            weight=0.1, result_value=res_value, active=True, factor_values=[factor_value]
        )
    weight = config.weight
    result_value = config.result_value
    active = config.active
    factor_values = config.factor_values

    example = ExampleController.make(db, weight, result_value)
    example.active = active

    for factor_value in factor_values:
        example.add_value(factor_value)

    return default_example(weight, result_value, active, factor_values, example)


def make_default_examples(
    db: DataBase,
    configs: list[default_example_config | None] | None = None,
) -> list[default_example]:
    if configs is None:
        factors_and_values = make_default_factors_and_values(db)
        result_values = make_default_result_values(db)
        f1_values = [data.value for data in factors_and_values[0][1]]
        f2_values = [data.value for data in factors_and_values[1][1]]
        f3_values = [data.value for data in factors_and_values[2][1]]
        f4_values = [data.value for data in factors_and_values[3][1]]
        f5_values = [data.value for data in factors_and_values[4][1]]

        configs = [
            default_example_config(
                weight=0.1,
                result_value=result_values[0].result_value,
                active=True,
                factor_values=f1_values,
            ),
            default_example_config(
                weight=0.2,
                result_value=result_values[1].result_value,
                active=True,
                factor_values=f2_values,
            ),
            default_example_config(
                weight=0.3,
                result_value=result_values[2].result_value,
                active=True,
                factor_values=f3_values,
            ),
            default_example_config(
                weight=0.4,
                result_value=result_values[3].result_value,
                active=True,
                factor_values=f4_values,
            ),
            default_example_config(
                weight=0.5,
                result_value=result_values[4].result_value,
                active=True,
                factor_values=f5_values,
            ),
        ]

    return [make_default_example(db, config) for config in configs]

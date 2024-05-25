from typing import TypeAlias

from data_utils.imp.tables import (
    AdditionalData,
    Example,
    ExampleFactorValue,
    Factor,
    ResultValue,
    Value,
)

GetByIdTables: TypeAlias = (
    Example | Factor | ResultValue | Value | ExampleFactorValue | AdditionalData
)
GetByPosTable: TypeAlias = Factor | ResultValue | Example

table_to_id_name: dict[type[GetByIdTables], str] = {
    Example: "example_id",
    Factor: "factor_id",
    ResultValue: "result_value_id",
    Value: "value_id",
    ExampleFactorValue: "example_factor_value_id",
    AdditionalData: "id",
}

table_to_position_name: dict[type[GetByPosTable], str] = {
    Example: "example_positions",
    Factor: "factor_positions",
    ResultValue: "result_value_positions",
}

from pathlib import Path

from data_utils.controllers.ExampleController import ExampleController
from data_utils.controllers.FactorController import FactorController
from data_utils.controllers.ResultController import ResultController
from data_utils.controllers.TreeController import TreeController
from data_utils.controllers.ValueController import ValueController
from data_utils.core import DataBase
from data_utils.ResultMethodType import ResultMethodType


def print_pos(db, count):
    for i in range(0, count):
        example = ExampleController.get_by_position(db, i)
        print(
            example.weight,
            example.result_value.name,
            {
                factor.name: example.get_value(factor).name if example.get_value(factor) else None
                for factor in FactorController.get_all(db)
            },
        )
    print()


# запуск
if __name__ == "__main__":
    db = DataBase.create(Path("test.db"))
    f1 = FactorController.make(db, "f1")
    f2 = FactorController.make(db, "f2")
    f3 = FactorController.make(db, "f3")

    f1v1 = f1.make_value("v1")
    f1v2 = f1.make_value("v2")

    f2v1 = f2.make_value("v1")

    rv1 = ResultController.get(db).make_value("rv1")
    rv2 = ResultController.get(db).make_value("rv2")
    rv3 = ResultController.get(db).make_value("rv3")

    print(ResultController.get(db).type)
    ResultController.get(db).type = ResultMethodType.confidence
    print(ResultController.get(db).type)

    example1 = ExampleController.make(db, 1.0, rv1)
    example2 = ExampleController.make(db, 2.0, rv2)
    example3 = ExampleController.make(db, 3.0, rv3)

    examples = [example1, example2, example3]

    print_pos(db, 3)
    example2.position = 0
    print_pos(db, 3)
    example1.position = 2
    print_pos(db, 3)
    example1.result_value = rv3
    print_pos(db, 3)

    example2.swap_position(example1)
    print_pos(db, 3)

    example1.add_value(f1v1)
    print_pos(db, 3)
    example1.add_value(f1v2)
    print_pos(db, 3)
    example1.add_value(f2v1)
    print_pos(db, 3)
    example2.add_value(f1v2)
    print_pos(db, 3)

    example2.remove_value(f1)
    print_pos(db, 3)

    example1.remove_values()
    print_pos(db, 3)

    print(example1 == example1)
    print(example1 == example2)
    print(example1 == example3)
    print(example2 == example1)
    print(example2 == example2)
    print(example2 == example3)
    print(example3 == example1)
    print(example3 == example2)
    print(example3 == example3)

    FactorController.remove_all(db)

    # print(ValueController.get_all(db))
    ResultController.get(db).remove_values()
    print(TreeController.get(db).data)
    TreeController.get(db).data = "kekw".encode()
    print(TreeController.get(db).data)
    # ExampleController.remove_all(db)

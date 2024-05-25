from functools import wraps
from typing import Any, Callable


# NOTE: Кеш (словарь) с группами
#       группа -> словарь по индексам
class SimpleGroupCache:
    def __init__(self):
        self._data = {}

    # проверка наличия значения
    def exists(self, group: str, index: Any) -> bool:
        group_data = self._group_data(group)
        return index in group_data

    # установка значения
    def set(self, group: str, index: Any, value: Any) -> None:
        group_data = self._group_data(group)
        group_data[index] = value

    # получение значения
    def get(self, group: str, index: Any) -> Any:
        group_data = self._group_data(group)
        return group_data[index]

    # удаление значений группы
    def invalidate_group(self, group: str) -> None:
        group_data = self._group_data(group)
        group_data.clear()

    # удаление всех значений
    def invalidate_all(self) -> None:
        self._data.clear()

    def _group_data(self, group: str) -> dict:
        try:
            return self._data[group]
        except KeyError:
            self._data[group] = {}
            return self._data[group]


# декоратор, который кеширует результат функции в cache
# ожидает индекс в аргументе cached_index
def cached(cache: SimpleGroupCache, group: str) -> Any:
    def decorator(f: Callable[[Any], Any]):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cached_index = kwargs.get("cached_index", None)
            if not cache.exists(group, cached_index):
                actual_value = f(*args, **kwargs)
                cache.set(group, cached_index, actual_value)
            return cache.get(group, cached_index)

        return wrapper

    return decorator

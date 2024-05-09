# базовый класс для всех ошибок в бд
class DataBaseError(Exception):
    pass


# схема загружаемой бд отличается
class LoadWrongScheme(DataBaseError):
    pass


# попытка изменить позицию на невалидное значение
class InvalidPosition(DataBaseError):
    pass

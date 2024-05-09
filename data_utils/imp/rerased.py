from functools import wraps

from sqlalchemy import exc

from data_utils.errors import DataBaseError


def reraised(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as ex:
            if isinstance(ex, DataBaseError):
                raise
            if isinstance(ex, exc.SQLAlchemyError):
                raise DataBaseError from ex
            raise

    return wrapper


def reraised_class(exclude: list | None = None):
    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)) and (not exclude or attr not in exclude):
                setattr(cls, attr, reraised(getattr(cls, attr)))
        return cls

    return decorate

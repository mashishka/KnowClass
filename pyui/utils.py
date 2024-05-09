import logging as log
from functools import wraps

from PyQt5.QtWidgets import *


# QMessageBox.critical при исключении в методе
def error_window(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        try:
            log.debug(f"{f}, {self}, {args}, {kwargs}")
            f(self, *args, **kwargs)
        except Exception as err:
            log.debug(f"error_window exception: {err}")
            QMessageBox.critical(self, "Внимание!", f"Возникла ошибка: {err}")

    return wrapper

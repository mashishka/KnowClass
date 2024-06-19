import logging as log
from functools import wraps

from PyQt5.QtWidgets import *


# Элемент отображения дерева, дополнительно хранит список примеров своего узла
class ExtendedTreeItem(QTreeWidgetItem):
    def __init__(self, examples: list[int], parent=None):
        super(ExtendedTreeItem, self).__init__(parent)
        self.node_examples = examples


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

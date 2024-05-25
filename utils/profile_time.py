from contextlib import contextmanager
from dataclasses import dataclass
import logging as log
from time import time


@dataclass
class Data:
    end: float
    s: float = 0.0
    count: int = 0


sumtime: dict[str, Data] = {}


@contextmanager
def logsum_time(id: str, interval: float):
    global sumtime
    if id not in sumtime:
        sumtime[id] = Data(end=time() + interval)
    s = time()
    try:
        yield
    finally:
        dt = time() - s
        data = sumtime[id]
        data.s += dt
        data.count += 1
        if time() >= data.end:
            log.debug(
                "%s: (%.4f) %s, %s -> %s ms",
                id,
                time() - data.end,
                data.s,
                data.count,
                (data.s / data.count) * 1000,
            )
            del sumtime[id]


@contextmanager
def logtime(msg: str):
    s = time()
    try:
        yield
    finally:
        log.debug("%s: %s", msg, time() - s)

from sqlalchemy import MetaData
from sqlalchemy.orm import Session

from data_utils.errors import LoadWrongScheme
from data_utils.imp.tables import AdditionalData


# NOTE: неполная проверка, только таблицы, столбцы и их имена
# raises errors if schemas differs
def assert_scheme(meta1: MetaData, meta2: MetaData):
    st1 = meta1.sorted_tables
    st2 = meta2.sorted_tables
    if len(st1) != len(st2):
        raise LoadWrongScheme("tables count")

    for t1, t2 in zip(st1, st2):
        if t1.name != t2.name:
            raise LoadWrongScheme("tables names")
        cs1 = sorted(t1.columns, key=lambda c: c.name)
        cs2 = sorted(t2.columns, key=lambda c: c.name)

        if len(cs1) != len(cs2):
            raise LoadWrongScheme("columns count")

        for c1, c2 in zip(cs1, cs2):
            if c1.name != c2.name:
                raise LoadWrongScheme("columns names")


# спец таблица с 1 значением
def assert_addition_data(session: Session):
    all = session.query(AdditionalData).all()
    if len(all) != 1:
        raise LoadWrongScheme("AdditionalData count")

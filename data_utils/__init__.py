from sqlite3 import Connection as SQLite3Connection

from sqlalchemy import Engine, event


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        pragmas = [
            "PRAGMA foreign_keys=ON;",
            "PRAGMA synchronous=OFF;",
            "PRAGMA temp_store = MEMORY;",
            "PRAGMA journal_mode=MEMORY;",
        ]
        for pragma in pragmas:
            cursor.execute(pragma)
        cursor.close()

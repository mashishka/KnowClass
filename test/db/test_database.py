from pathlib import Path

import pytest

from data_utils.core import DataBase


class TestCreate:
    def test_create(self, tmp_path: Path):
        DataBase.create(tmp_path / "database.db")

    def test_override(self, tmp_path: Path):
        db = DataBase.create(tmp_path / "database.db")
        db.close()
        DataBase.create(tmp_path / "database.db")


class TestLoad:
    def test_load(self, tmp_path: Path):
        db = DataBase.create(tmp_path / "database.db")
        db.close()
        DataBase.load(tmp_path / "database.db")


class TestPath:
    def test_get(self, tmp_path: Path):
        path = tmp_path / "database.db"
        db = DataBase.create(path)
        assert db.path == path.as_posix()

    def test_set_error(self, tmp_path: Path):
        path = tmp_path / "database.db"
        db = DataBase.create(path)

        with pytest.raises(AttributeError):
            db.path = "new_path"  # type: ignore

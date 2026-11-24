import os
import tempfile
from pathlib import Path

import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

# Configure the application engine before any test imports app.database.
_TEST_DATABASE_DIRECTORY = tempfile.TemporaryDirectory(prefix="comp3613-tests-")
_TEST_DATABASE_PATH = Path(_TEST_DATABASE_DIRECTORY.name) / "application-tests.db"
os.environ["DATABASE_URI"] = f"sqlite:///{_TEST_DATABASE_PATH.as_posix()}"

from app.config import clear_settings_cache

clear_settings_cache()

from app.database import engine as _test_engine

if Path(_test_engine.url.database).resolve() != _TEST_DATABASE_PATH.resolve():
    raise RuntimeError("Tests must use the isolated temporary SQLite database")

import app.models


@pytest.fixture(scope="session")
def isolated_test_database():
    SQLModel.metadata.create_all(_test_engine)
    yield _test_engine
    _test_engine.dispose()
    _TEST_DATABASE_DIRECTORY.cleanup()


@pytest.fixture
def test_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

import os
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.api.app import app

try:
    from app.db.session import get_db
except Exception: 
    get_db = None


def _build_test_engine():
    
    user = os.getenv("DB_USER", "eps_user")
    password = os.getenv("DB_PASSWORD", "eps_pass")
    host = os.getenv("DB_HOST", "db")
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "pool_db")

    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
    return create_engine(url, pool_pre_ping=True)


@pytest.fixture(scope="session")
def engine():
    return _build_test_engine()


@pytest.fixture(scope="function")
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(bind=connection, autoflush=False, autocommit=False)
    session = TestingSessionLocal()

    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    try:
        yield session
    finally:
        try:
            session.close()
        finally:
            try:
                if getattr(transaction, "is_active", False):
                    transaction.rollback()
            except Exception:
                pass
            connection.close()



@pytest.fixture(scope="function")
def client(db_session):
   
    if get_db is None:
        raise RuntimeError("Could not import get_db from app.db.session")

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()

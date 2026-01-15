import os
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from urllib.parse import urlencode

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
def anon_client(db_session):
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


@pytest.fixture(scope="function")
def auth_headers(anon_client):
    username = "test_admin"
    email = "test_admin@example.com"
    password = "Password123!"

    r = anon_client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    if r.status_code not in (201, 409):
        raise AssertionError(f"Unexpected register status {r.status_code}: {r.text}")

    form = urlencode({"username": username, "password": password})
    r2 = anon_client.post(
        "/api/v1/auth/token",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if r2.status_code != 200:
        raise AssertionError(f"Token failed {r2.status_code}: {r2.text}")

    token = r2.json().get("access_token")
    if not token:
        raise AssertionError(f"No access_token in response: {r2.text}")

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def client(anon_client, auth_headers):
    anon_client.headers.update(auth_headers)
    return anon_client

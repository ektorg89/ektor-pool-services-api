import os
import time
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_LOCAL_PATH = BASE_DIR / ".env.local"
ENV_PATH = BASE_DIR / ".env"

REQUIRED_VARS = ["DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"]

missing_before = [v for v in REQUIRED_VARS if not os.getenv(v)]
if missing_before:
    load_dotenv(dotenv_path=ENV_LOCAL_PATH if ENV_LOCAL_PATH.exists() else ENV_PATH, override=False)

missing_after = [v for v in REQUIRED_VARS if not os.getenv(v)]
if missing_after:
    raise RuntimeError(f"Missing required env vars: {', '.join(missing_after)}")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def _create_engine_with_retry(url: str, attempts: int = 10, delay_seconds: float = 1.0):
    last_err: Exception | None = None

    for i in range(1, attempts + 1):
        try:
            engine = create_engine(url, pool_pre_ping=True)
            
            with engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            return engine
        except OperationalError as e:
            last_err = e
            time.sleep(delay_seconds)

engine = _create_engine_with_retry(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

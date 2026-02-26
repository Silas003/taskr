from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv,find_dotenv

load_dotenv(find_dotenv())

DATABASE_URL = URL.create(
    drivername=os.environ.get("DB_DRIVER", "postgresql+psycopg2"),
    username=os.environ.get("DB_USER", "postgres"),
    password=os.environ.get("DB_PASS", "postgres"),
    host=os.environ.get("DB_HOST", "localhost"),
    port=int(os.environ.get("DB_PORT", 5432)),
    database=os.environ.get("DB_NAME", "taskr"),
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """Yield a database session and ensure it is closed after use."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
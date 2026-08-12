import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Default to local SQLite file if no DATABASE_URL is set in .env
DEFAULT_SQLITE_URL = "sqlite:///./securelens.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)

# SQLite URL compatibility fix for SQLAlchemy 2.0 (ensure it works with ///)
is_sqlite = DATABASE_URL.startswith("sqlite")

# Create engine options
engine_args = {}
if is_sqlite:
    # check_same_thread=False is required for SQLite in multi-threaded environments like FastAPI
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_args)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for database models
Base = declarative_base()


def get_db():
    """FastAPI Dependency to yield database sessions with auto-cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

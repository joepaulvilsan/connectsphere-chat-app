from sqlmodel import SQLModel, create_engine
from sqlmodel import Session
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:mysecretpassword@localhost:5433/connectsphere_db"
)

# Optimize database connection pool settings
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("DB_ECHO", "false").lower() == "true",  # Disable echo by default for performance
    pool_size=10,  # Maximum number of connections to keep in the pool
    max_overflow=20,  # Maximum overflow connections beyond pool_size
    pool_timeout=30,  # Timeout for getting connection from pool
    pool_recycle=3600,  # Recycle connections after 1 hour to prevent stale connections
    pool_pre_ping=True,  # Verify connections before using them
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()  
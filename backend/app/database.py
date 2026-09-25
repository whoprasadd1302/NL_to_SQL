import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DATABASE_URL

logger = logging.getLogger("mitraai")

Base = declarative_base()

def init_engine():
    """Initializes SQLAlchemy engine with PostgreSQL, fallback to SQLite if connection fails."""
    try:
        if DATABASE_URL.startswith("postgresql"):
            eng = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
            # Test connection
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"Connected to PostgreSQL database: {DATABASE_URL}")
            return eng
    except Exception as e:
        logger.warning(
            f"Could not connect to PostgreSQL ({e}). Falling back to SQLite local database."
        )

    # SQLite Fallback
    sqlite_url = "sqlite:///./mitraai.db"
    eng = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    logger.info(f"Connected to fallback SQLite database: {sqlite_url}")
    return eng


engine = init_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

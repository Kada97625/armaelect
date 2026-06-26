from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from app.config import get_settings
import os

settings = get_settings()

def get_database_url():
    """Détecte automatiquement SQLite (local) ou Cloud SQL (GCP)."""
    if settings.cloud_sql_connection_name:
        return (
            f"postgresql+pg8000://{settings.db_user}:{settings.db_password}@/"
            f"{settings.db_name}?unix_sock=/cloudsql/{settings.cloud_sql_connection_name}/.s.PGSQL.5432"
        )
    url = settings.database_url or os.getenv("DATABASE_URL")
    if url:
        return url
    return "sqlite:///./app.db"

def create_app_engine():
    url = get_database_url()
    connect_args = {"check_same_thread": False} if "sqlite" in url else {}
    poolclass = StaticPool if "sqlite" in url else None
    return create_engine(url, connect_args={} if "sqlite" not in url else connect_args, poolclass=poolclass, pool_pre_ping=True)

engine = create_app_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.config import get_database_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_database_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    # Entities are built from models right after each query, so keeping attributes
    # loaded after a commit avoids extra SELECTs.
    return sessionmaker(bind=get_engine(), expire_on_commit=False)

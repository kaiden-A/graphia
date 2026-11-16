from __future__ import annotations

import ssl
from collections.abc import Generator, Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import settings


def _build_engine():
    kwargs: dict = {"pool_pre_ping": True, "pool_recycle": 300}
    if settings.sqlalchemy_url.startswith("postgresql+pg8000://"):
        kwargs["connect_args"] = {}
        if settings.ssl_required:
            context = ssl.create_default_context()
            kwargs["connect_args"]["ssl_context"] = context
    elif settings.sqlalchemy_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        kwargs.pop("pool_pre_ping", None)
        kwargs.pop("pool_recycle", None)
    return create_engine(settings.sqlalchemy_url, **kwargs)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

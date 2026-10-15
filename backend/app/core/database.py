from collections.abc import Generator
import socket
from urllib.parse import urlsplit

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings


def get_connect_args(database_url: str) -> dict[str, str | int]:
    connect_args: dict[str, str | int] = {"connect_timeout": 10}
    parsed_url = urlsplit(database_url)
    if parsed_url.hostname:
        addresses = socket.getaddrinfo(
            parsed_url.hostname,
            parsed_url.port or 5432,
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
        )
        if addresses:
            connect_args["hostaddr"] = addresses[0][4][0]
    return connect_args


database_url = get_settings().database_url
engine = create_engine(
    database_url,
    pool_pre_ping=True,
    connect_args=get_connect_args(database_url),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

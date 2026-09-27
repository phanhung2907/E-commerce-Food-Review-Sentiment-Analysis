import os
import threading

import psycopg
from dotenv import load_dotenv


load_dotenv()

POSTGRES_HOST = os.getenv(
    "POSTGRES_HOST",
    "localhost",
)

POSTGRES_PORT = int(
    os.getenv(
        "POSTGRES_PORT",
        "5432",
    )
)

POSTGRES_DB = os.getenv(
    "POSTGRES_DB",
    "food_review",
)

POSTGRES_USER = os.getenv(
    "POSTGRES_USER",
    "postgres",
)

POSTGRES_PASSWORD = os.getenv(
    "POSTGRES_PASSWORD",
    "postgres",
)

_thread_local = threading.local()


def build_conninfo() -> str:
    return (
        f"host={POSTGRES_HOST} "
        f"port={POSTGRES_PORT} "
        f"dbname={POSTGRES_DB} "
        f"user={POSTGRES_USER} "
        f"password={POSTGRES_PASSWORD}"
    )


def create_postgres_connection():
    return psycopg.connect(
        build_conninfo(),
        autocommit=False,
    )


def get_thread_postgres_connection():
    """
    Reuse one PostgreSQL connection per worker thread.
    """
    conn = getattr(
        _thread_local,
        "connection",
        None,
    )

    if (
        conn is None
        or conn.closed
    ):
        conn = (
            create_postgres_connection()
        )
        _thread_local.connection = conn

    return conn

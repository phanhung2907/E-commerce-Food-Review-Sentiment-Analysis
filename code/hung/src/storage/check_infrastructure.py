import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1]

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(SRC_ROOT),
    )

from storage.minio_client import (  # noqa: E402
    MINIO_BUCKET,
    MINIO_ENDPOINT,
    create_minio_client,
    require_bucket,
)
from storage.postgres_client import (  # noqa: E402
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PORT,
    create_postgres_connection,
)


REQUIRED_TABLES = {
    "sources",
    "restaurants",
    "restaurant_opening_hours",
    "restaurant_cuisines",
    "reviewers",
    "reviews",
    "review_tags",
}


def check_minio():
    client = create_minio_client()
    require_bucket(client)

    print(
        f"[OK] MinIO "
        f"{MINIO_ENDPOINT} "
        f"bucket={MINIO_BUCKET}"
    )


def check_postgres():
    with (
        create_postgres_connection()
        as conn
    ):
        rows = conn.execute(
            """
            SELECT tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname = 'public'
            """
        ).fetchall()

        tables = {
            row[0]
            for row in rows
        }

        missing = (
            REQUIRED_TABLES
            - tables
        )

        if missing:
            raise RuntimeError(
                "PostgreSQL schema chưa được setup. "
                "Thiếu tables: "
                + ", ".join(
                    sorted(missing)
                )
                + ". Chạy init_postgres.py "
                "một lần trước pipeline."
            )

        source = conn.execute(
            """
            SELECT source_code
            FROM sources
            WHERE source_code = 'foody'
            """
        ).fetchone()

        if source is None:
            raise RuntimeError(
                "Table sources chưa có "
                "source_code='foody'. "
                "Chạy init_postgres.py."
            )

    print(
        f"[OK] PostgreSQL "
        f"{POSTGRES_HOST}:"
        f"{POSTGRES_PORT}/"
        f"{POSTGRES_DB}"
    )


def main():
    try:
        check_minio()
        check_postgres()

    except Exception as e:
        print(
            f"[ERROR] Infrastructure "
            f"check failed: {e}"
        )
        raise SystemExit(1)

    print(
        "[OK] Infrastructure ready."
    )


if __name__ == "__main__":
    main()

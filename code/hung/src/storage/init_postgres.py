from pathlib import Path

from postgres_client import (
    create_postgres_connection,
)


SCHEMA_FILE = (
    Path(__file__)
    .with_name(
        "schema_3nf.sql"
    )
)


def main():
    sql = SCHEMA_FILE.read_text(
        encoding="utf-8"
    )

    with (
        create_postgres_connection()
        as conn
    ):
        with conn.cursor() as cur:
            cur.execute(sql)

        conn.commit()

    print(
        "PostgreSQL 3NF schema "
        "initialized successfully."
    )


if __name__ == "__main__":
    main()

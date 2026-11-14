"""Export PostgreSQL base tables from one consistent read-only snapshot."""
import argparse
import json
import tempfile
from pathlib import Path

import pipeline  # Adds the repo's src directory for storage imports.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("database-merge-data"))
    parser.add_argument("--schema", default="public")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")

    from psycopg import sql
    from storage.postgres_client import create_postgres_connection

    counts = {}
    with tempfile.TemporaryDirectory(prefix=".csv-export-", dir=output.parent) as staging:
        staged_output = Path(staging) / output.name
        staged_output.mkdir()
        with create_postgres_connection() as conn:
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            tables = conn.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (args.schema,)).fetchall()
            if not tables:
                raise ValueError(f"No base tables found in {args.schema}")
            for (table,) in tables:
                filename = f"{table}.csv"
                if any(character in filename for character in '<>:"/\\|?*'):
                    raise ValueError(f"Table name cannot be used as a CSV filename: {table}")
                relation = sql.Identifier(args.schema, table)
                with (staged_output / filename).open("wb") as file, conn.cursor() as cur:
                    with cur.copy(sql.SQL("COPY {} TO STDOUT WITH (FORMAT CSV, HEADER, ENCODING 'UTF8')").format(relation)) as copy:
                        for block in copy:
                            file.write(block)
                counts[table] = conn.execute(sql.SQL("SELECT count(*) FROM {}").format(relation)).fetchone()[0]
        staged_output.rename(output)
    print(json.dumps({"output": str(output), "rows": counts}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

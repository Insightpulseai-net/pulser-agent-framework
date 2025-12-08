# scripts/migrate.py
"""
Simple migration runner that:
- Ensures `schema_migrations` exists
- Sorts `migrations/*.sql`
- Applies any migration not yet recorded
"""
import argparse
import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import DictCursor


def ensure_schema_migrations(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version    text PRIMARY KEY,
            applied_at timestamptz NOT NULL DEFAULT now()
        );
        """
    )


def get_applied_versions(cur):
    cur.execute("SELECT version FROM schema_migrations;")
    return {row["version"] for row in cur.fetchall()}


def apply_migration(cur, path: Path):
    version = path.stem  # e.g. "0001_init"
    with path.open("r", encoding="utf-8") as f:
        sql = f.read()
    if not sql.strip():
        print(f"[SKIP] {version}: empty migration")
        return

    print(f"[APPLY] {version} from {path}")
    cur.execute(sql)
    cur.execute(
        "INSERT INTO schema_migrations (version) VALUES (%s) ON CONFLICT DO NOTHING;",
        (version,),
    )


def run_migrations(dsn: str, migrations_dir: str = "migrations"):
    migration_paths = sorted(
        Path(migrations_dir).glob("*.sql"), key=lambda p: p.name
    )
    if not migration_paths:
        print(f"No migrations found in {migrations_dir}/, nothing to do.")
        return

    conn = psycopg2.connect(dsn)
    conn.autocommit = False

    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            ensure_schema_migrations(cur)
            applied = get_applied_versions(cur)

            for path in migration_paths:
                version = path.stem
                if version in applied:
                    print(f"[OK] {version} already applied, skipping.")
                    continue
                apply_migration(cur, path)

        conn.commit()
        print("All migrations applied successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}", file=sys.stderr)
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Apply SQL migrations.")
    parser.add_argument(
        "--dsn",
        default=os.getenv("DB_URL") or os.getenv("DATABASE_URL"),
        help="Postgres DSN, e.g. postgres://user:pass@host:5432/dbname",
    )
    parser.add_argument(
        "--migrations-dir",
        default="migrations",
        help="Directory containing *.sql migrations",
    )

    args = parser.parse_args()

    if not args.dsn:
        print("Error: --dsn or DB_URL/DATABASE_URL env is required.", file=sys.stderr)
        sys.exit(1)

    run_migrations(args.dsn, migrations_dir=args.migrations_dir)


if __name__ == "__main__":
    main()

# scripts/seed_demo_data.py
"""
Minimal demo seeding into the `tenants` + `workspaces` tables.
"""
import argparse
import os
import sys

import psycopg2
from psycopg2.extras import DictCursor


def seed(dsn: str):
    conn = psycopg2.connect(dsn)
    conn.autocommit = False

    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # Check if any tenants already exist
            cur.execute("SELECT COUNT(*) AS c FROM tenants;")
            count = cur.fetchone()["c"]
            if count > 0:
                print("Tenants already exist, skipping demo seed.")
                conn.commit()
                return

            # Insert one demo tenant + workspace
            cur.execute(
                """
                INSERT INTO tenants (slug, name)
                VALUES (%s, %s)
                RETURNING id;
                """,
                ("demo-tenant", "Demo Tenant"),
            )
            tenant_id = cur.fetchone()["id"]

            cur.execute(
                """
                INSERT INTO workspaces (tenant_id, slug, name)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (tenant_id, "default", "Default Workspace"),
            )
            workspace_id = cur.fetchone()["id"]

            print(f"Seeded demo tenant={tenant_id}, workspace={workspace_id}")
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Seeding failed: {e}", file=sys.stderr)
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Seed demo data into DB.")
    parser.add_argument(
        "--dsn",
        default=os.getenv("DB_URL") or os.getenv("DATABASE_URL"),
        help="Postgres DSN, e.g. postgres://user:pass@host:5432/dbname",
    )
    args = parser.parse_args()

    if not args.dsn:
        print("Error: --dsn or DB_URL/DATABASE_URL env is required.", file=sys.stderr)
        sys.exit(1)

    seed(args.dsn)


if __name__ == "__main__":
    main()

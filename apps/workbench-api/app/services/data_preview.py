"""
Data Preview Service
====================
Preview data from catalog entries.
"""

from typing import Any, List

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.database import async_session


async def get_preview(entry, limit: int = 100) -> dict:
    """
    Get a preview of data from a catalog entry.

    Args:
        entry: CatalogEntry object with connection_id, schema_name, name
        limit: Maximum number of rows to return

    Returns:
        dict with columns, rows, row_count, truncated
    """
    from app.models.connection import Connection

    async with async_session() as db:
        result = await db.execute(
            select(Connection).where(Connection.id == entry.connection_id)
        )
        connection = result.scalar_one_or_none()

    if not connection:
        return {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "truncated": False,
        }

    conn_type = connection.type.lower()
    config = connection.config or {}

    if conn_type in ("postgresql", "postgres"):
        return await _preview_postgresql(entry, config, limit)
    elif conn_type == "mysql":
        return await _preview_mysql(entry, config, limit)
    elif conn_type == "duckdb":
        return await _preview_duckdb(entry, config, limit)
    else:
        return {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "truncated": False,
        }


async def _preview_postgresql(entry, config: dict, limit: int) -> dict:
    """Preview data from a PostgreSQL table or view."""
    host = config.get("host", "localhost")
    port = config.get("port", 5432)
    database = config.get("database", "postgres")
    user = config.get("user", "postgres")
    password = config.get("password", "")

    dsn = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"

    table_ref = _build_table_ref(entry.schema_name, entry.name)

    try:
        engine = create_async_engine(dsn, echo=False)
        async with engine.connect() as conn:
            count_query = text(f"SELECT COUNT(*) FROM {table_ref}")
            count_result = await conn.execute(count_query)
            total_count = count_result.scalar() or 0

            data_query = text(f"SELECT * FROM {table_ref} LIMIT :limit")
            result = await conn.execute(data_query, {"limit": limit + 1})

            rows_raw = result.fetchall()
            columns = list(result.keys())

            truncated = len(rows_raw) > limit
            rows = [list(_serialize_row(row)) for row in rows_raw[:limit]]

        await engine.dispose()

        return {
            "columns": columns,
            "rows": rows,
            "row_count": total_count,
            "truncated": truncated,
        }
    except Exception as e:
        return {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "truncated": False,
        }


async def _preview_mysql(entry, config: dict, limit: int) -> dict:
    """Preview data from a MySQL table or view."""
    host = config.get("host", "localhost")
    port = config.get("port", 3306)
    database = config.get("database", "mysql")
    user = config.get("user", "root")
    password = config.get("password", "")

    dsn = f"mysql+aiomysql://{user}:{password}@{host}:{port}/{database}"

    table_ref = _build_table_ref(entry.schema_name, entry.name)

    try:
        engine = create_async_engine(dsn, echo=False)
        async with engine.connect() as conn:
            count_query = text(f"SELECT COUNT(*) FROM {table_ref}")
            count_result = await conn.execute(count_query)
            total_count = count_result.scalar() or 0

            data_query = text(f"SELECT * FROM {table_ref} LIMIT :limit")
            result = await conn.execute(data_query, {"limit": limit + 1})

            rows_raw = result.fetchall()
            columns = list(result.keys())

            truncated = len(rows_raw) > limit
            rows = [list(_serialize_row(row)) for row in rows_raw[:limit]]

        await engine.dispose()

        return {
            "columns": columns,
            "rows": rows,
            "row_count": total_count,
            "truncated": truncated,
        }
    except Exception:
        return {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "truncated": False,
        }


async def _preview_duckdb(entry, config: dict, limit: int) -> dict:
    """Preview data from a DuckDB database."""
    import duckdb

    db_path = config.get("path", ":memory:")
    table_ref = _build_table_ref(entry.schema_name, entry.name)

    try:
        conn = duckdb.connect(db_path, read_only=True)

        count_result = conn.execute(f"SELECT COUNT(*) FROM {table_ref}").fetchone()
        total_count = count_result[0] if count_result else 0

        result = conn.execute(f"SELECT * FROM {table_ref} LIMIT {limit + 1}")
        columns = [desc[0] for desc in result.description]
        rows_raw = result.fetchall()

        truncated = len(rows_raw) > limit
        rows = [list(_serialize_row(row)) for row in rows_raw[:limit]]

        conn.close()

        return {
            "columns": columns,
            "rows": rows,
            "row_count": total_count,
            "truncated": truncated,
        }
    except Exception:
        return {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "truncated": False,
        }


def _build_table_ref(schema_name: str | None, table_name: str) -> str:
    """Build a quoted table reference."""
    if schema_name:
        return f'"{schema_name}"."{table_name}"'
    return f'"{table_name}"'


def _serialize_row(row) -> List[Any]:
    """Serialize a row to JSON-compatible values."""
    result = []
    for val in row:
        if val is None:
            result.append(None)
        elif isinstance(val, (int, float, str, bool)):
            result.append(val)
        elif isinstance(val, bytes):
            result.append(f"<binary:{len(val)} bytes>")
        elif hasattr(val, "isoformat"):
            result.append(val.isoformat())
        else:
            result.append(str(val))
    return result

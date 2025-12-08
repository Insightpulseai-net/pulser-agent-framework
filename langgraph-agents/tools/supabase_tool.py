"""
Supabase Tool - Query Supabase PostgreSQL from agents.
"""

import logging
from typing import Dict, List, Any, Optional
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupabaseTool:
    """Execute SQL queries against Supabase."""

    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)
        logger.info(f"Initialized Supabase client: {url}")

    async def execute_sql(self, sql: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query via Supabase RPC.

        Args:
            sql: SQL query to execute

        Returns:
            Query results as list of dicts
        """
        try:
            # Use Supabase RPC function to execute arbitrary SQL
            response = self.client.rpc("execute_sql", {"sql": sql}).execute()
            return response.data

        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            raise

    async def query_table(
        self,
        table: str,
        select: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query a table with filters.

        Args:
            table: Table name (e.g., "gold.finance_expenses")
            select: Columns to select
            filters: Filter conditions
            limit: Max results

        Returns:
            Query results
        """
        try:
            query = self.client.table(table).select(select).limit(limit)

            # Apply filters
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            response = query.execute()
            return response.data

        except Exception as e:
            logger.error(f"Table query failed: {e}")
            raise

    async def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a row into a table."""
        try:
            response = self.client.table(table).insert(data).execute()
            return response.data[0] if response.data else {}

        except Exception as e:
            logger.error(f"Insert failed: {e}")
            raise

    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Update rows in a table."""
        try:
            query = self.client.table(table).update(data)

            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)

            response = query.execute()
            return response.data

        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise

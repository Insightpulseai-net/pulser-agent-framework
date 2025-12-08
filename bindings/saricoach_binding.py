"""
SariCoach Agent Binding - Bind SariCoach agent to Scout gold tables.

Gold tables:
- gold.finance_expenses
- gold.finance_vendors
- gold.scout_transactions

Context generation for agent prompts.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TableContext:
    """Context information for a gold table."""
    schema: str
    table: str
    description: str
    columns: List[Dict[str, str]]
    sample_queries: List[str]
    business_rules: List[str]


class SariCoachBinding:
    """Bind SariCoach agent to Scout gold tables."""

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.gold_tables = self._define_gold_tables()

    def _define_gold_tables(self) -> Dict[str, TableContext]:
        """Define gold table contexts for SariCoach."""
        return {
            "finance_expenses": TableContext(
                schema="gold",
                table="finance_expenses",
                description="Aggregated expense records with vendor, category, and approval status",
                columns=[
                    {"name": "id", "type": "uuid", "description": "Unique expense ID"},
                    {"name": "vendor", "type": "text", "description": "Vendor name"},
                    {"name": "amount", "type": "numeric", "description": "Expense amount (PHP)"},
                    {"name": "category", "type": "text", "description": "Expense category"},
                    {"name": "date", "type": "date", "description": "Expense date"},
                    {"name": "status", "type": "text", "description": "Approval status (pending, approved, rejected)"},
                    {"name": "submitted_by", "type": "uuid", "description": "User who submitted"},
                    {"name": "approved_by", "type": "uuid", "description": "User who approved"},
                    {"name": "created_at", "type": "timestamp", "description": "Record creation time"}
                ],
                sample_queries=[
                    "SELECT vendor, SUM(amount) as total FROM gold.finance_expenses WHERE status = 'approved' GROUP BY vendor ORDER BY total DESC LIMIT 10",
                    "SELECT category, COUNT(*) as count FROM gold.finance_expenses WHERE date >= CURRENT_DATE - INTERVAL '30 days' GROUP BY category",
                    "SELECT * FROM gold.finance_expenses WHERE amount > 5000 AND status = 'pending'"
                ],
                business_rules=[
                    "Only 'approved' expenses are included in financial reports",
                    "Expenses over 10,000 PHP require director approval",
                    "Entertainment expenses are capped at 500 PHP per transaction"
                ]
            ),
            "finance_vendors": TableContext(
                schema="gold",
                table="finance_vendors",
                description="Vendor master data with contact information and payment terms",
                columns=[
                    {"name": "id", "type": "uuid", "description": "Unique vendor ID"},
                    {"name": "name", "type": "text", "description": "Vendor name"},
                    {"name": "category", "type": "text", "description": "Vendor category"},
                    {"name": "email", "type": "text", "description": "Contact email"},
                    {"name": "phone", "type": "text", "description": "Contact phone"},
                    {"name": "payment_terms", "type": "text", "description": "Payment terms (e.g., NET30)"},
                    {"name": "total_expenses_ytd", "type": "numeric", "description": "Total expenses year-to-date"},
                    {"name": "created_at", "type": "timestamp", "description": "Record creation time"}
                ],
                sample_queries=[
                    "SELECT * FROM gold.finance_vendors WHERE category = 'Transportation' ORDER BY total_expenses_ytd DESC",
                    "SELECT name, total_expenses_ytd FROM gold.finance_vendors WHERE total_expenses_ytd > 50000"
                ],
                business_rules=[
                    "Vendor names must be unique",
                    "Payment terms default to NET30 if not specified"
                ]
            ),
            "scout_transactions": TableContext(
                schema="gold",
                table="scout_transactions",
                description="Scout transaction data with brand, product, and agency information",
                columns=[
                    {"name": "id", "type": "uuid", "description": "Unique transaction ID"},
                    {"name": "brand", "type": "text", "description": "Brand name"},
                    {"name": "product", "type": "text", "description": "Product name"},
                    {"name": "agency", "type": "text", "description": "Agency name"},
                    {"name": "amount", "type": "numeric", "description": "Transaction amount"},
                    {"name": "category", "type": "text", "description": "Transaction category"},
                    {"name": "date", "type": "date", "description": "Transaction date"},
                    {"name": "created_at", "type": "timestamp", "description": "Record creation time"}
                ],
                sample_queries=[
                    "SELECT brand, SUM(amount) as total FROM gold.scout_transactions WHERE date >= CURRENT_DATE - INTERVAL '90 days' GROUP BY brand",
                    "SELECT agency, COUNT(*) as transaction_count FROM gold.scout_transactions GROUP BY agency ORDER BY transaction_count DESC"
                ],
                business_rules=[
                    "All transactions must have a valid brand and product",
                    "Agency field is optional for direct client transactions"
                ]
            )
        }

    def generate_agent_context(
        self,
        table_names: Optional[List[str]] = None,
        include_sample_data: bool = False
    ) -> str:
        """
        Generate context for SariCoach agent prompt.

        Args:
            table_names: List of table names to include (None = all)
            include_sample_data: Include sample rows from tables

        Returns:
            Formatted context string for agent prompt
        """
        tables_to_include = table_names or list(self.gold_tables.keys())

        context_parts = ["# Scout Gold Tables Context\n\n"]

        for table_name in tables_to_include:
            if table_name not in self.gold_tables:
                logger.warning(f"Unknown table: {table_name}")
                continue

            table_ctx = self.gold_tables[table_name]

            context_parts.append(f"## {table_ctx.schema}.{table_ctx.table}\n\n")
            context_parts.append(f"**Description**: {table_ctx.description}\n\n")

            # Columns
            context_parts.append("**Columns**:\n")
            for col in table_ctx.columns:
                context_parts.append(f"- `{col['name']}` ({col['type']}): {col['description']}\n")
            context_parts.append("\n")

            # Sample queries
            context_parts.append("**Sample Queries**:\n")
            for i, query in enumerate(table_ctx.sample_queries, 1):
                context_parts.append(f"{i}. ```sql\n{query}\n```\n\n")

            # Business rules
            context_parts.append("**Business Rules**:\n")
            for rule in table_ctx.business_rules:
                context_parts.append(f"- {rule}\n")
            context_parts.append("\n")

            # Sample data (optional)
            if include_sample_data:
                sample_data = self._fetch_sample_data(table_ctx.schema, table_ctx.table)
                if sample_data:
                    context_parts.append("**Sample Data** (first 3 rows):\n```json\n")
                    import json
                    context_parts.append(json.dumps(sample_data, indent=2))
                    context_parts.append("\n```\n\n")

        return "".join(context_parts)

    def _fetch_sample_data(self, schema: str, table: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Fetch sample data from a table."""
        try:
            response = self.supabase.table(f"{schema}.{table}").select("*").limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to fetch sample data from {schema}.{table}: {e}")
            return []

    def get_table_schema(self, table_name: str) -> Optional[TableContext]:
        """Get schema for a specific table."""
        return self.gold_tables.get(table_name)

    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validate SQL query against gold table schemas.

        Args:
            query: SQL query to validate

        Returns:
            Validation result
        """
        # Simple validation - check if query references valid tables
        query_lower = query.lower()

        referenced_tables = []
        for table_name in self.gold_tables.keys():
            if f"gold.{table_name}" in query_lower:
                referenced_tables.append(table_name)

        # Check for SELECT-only (no INSERT/UPDATE/DELETE)
        is_readonly = all(
            keyword not in query_lower
            for keyword in ["insert", "update", "delete", "drop", "alter", "truncate"]
        )

        return {
            "is_valid": is_readonly and len(referenced_tables) > 0,
            "is_readonly": is_readonly,
            "referenced_tables": referenced_tables,
            "warnings": [] if is_readonly else ["Query contains write operations"]
        }


# Example usage
if __name__ == "__main__":
    from supabase import create_client
    import os

    supabase = create_client(
        os.getenv("SUPABASE_URL", "https://xkxyvboeubffxxbebsll.supabase.co"),
        os.getenv("SUPABASE_KEY", "your-key")
    )

    binding = SariCoachBinding(supabase)

    # Generate context for all tables
    context = binding.generate_agent_context(include_sample_data=False)
    print(context)

    # Validate query
    query = "SELECT vendor, SUM(amount) FROM gold.finance_expenses GROUP BY vendor"
    validation = binding.validate_query(query)
    print(f"\nQuery validation: {validation}")

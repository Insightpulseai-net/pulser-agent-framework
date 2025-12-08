"""
Odoo Tool - XML-RPC operations from agents.
"""

import logging
from typing import Dict, List, Any, Optional
import xmlrpc.client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OdooTool:
    """Execute Odoo XML-RPC operations."""

    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Odoo."""
        try:
            common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            self.uid = common.authenticate(self.db, self.username, self.password, {})

            if not self.uid:
                raise ValueError("Odoo authentication failed")

            logger.info(f"Authenticated with Odoo: UID={self.uid}")

        except Exception as e:
            logger.error(f"Odoo authentication failed: {e}")
            raise

    def _get_models_proxy(self):
        """Get models proxy."""
        return xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    async def get_expense_categories(self) -> List[Dict[str, Any]]:
        """Get list of expense categories from Odoo."""
        try:
            models = self._get_models_proxy()
            categories = models.execute_kw(
                self.db, self.uid, self.password,
                'hr.expense.category', 'search_read',
                [[]],
                {'fields': ['name', 'code']}
            )
            return categories

        except Exception as e:
            logger.error(f"Failed to fetch expense categories: {e}")
            raise

    async def create_expense(self, expense_data: Dict[str, Any]) -> int:
        """
        Create expense record in Odoo.

        Args:
            expense_data: Expense data

        Returns:
            Expense ID
        """
        try:
            models = self._get_models_proxy()

            # Map fields to Odoo model
            odoo_data = {
                'name': f"Expense - {expense_data['vendor']}",
                'product_id': self._get_product_id(expense_data['category']),
                'unit_amount': expense_data['amount'],
                'date': expense_data['date'],
                'employee_id': self._get_employee_id(expense_data['submitted_by']),
                'state': expense_data.get('status', 'draft')
            }

            expense_id = models.execute_kw(
                self.db, self.uid, self.password,
                'hr.expense', 'create',
                [odoo_data]
            )

            logger.info(f"Created expense in Odoo: ID={expense_id}")
            return expense_id

        except Exception as e:
            logger.error(f"Failed to create expense: {e}")
            raise

    def _get_product_id(self, category: str) -> int:
        """Get product ID for a category."""
        # TODO: Implement proper product lookup
        return 1  # Default product

    def _get_employee_id(self, user_id: str) -> int:
        """Get employee ID for a user."""
        # TODO: Implement proper employee lookup
        return 1  # Default employee

    async def generate_bir_form(
        self,
        form_type: str,
        period: str,
        employee_id: str
    ) -> Dict[str, Any]:
        """
        Generate BIR form (1601-C, 2550Q, etc.).

        Args:
            form_type: BIR form type
            period: Period (YYYY-MM or YYYY-Q1)
            employee_id: Employee identifier

        Returns:
            Generated form data
        """
        try:
            models = self._get_models_proxy()

            # Call Odoo RPC method for BIR form generation
            form_data = models.execute_kw(
                self.db, self.uid, self.password,
                'ipai.finance.bir_schedule', 'generate_form',
                [form_type, period, employee_id]
            )

            logger.info(f"Generated BIR form: {form_type} for period {period}")
            return form_data

        except Exception as e:
            logger.error(f"Failed to generate BIR form: {e}")
            raise

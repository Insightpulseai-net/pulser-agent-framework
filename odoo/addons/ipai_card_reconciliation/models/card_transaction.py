# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class CardTransaction(models.Model):
    """Individual card transaction for reconciliation."""

    _name = "ipai.card.transaction"
    _description = "Card Transaction"
    _order = "transaction_date desc, id desc"

    statement_id = fields.Many2one(
        "ipai.card.statement",
        string="Statement",
        required=True,
        ondelete="cascade",
    )
    card_holder_id = fields.Many2one(
        related="statement_id.card_holder_id",
        store=True,
    )
    company_id = fields.Many2one(
        related="statement_id.company_id",
        store=True,
    )

    # Transaction details
    transaction_date = fields.Date(
        string="Transaction Date",
        required=True,
    )
    posting_date = fields.Date(string="Posting Date")
    reference = fields.Char(string="Reference/Auth Code")

    merchant_name = fields.Char(string="Merchant Name", required=True)
    merchant_category = fields.Char(string="Merchant Category")
    merchant_location = fields.Char(string="Location")

    description = fields.Char(string="Description")

    # Amount
    currency_id = fields.Many2one(
        related="statement_id.currency_id",
    )
    amount = fields.Monetary(
        string="Amount",
        currency_field="currency_id",
        required=True,
    )
    original_currency_id = fields.Many2one(
        "res.currency",
        string="Original Currency",
    )
    original_amount = fields.Monetary(
        string="Original Amount",
        currency_field="original_currency_id",
    )

    # Categorization
    expense_category_id = fields.Many2one(
        "product.product",
        string="Expense Category",
        domain=[("can_be_expensed", "=", True)],
    )
    suggested_category_id = fields.Many2one(
        "product.product",
        string="AI Suggested Category",
        domain=[("can_be_expensed", "=", True)],
    )
    category_confidence = fields.Float(string="Category Confidence")

    # Matching
    match_status = fields.Selection(
        [
            ("unmatched", "Unmatched"),
            ("matched", "Matched"),
            ("exception", "Exception"),
            ("ignored", "Ignored"),
        ],
        string="Match Status",
        default="unmatched",
    )
    expense_id = fields.Many2one(
        "hr.expense",
        string="Matched Expense",
    )
    receipt_attachment_id = fields.Many2one(
        "ir.attachment",
        string="Receipt",
    )

    # Flags
    is_duplicate = fields.Boolean(string="Potential Duplicate")
    is_suspicious = fields.Boolean(string="Suspicious Transaction")
    flag_reason = fields.Char(string="Flag Reason")

    notes = fields.Text(string="Notes")

    def action_auto_match(self):
        """Try to automatically match to an expense."""
        self.ensure_one()
        Expense = self.env["hr.expense"]

        # Search for matching expenses
        domain = [
            ("employee_id", "=", self.card_holder_id.id),
            ("expense_type", "=", "corporate_card"),
            ("total_amount", "=", self.amount),
            ("date", ">=", self.transaction_date),
        ]

        # Try exact match first
        match = Expense.search(domain, limit=1)

        if match:
            self.write({
                "match_status": "matched",
                "expense_id": match.id,
            })
            return True

        # Try fuzzy match on merchant name
        if self.merchant_name:
            domain_fuzzy = [
                ("employee_id", "=", self.card_holder_id.id),
                ("expense_type", "=", "corporate_card"),
                ("vendor_name", "ilike", self.merchant_name[:10]),
            ]
            match = Expense.search(domain_fuzzy, limit=1)
            if match and abs(match.total_amount - self.amount) < 10:
                self.write({
                    "match_status": "matched",
                    "expense_id": match.id,
                })
                return True

        return False

    def action_create_expense(self):
        """Create an expense from this transaction."""
        self.ensure_one()
        Expense = self.env["hr.expense"]

        vals = {
            "name": f"{self.merchant_name} - {self.description or self.transaction_date}",
            "employee_id": self.card_holder_id.id,
            "product_id": self.expense_category_id.id or self.suggested_category_id.id,
            "unit_amount": self.amount,
            "quantity": 1,
            "date": self.transaction_date,
            "expense_type": "corporate_card",
            "vendor_name": self.merchant_name,
        }

        expense = Expense.create(vals)
        self.write({
            "match_status": "matched",
            "expense_id": expense.id,
        })

        return expense

    def action_mark_exception(self):
        """Mark as exception for manual review."""
        self.write({"match_status": "exception"})

    def action_ignore(self):
        """Ignore this transaction (e.g., personal expense, refund)."""
        self.write({"match_status": "ignored"})

    def action_view_expense(self):
        """View linked expense."""
        self.ensure_one()
        if not self.expense_id:
            return
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.expense",
            "res_id": self.expense_id.id,
            "view_mode": "form",
        }

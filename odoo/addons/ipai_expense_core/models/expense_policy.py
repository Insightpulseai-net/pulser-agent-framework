# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ExpensePolicy(models.Model):
    """Expense policy rules for Concur-style T&E management."""

    _name = "ipai.expense.policy"
    _description = "Expense Policy"
    _order = "sequence, name"

    name = fields.Char(string="Policy Name", required=True)
    code = fields.Char(string="Policy Code", required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    description = fields.Text(string="Description")

    # Scope
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    department_ids = fields.Many2many(
        "hr.department",
        string="Applicable Departments",
        help="Leave empty to apply to all departments",
    )
    employee_category_ids = fields.Many2many(
        "hr.employee.category",
        string="Employee Categories",
        help="Leave empty to apply to all categories",
    )

    # Limits
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    daily_limit = fields.Monetary(
        string="Daily Limit",
        currency_field="currency_id",
    )
    monthly_limit = fields.Monetary(
        string="Monthly Limit",
        currency_field="currency_id",
    )
    per_transaction_limit = fields.Monetary(
        string="Per Transaction Limit",
        currency_field="currency_id",
    )

    # Receipt requirements
    receipt_required_above = fields.Monetary(
        string="Receipt Required Above",
        currency_field="currency_id",
        default=500.0,
        help="Amount above which receipt is mandatory",
    )
    receipt_types = fields.Selection(
        [
            ("none", "No Receipt Required"),
            ("image", "Photo/Scan"),
            ("official", "Official Receipt (OR) Only"),
        ],
        string="Receipt Type",
        default="image",
    )

    # Approval
    approval_required_above = fields.Monetary(
        string="Approval Required Above",
        currency_field="currency_id",
        default=0.0,
    )
    auto_approve_below = fields.Monetary(
        string="Auto-Approve Below",
        currency_field="currency_id",
        default=0.0,
    )

    # Categories
    allowed_product_ids = fields.Many2many(
        "product.product",
        string="Allowed Expense Categories",
        domain=[("can_be_expensed", "=", True)],
    )
    blocked_product_ids = fields.Many2many(
        "product.product",
        "ipai_expense_policy_blocked_products",
        "policy_id",
        "product_id",
        string="Blocked Expense Categories",
    )

    # Per diem
    per_diem_enabled = fields.Boolean(string="Per Diem Enabled", default=True)
    per_diem_rate = fields.Monetary(
        string="Default Per Diem Rate",
        currency_field="currency_id",
    )

    # Rules
    rule_ids = fields.One2many(
        "ipai.expense.policy.rule",
        "policy_id",
        string="Policy Rules",
    )

    def check_expense(self, expense):
        """Validate an expense against this policy."""
        self.ensure_one()
        violations = []

        # Check per-transaction limit
        if self.per_transaction_limit and expense.total_amount > self.per_transaction_limit:
            violations.append(_(
                "Amount %s exceeds per-transaction limit of %s"
            ) % (expense.total_amount, self.per_transaction_limit))

        # Check receipt requirement
        if self.receipt_required_above and expense.total_amount > self.receipt_required_above:
            if not expense.attachment_ids:
                violations.append(_(
                    "Receipt required for amounts above %s"
                ) % self.receipt_required_above)

        # Check blocked categories
        if expense.product_id in self.blocked_product_ids:
            violations.append(_(
                "Expense category '%s' is not allowed under this policy"
            ) % expense.product_id.name)

        return violations


class ExpensePolicyRule(models.Model):
    """Individual rules within an expense policy."""

    _name = "ipai.expense.policy.rule"
    _description = "Expense Policy Rule"
    _order = "sequence"

    policy_id = fields.Many2one(
        "ipai.expense.policy",
        string="Policy",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(string="Rule Name", required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    rule_type = fields.Selection(
        [
            ("limit", "Amount Limit"),
            ("category", "Category Restriction"),
            ("time", "Time Restriction"),
            ("location", "Location Restriction"),
            ("custom", "Custom Rule"),
        ],
        string="Rule Type",
        required=True,
        default="limit",
    )

    # For limit rules
    limit_type = fields.Selection(
        [
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("per_trip", "Per Trip"),
        ],
        string="Limit Type",
    )
    limit_amount = fields.Monetary(
        string="Limit Amount",
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        related="policy_id.currency_id",
    )

    # For category rules
    product_id = fields.Many2one(
        "product.product",
        string="Expense Category",
        domain=[("can_be_expensed", "=", True)],
    )

    # Action
    action = fields.Selection(
        [
            ("warn", "Warning Only"),
            ("block", "Block Submission"),
            ("require_approval", "Require Extra Approval"),
        ],
        string="Action",
        default="warn",
    )
    warning_message = fields.Text(string="Warning Message")

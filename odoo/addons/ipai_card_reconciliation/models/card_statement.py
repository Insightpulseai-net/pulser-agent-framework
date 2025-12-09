# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CardStatement(models.Model):
    """Corporate card statement."""

    _name = "ipai.card.statement"
    _description = "Card Statement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "statement_date desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )

    # Card details
    card_type = fields.Selection(
        [
            ("visa", "Visa Corporate"),
            ("mastercard", "Mastercard Business"),
            ("amex", "AMEX Business"),
            ("bpi", "BPI Corporate"),
            ("bdo", "BDO Corporate"),
            ("other", "Other"),
        ],
        string="Card Type",
        required=True,
        default="visa",
    )
    card_last_four = fields.Char(
        string="Card Last 4 Digits",
        size=4,
    )
    card_holder_id = fields.Many2one(
        "hr.employee",
        string="Card Holder",
        required=True,
    )

    # Statement details
    statement_date = fields.Date(
        string="Statement Date",
        required=True,
        default=fields.Date.today,
    )
    period_start = fields.Date(string="Period Start")
    period_end = fields.Date(string="Period End")

    # Company
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    # State
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("imported", "Imported"),
            ("in_progress", "Reconciliation In Progress"),
            ("reconciled", "Reconciled"),
            ("posted", "Posted"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Financials
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    total_amount = fields.Monetary(
        string="Total Amount",
        compute="_compute_totals",
        currency_field="currency_id",
        store=True,
    )
    matched_amount = fields.Monetary(
        string="Matched Amount",
        compute="_compute_totals",
        currency_field="currency_id",
        store=True,
    )
    unmatched_amount = fields.Monetary(
        string="Unmatched Amount",
        compute="_compute_totals",
        currency_field="currency_id",
        store=True,
    )

    # Transactions
    transaction_ids = fields.One2many(
        "ipai.card.transaction",
        "statement_id",
        string="Transactions",
    )
    transaction_count = fields.Integer(
        string="Transaction Count",
        compute="_compute_transaction_count",
    )
    matched_count = fields.Integer(
        string="Matched Count",
        compute="_compute_transaction_count",
    )
    exception_count = fields.Integer(
        string="Exceptions",
        compute="_compute_transaction_count",
    )

    # Import details
    import_file = fields.Binary(string="Import File")
    import_filename = fields.Char(string="Import Filename")
    import_date = fields.Datetime(string="Import Date")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ipai.card.statement"
                ) or _("New")
        return super().create(vals_list)

    @api.depends("transaction_ids.amount")
    def _compute_totals(self):
        for statement in self:
            transactions = statement.transaction_ids
            statement.total_amount = sum(transactions.mapped("amount"))
            matched = transactions.filtered(lambda t: t.match_status == "matched")
            statement.matched_amount = sum(matched.mapped("amount"))
            statement.unmatched_amount = statement.total_amount - statement.matched_amount

    @api.depends("transaction_ids", "transaction_ids.match_status")
    def _compute_transaction_count(self):
        for statement in self:
            transactions = statement.transaction_ids
            statement.transaction_count = len(transactions)
            statement.matched_count = len(
                transactions.filtered(lambda t: t.match_status == "matched")
            )
            statement.exception_count = len(
                transactions.filtered(lambda t: t.match_status == "exception")
            )

    def action_import_transactions(self):
        """Open import wizard."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Import Statement"),
            "res_model": "ipai.card.import.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_statement_id": self.id,
            },
        }

    def action_auto_match(self):
        """Attempt to auto-match transactions."""
        self.ensure_one()
        for transaction in self.transaction_ids.filtered(
            lambda t: t.match_status == "unmatched"
        ):
            transaction.action_auto_match()
        self.write({"state": "in_progress"})

    def action_create_expenses(self):
        """Create expenses from unmatched transactions."""
        self.ensure_one()
        created = 0
        for transaction in self.transaction_ids.filtered(
            lambda t: t.match_status == "unmatched" and not t.expense_id
        ):
            transaction.action_create_expense()
            created += 1
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Expenses Created"),
                "message": _("%d expenses created from card transactions") % created,
                "type": "success",
            },
        }

    def action_reconcile(self):
        """Mark statement as reconciled."""
        if self.exception_count > 0:
            raise UserError(_(
                "Cannot reconcile statement with %d unresolved exceptions."
            ) % self.exception_count)
        self.write({"state": "reconciled"})

    def action_post(self):
        """Post reconciled statement to accounting."""
        if self.state != "reconciled":
            raise UserError(_("Statement must be reconciled before posting."))
        # Create journal entries for card transactions
        self.write({"state": "posted"})

    def action_view_transactions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Card Transactions"),
            "res_model": "ipai.card.transaction",
            "view_mode": "tree,form",
            "domain": [("statement_id", "=", self.id)],
            "context": {"default_statement_id": self.id},
        }

    def action_view_exceptions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Exceptions"),
            "res_model": "ipai.card.transaction",
            "view_mode": "tree,form",
            "domain": [
                ("statement_id", "=", self.id),
                ("match_status", "=", "exception"),
            ],
        }

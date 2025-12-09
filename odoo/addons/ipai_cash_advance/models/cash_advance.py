# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta


class CashAdvance(models.Model):
    """Cash advance request with liquidation tracking."""

    _name = "ipai.cash.advance"
    _description = "Cash Advance"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "request_date desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )

    # Employee
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        default=lambda self: self.env.user.employee_id,
        tracking=True,
    )
    department_id = fields.Many2one(
        related="employee_id.department_id",
        store=True,
    )
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
            ("submitted", "Submitted"),
            ("manager_approved", "Manager Approved"),
            ("finance_approved", "Finance Approved"),
            ("released", "Released"),
            ("partially_liquidated", "Partially Liquidated"),
            ("fully_liquidated", "Fully Liquidated"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Request details
    request_date = fields.Date(
        string="Request Date",
        required=True,
        default=fields.Date.today,
    )
    purpose = fields.Text(string="Purpose", required=True)

    advance_type = fields.Selection(
        [
            ("travel", "Travel Advance"),
            ("petty_cash", "Petty Cash"),
            ("project", "Project Expense"),
            ("other", "Other"),
        ],
        string="Advance Type",
        required=True,
        default="travel",
    )

    # Financials
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    amount_requested = fields.Monetary(
        string="Amount Requested",
        currency_field="currency_id",
        required=True,
        tracking=True,
    )
    amount_approved = fields.Monetary(
        string="Amount Approved",
        currency_field="currency_id",
        tracking=True,
    )
    amount_released = fields.Monetary(
        string="Amount Released",
        currency_field="currency_id",
    )
    amount_liquidated = fields.Monetary(
        string="Amount Liquidated",
        compute="_compute_liquidation_amounts",
        currency_field="currency_id",
        store=True,
    )
    amount_outstanding = fields.Monetary(
        string="Outstanding Balance",
        compute="_compute_liquidation_amounts",
        currency_field="currency_id",
        store=True,
    )
    amount_refund = fields.Monetary(
        string="Refund Due",
        compute="_compute_liquidation_amounts",
        currency_field="currency_id",
        store=True,
    )

    # Project
    project_id = fields.Many2one(
        "project.project",
        string="Project",
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
    )

    # Travel reference
    travel_id = fields.Many2one(
        "ipai.travel.request",
        string="Travel Request",
    )

    # Liquidation
    due_date = fields.Date(
        string="Liquidation Due Date",
        compute="_compute_due_date",
        store=True,
    )
    is_overdue = fields.Boolean(
        string="Overdue",
        compute="_compute_is_overdue",
    )
    liquidation_ids = fields.One2many(
        "ipai.cash.advance.liquidation",
        "cash_advance_id",
        string="Liquidations",
    )

    # Approvals
    manager_approved_by = fields.Many2one("res.users", string="Manager Approved By")
    manager_approved_date = fields.Datetime(string="Manager Approved Date")
    finance_approved_by = fields.Many2one("res.users", string="Finance Approved By")
    finance_approved_date = fields.Datetime(string="Finance Approved Date")
    released_by = fields.Many2one("res.users", string="Released By")
    released_date = fields.Datetime(string="Released Date")

    # Accounting
    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
    )
    move_id = fields.Many2one(
        "account.move",
        string="Journal Entry",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ipai.cash.advance"
                ) or _("New")
        return super().create(vals_list)

    @api.depends("request_date")
    def _compute_due_date(self):
        grace_days = 30  # Default grace period
        for record in self:
            if record.request_date:
                record.due_date = record.request_date + timedelta(days=grace_days)
            else:
                record.due_date = False

    @api.depends("due_date", "state")
    def _compute_is_overdue(self):
        today = fields.Date.today()
        for record in self:
            if record.due_date and record.state in ["released", "partially_liquidated"]:
                record.is_overdue = today > record.due_date
            else:
                record.is_overdue = False

    @api.depends("liquidation_ids.amount", "amount_released")
    def _compute_liquidation_amounts(self):
        for record in self:
            liquidated = sum(record.liquidation_ids.mapped("amount"))
            record.amount_liquidated = liquidated
            record.amount_outstanding = record.amount_released - liquidated
            record.amount_refund = max(0, liquidated - record.amount_released) if liquidated else 0

    @api.constrains("amount_requested")
    def _check_amount(self):
        for record in self:
            if record.amount_requested <= 0:
                raise ValidationError(_("Requested amount must be positive."))

    def action_submit(self):
        self.write({"state": "submitted"})

    def action_manager_approve(self):
        self.write({
            "state": "manager_approved",
            "manager_approved_by": self.env.user.id,
            "manager_approved_date": fields.Datetime.now(),
            "amount_approved": self.amount_requested,
        })

    def action_finance_approve(self):
        self.write({
            "state": "finance_approved",
            "finance_approved_by": self.env.user.id,
            "finance_approved_date": fields.Datetime.now(),
        })

    def action_release(self):
        self.write({
            "state": "released",
            "released_by": self.env.user.id,
            "released_date": fields.Datetime.now(),
            "amount_released": self.amount_approved,
        })

    def action_cancel(self):
        if self.state in ["released", "partially_liquidated"]:
            raise UserError(_("Cannot cancel a released cash advance."))
        self.write({"state": "cancelled"})

    def action_add_liquidation(self):
        """Open wizard to add liquidation."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Add Liquidation"),
            "res_model": "ipai.cash.advance.liquidation",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_cash_advance_id": self.id,
            },
        }

    def _check_fully_liquidated(self):
        """Check and update state if fully liquidated."""
        for record in self:
            if record.amount_outstanding <= 0:
                record.write({"state": "fully_liquidated"})
            elif record.amount_liquidated > 0:
                record.write({"state": "partially_liquidated"})

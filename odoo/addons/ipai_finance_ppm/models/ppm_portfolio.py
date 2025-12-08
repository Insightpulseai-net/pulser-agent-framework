# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PpmPortfolio(models.Model):
    """Portfolio for grouping programs and projects."""

    _name = "ipai.ppm.portfolio"
    _description = "PPM Portfolio"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"

    name = fields.Char(
        string="Portfolio Name",
        required=True,
        tracking=True,
    )
    code = fields.Char(
        string="Portfolio Code",
        required=True,
        copy=False,
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    description = fields.Html(string="Description")
    notes = fields.Text(string="Internal Notes")

    # Organization
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    owner_id = fields.Many2one(
        "res.users",
        string="Portfolio Owner",
        tracking=True,
    )
    sponsor_id = fields.Many2one(
        "res.partner",
        string="Executive Sponsor",
    )

    # State
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("on_hold", "On Hold"),
            ("closed", "Closed"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Dates
    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="Target End Date")

    # Hierarchy
    program_ids = fields.One2many(
        "ipai.ppm.program",
        "portfolio_id",
        string="Programs",
    )
    program_count = fields.Integer(
        string="Programs",
        compute="_compute_program_count",
    )

    # Financials
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    budget_total = fields.Monetary(
        string="Total Budget",
        currency_field="currency_id",
        tracking=True,
    )
    budget_allocated = fields.Monetary(
        string="Allocated Budget",
        compute="_compute_budget_metrics",
        currency_field="currency_id",
    )
    budget_spent = fields.Monetary(
        string="Spent Budget",
        compute="_compute_budget_metrics",
        currency_field="currency_id",
    )
    budget_remaining = fields.Monetary(
        string="Remaining Budget",
        compute="_compute_budget_metrics",
        currency_field="currency_id",
    )
    budget_variance = fields.Float(
        string="Budget Variance %",
        compute="_compute_budget_metrics",
    )

    # Strategic alignment
    strategic_priority = fields.Selection(
        [
            ("critical", "Critical"),
            ("high", "High"),
            ("medium", "Medium"),
            ("low", "Low"),
        ],
        string="Strategic Priority",
        default="medium",
        tracking=True,
    )
    strategic_objectives = fields.Text(string="Strategic Objectives")
    expected_benefits = fields.Text(string="Expected Benefits")

    @api.depends("program_ids")
    def _compute_program_count(self):
        for portfolio in self:
            portfolio.program_count = len(portfolio.program_ids)

    @api.depends("program_ids", "program_ids.budget_total", "program_ids.budget_spent")
    def _compute_budget_metrics(self):
        for portfolio in self:
            programs = portfolio.program_ids
            portfolio.budget_allocated = sum(programs.mapped("budget_total"))
            portfolio.budget_spent = sum(programs.mapped("budget_spent"))
            portfolio.budget_remaining = portfolio.budget_total - portfolio.budget_spent

            if portfolio.budget_total:
                variance = ((portfolio.budget_total - portfolio.budget_spent) / portfolio.budget_total) * 100
                portfolio.budget_variance = variance
            else:
                portfolio.budget_variance = 0.0

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for record in self:
            if record.date_start and record.date_end and record.date_start > record.date_end:
                raise ValidationError(_("End date must be after start date."))

    def action_activate(self):
        self.write({"state": "active"})

    def action_hold(self):
        self.write({"state": "on_hold"})

    def action_close(self):
        self.write({"state": "closed"})

    def action_view_programs(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Programs"),
            "res_model": "ipai.ppm.program",
            "view_mode": "kanban,tree,form",
            "domain": [("portfolio_id", "=", self.id)],
            "context": {"default_portfolio_id": self.id},
        }

# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PpmProject(models.Model):
    """PPM-enhanced project with financial tracking."""

    _name = "ipai.ppm.project"
    _description = "PPM Project"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"

    name = fields.Char(string="Project Name", required=True, tracking=True)
    code = fields.Char(string="Project Code", required=True, copy=False)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    description = fields.Html(string="Description")

    # Link to Odoo project
    odoo_project_id = fields.Many2one(
        "project.project",
        string="Odoo Project",
        ondelete="set null",
    )

    # Hierarchy
    program_id = fields.Many2one(
        "ipai.ppm.program",
        string="Program",
        ondelete="restrict",
        tracking=True,
    )
    portfolio_id = fields.Many2one(
        related="program_id.portfolio_id",
        string="Portfolio",
        store=True,
    )

    # Organization
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    project_manager_id = fields.Many2one(
        "res.users",
        string="Project Manager",
        tracking=True,
    )
    team_member_ids = fields.Many2many(
        "res.users",
        string="Team Members",
    )

    # State
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("planning", "Planning"),
            ("approved", "Approved"),
            ("in_progress", "In Progress"),
            ("on_hold", "On Hold"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Dates
    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="Target End Date")
    date_actual_end = fields.Date(string="Actual End Date")

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
    budget_spent = fields.Monetary(
        string="Spent Budget",
        currency_field="currency_id",
        compute="_compute_budget_spent",
        store=True,
    )
    budget_remaining = fields.Monetary(
        string="Remaining Budget",
        compute="_compute_budget_remaining",
        currency_field="currency_id",
    )
    burn_rate = fields.Monetary(
        string="Monthly Burn Rate",
        currency_field="currency_id",
    )

    # Analytics
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
    )

    # Progress
    percent_complete = fields.Float(
        string="% Complete",
        default=0.0,
    )
    health_status = fields.Selection(
        [
            ("green", "On Track"),
            ("yellow", "At Risk"),
            ("red", "Critical"),
        ],
        string="Health Status",
        default="green",
        tracking=True,
    )

    # Risk & Issues
    risk_level = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        string="Risk Level",
        default="low",
    )
    risk_notes = fields.Text(string="Risk Notes")
    issue_notes = fields.Text(string="Issues & Blockers")

    @api.depends("analytic_account_id", "analytic_account_id.line_ids")
    def _compute_budget_spent(self):
        for project in self:
            if project.analytic_account_id:
                lines = self.env["account.analytic.line"].search([
                    ("account_id", "=", project.analytic_account_id.id),
                    ("amount", "<", 0),
                ])
                project.budget_spent = abs(sum(lines.mapped("amount")))
            else:
                project.budget_spent = 0.0

    @api.depends("budget_total", "budget_spent")
    def _compute_budget_remaining(self):
        for project in self:
            project.budget_remaining = project.budget_total - project.budget_spent

    def action_approve(self):
        self.write({"state": "approved"})

    def action_start(self):
        self.write({"state": "in_progress"})

    def action_complete(self):
        self.write({
            "state": "completed",
            "date_actual_end": fields.Date.today(),
            "percent_complete": 100.0,
        })

    def action_cancel(self):
        self.write({"state": "cancelled"})

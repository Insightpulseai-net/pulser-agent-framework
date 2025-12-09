# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PpmProgram(models.Model):
    """Program for grouping related projects."""

    _name = "ipai.ppm.program"
    _description = "PPM Program"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"

    name = fields.Char(string="Program Name", required=True, tracking=True)
    code = fields.Char(string="Program Code", required=True, copy=False)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    description = fields.Html(string="Description")

    # Hierarchy
    portfolio_id = fields.Many2one(
        "ipai.ppm.portfolio",
        string="Portfolio",
        ondelete="restrict",
        tracking=True,
    )
    project_ids = fields.One2many(
        "ipai.ppm.project",
        "program_id",
        string="Projects",
    )
    project_count = fields.Integer(
        string="Projects",
        compute="_compute_project_count",
    )

    # Organization
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    manager_id = fields.Many2one(
        "res.users",
        string="Program Manager",
        tracking=True,
    )

    # State
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("planning", "Planning"),
            ("active", "Active"),
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
        compute="_compute_budget_spent",
        currency_field="currency_id",
    )
    budget_remaining = fields.Monetary(
        string="Remaining Budget",
        compute="_compute_budget_remaining",
        currency_field="currency_id",
    )

    @api.depends("project_ids")
    def _compute_project_count(self):
        for program in self:
            program.project_count = len(program.project_ids)

    @api.depends("project_ids.budget_spent")
    def _compute_budget_spent(self):
        for program in self:
            program.budget_spent = sum(program.project_ids.mapped("budget_spent"))

    @api.depends("budget_total", "budget_spent")
    def _compute_budget_remaining(self):
        for program in self:
            program.budget_remaining = program.budget_total - program.budget_spent

    def action_view_projects(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Projects"),
            "res_model": "ipai.ppm.project",
            "view_mode": "kanban,tree,form",
            "domain": [("program_id", "=", self.id)],
            "context": {"default_program_id": self.id},
        }

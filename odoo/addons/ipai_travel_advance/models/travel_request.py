# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta


class TravelRequest(models.Model):
    """Travel request with advance management."""

    _name = "ipai.travel.request"
    _description = "Travel Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_departure desc, id desc"

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
    manager_id = fields.Many2one(
        related="employee_id.parent_id",
        string="Manager",
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
            ("approved", "Approved"),
            ("advance_issued", "Advance Issued"),
            ("traveling", "Traveling"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Trip details
    purpose = fields.Text(string="Purpose of Travel", required=True)
    destination = fields.Char(string="Destination", required=True)
    destination_country_id = fields.Many2one(
        "res.country",
        string="Destination Country",
    )
    is_international = fields.Boolean(
        string="International Travel",
        compute="_compute_is_international",
        store=True,
    )

    # Dates
    date_departure = fields.Date(string="Departure Date", required=True)
    date_return = fields.Date(string="Return Date", required=True)
    duration_days = fields.Integer(
        string="Duration (Days)",
        compute="_compute_duration",
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

    # Financials
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    estimated_cost = fields.Monetary(
        string="Estimated Cost",
        currency_field="currency_id",
    )
    per_diem_rate = fields.Monetary(
        string="Per Diem Rate",
        currency_field="currency_id",
    )
    per_diem_total = fields.Monetary(
        string="Total Per Diem",
        compute="_compute_per_diem_total",
        currency_field="currency_id",
        store=True,
    )
    advance_requested = fields.Monetary(
        string="Advance Requested",
        currency_field="currency_id",
    )
    advance_approved = fields.Monetary(
        string="Advance Approved",
        currency_field="currency_id",
    )

    # Itinerary
    itinerary_ids = fields.One2many(
        "ipai.travel.itinerary",
        "travel_id",
        string="Itinerary",
    )

    # Expenses
    expense_ids = fields.One2many(
        "hr.expense",
        "trip_id",
        string="Expenses",
    )
    expense_total = fields.Monetary(
        string="Total Expenses",
        compute="_compute_expense_total",
        currency_field="currency_id",
    )

    # Approvals
    approved_by = fields.Many2one("res.users", string="Approved By")
    approved_date = fields.Datetime(string="Approved Date")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ipai.travel.request"
                ) or _("New")
        return super().create(vals_list)

    @api.depends("destination_country_id", "company_id")
    def _compute_is_international(self):
        for record in self:
            if record.destination_country_id and record.company_id.country_id:
                record.is_international = (
                    record.destination_country_id != record.company_id.country_id
                )
            else:
                record.is_international = False

    @api.depends("date_departure", "date_return")
    def _compute_duration(self):
        for record in self:
            if record.date_departure and record.date_return:
                delta = record.date_return - record.date_departure
                record.duration_days = delta.days + 1
            else:
                record.duration_days = 0

    @api.depends("duration_days", "per_diem_rate")
    def _compute_per_diem_total(self):
        for record in self:
            record.per_diem_total = record.duration_days * record.per_diem_rate

    @api.depends("expense_ids.total_amount")
    def _compute_expense_total(self):
        for record in self:
            record.expense_total = sum(record.expense_ids.mapped("total_amount"))

    @api.onchange("destination")
    def _onchange_destination(self):
        """Auto-set per diem rate based on destination."""
        if self.destination:
            PerDiem = self.env["ipai.travel.per.diem"]
            rate = PerDiem.search([
                ("destination", "ilike", self.destination),
                ("active", "=", True),
            ], limit=1)
            if rate:
                self.per_diem_rate = rate.rate

    def action_submit(self):
        self.write({"state": "submitted"})

    def action_approve(self):
        self.write({
            "state": "approved",
            "approved_by": self.env.user.id,
            "approved_date": fields.Datetime.now(),
            "advance_approved": self.advance_requested,
        })

    def action_issue_advance(self):
        self.write({"state": "advance_issued"})

    def action_start_travel(self):
        self.write({"state": "traveling"})

    def action_complete(self):
        self.write({"state": "completed"})

    def action_cancel(self):
        self.write({"state": "cancelled"})

    def action_create_expense_report(self):
        """Create expense report from travel request."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Expense Report"),
            "res_model": "hr.expense.sheet",
            "view_mode": "form",
            "context": {
                "default_employee_id": self.employee_id.id,
                "default_name": f"Travel: {self.destination} ({self.name})",
            },
        }


class TravelItinerary(models.Model):
    """Itinerary item for travel request."""

    _name = "ipai.travel.itinerary"
    _description = "Travel Itinerary"
    _order = "date, sequence"

    travel_id = fields.Many2one(
        "ipai.travel.request",
        string="Travel Request",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    date = fields.Date(string="Date", required=True)

    itinerary_type = fields.Selection(
        [
            ("flight", "Flight"),
            ("hotel", "Hotel"),
            ("car", "Car Rental"),
            ("train", "Train"),
            ("meeting", "Meeting"),
            ("other", "Other"),
        ],
        string="Type",
        required=True,
        default="other",
    )

    description = fields.Text(string="Description")
    location = fields.Char(string="Location")
    booking_reference = fields.Char(string="Booking Reference")

    # Costs
    currency_id = fields.Many2one(
        related="travel_id.currency_id",
    )
    estimated_cost = fields.Monetary(
        string="Estimated Cost",
        currency_field="currency_id",
    )

# -*- coding: utf-8 -*-
from odoo import api, fields, models


class TravelPerDiem(models.Model):
    """Per diem rates by destination."""

    _name = "ipai.travel.per.diem"
    _description = "Travel Per Diem Rate"
    _order = "destination"

    destination = fields.Char(string="Destination", required=True)
    country_id = fields.Many2one("res.country", string="Country")
    active = fields.Boolean(default=True)

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    rate = fields.Monetary(
        string="Daily Rate",
        currency_field="currency_id",
        required=True,
    )

    # Breakdown
    meals_rate = fields.Monetary(
        string="Meals",
        currency_field="currency_id",
    )
    incidentals_rate = fields.Monetary(
        string="Incidentals",
        currency_field="currency_id",
    )

    notes = fields.Text(string="Notes")

    _sql_constraints = [
        ("destination_unique", "unique(destination, country_id)",
         "Per diem rate for this destination already exists."),
    ]

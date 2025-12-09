# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class CashAdvanceLiquidation(models.Model):
    """Liquidation entry for cash advance."""

    _name = "ipai.cash.advance.liquidation"
    _description = "Cash Advance Liquidation"
    _order = "date desc, id desc"

    cash_advance_id = fields.Many2one(
        "ipai.cash.advance",
        string="Cash Advance",
        required=True,
        ondelete="cascade",
    )

    date = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.today,
    )
    description = fields.Char(string="Description", required=True)

    # Amount
    currency_id = fields.Many2one(
        related="cash_advance_id.currency_id",
    )
    amount = fields.Monetary(
        string="Amount",
        currency_field="currency_id",
        required=True,
    )

    # Supporting documents
    expense_id = fields.Many2one(
        "hr.expense",
        string="Linked Expense",
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        string="Receipts/Documents",
    )

    # Verification
    verified = fields.Boolean(string="Verified", default=False)
    verified_by = fields.Many2one("res.users", string="Verified By")
    verified_date = fields.Datetime(string="Verified Date")

    notes = fields.Text(string="Notes")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Update parent cash advance state
        for record in records:
            record.cash_advance_id._check_fully_liquidated()
        return records

    def write(self, vals):
        result = super().write(vals)
        # Update parent cash advance state
        for record in self:
            record.cash_advance_id._check_fully_liquidated()
        return result

    def action_verify(self):
        self.write({
            "verified": True,
            "verified_by": self.env.user.id,
            "verified_date": fields.Datetime.now(),
        })

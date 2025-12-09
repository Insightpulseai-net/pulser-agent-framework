# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrExpense(models.Model):
    """Extended expense with Concur-style features."""

    _inherit = "hr.expense"

    # Policy
    policy_id = fields.Many2one(
        "ipai.expense.policy",
        string="Expense Policy",
        compute="_compute_policy_id",
        store=True,
    )
    policy_violations = fields.Text(
        string="Policy Violations",
        compute="_compute_policy_violations",
    )
    policy_status = fields.Selection(
        [
            ("compliant", "Compliant"),
            ("warning", "Warning"),
            ("violation", "Violation"),
        ],
        string="Policy Status",
        compute="_compute_policy_violations",
    )

    # Enhanced fields
    expense_type = fields.Selection(
        [
            ("standard", "Standard Expense"),
            ("per_diem", "Per Diem"),
            ("mileage", "Mileage"),
            ("corporate_card", "Corporate Card"),
        ],
        string="Expense Type",
        default="standard",
    )

    # Trip/Travel reference
    trip_id = fields.Many2one(
        "ipai.travel.request",
        string="Travel Request",
        ondelete="set null",
    )

    # Project/Cost center
    project_code = fields.Char(string="Project Code")
    cost_center = fields.Char(string="Cost Center")

    # Receipt details
    receipt_number = fields.Char(string="Receipt/Invoice Number")
    receipt_date = fields.Date(string="Receipt Date")
    vendor_name = fields.Char(string="Vendor Name")
    vendor_tin = fields.Char(string="Vendor TIN")

    # Tax handling (PH-specific)
    is_vatable = fields.Boolean(string="VATable", default=True)
    vat_amount = fields.Monetary(
        string="VAT Amount",
        currency_field="currency_id",
        compute="_compute_vat_amount",
        store=True,
    )
    withholding_tax = fields.Monetary(
        string="Withholding Tax",
        currency_field="currency_id",
    )
    net_amount = fields.Monetary(
        string="Net Amount",
        currency_field="currency_id",
        compute="_compute_net_amount",
        store=True,
    )

    # OCR integration
    ocr_job_id = fields.Char(string="OCR Job ID")
    ocr_confidence = fields.Float(string="OCR Confidence")
    ocr_extracted_data = fields.Text(string="OCR Extracted Data")

    @api.depends("employee_id", "employee_id.department_id")
    def _compute_policy_id(self):
        Policy = self.env["ipai.expense.policy"]
        for expense in self:
            domain = [
                ("company_id", "=", expense.company_id.id),
                ("active", "=", True),
            ]
            if expense.employee_id.department_id:
                domain.append("|")
                domain.append(("department_ids", "=", False))
                domain.append(("department_ids", "in", expense.employee_id.department_id.ids))

            policy = Policy.search(domain, limit=1)
            expense.policy_id = policy

    @api.depends("policy_id", "total_amount", "product_id", "attachment_ids")
    def _compute_policy_violations(self):
        for expense in self:
            if expense.policy_id:
                violations = expense.policy_id.check_expense(expense)
                expense.policy_violations = "\n".join(violations) if violations else ""
                if violations:
                    expense.policy_status = "violation"
                else:
                    expense.policy_status = "compliant"
            else:
                expense.policy_violations = ""
                expense.policy_status = "compliant"

    @api.depends("total_amount", "is_vatable")
    def _compute_vat_amount(self):
        for expense in self:
            if expense.is_vatable:
                # PH VAT is 12%
                expense.vat_amount = expense.total_amount * 0.12 / 1.12
            else:
                expense.vat_amount = 0.0

    @api.depends("total_amount", "withholding_tax")
    def _compute_net_amount(self):
        for expense in self:
            expense.net_amount = expense.total_amount - expense.withholding_tax

    def action_submit_expenses(self):
        """Override to check policy before submission."""
        for expense in self:
            if expense.policy_status == "violation":
                raise UserError(_(
                    "Cannot submit expense with policy violations:\n%s"
                ) % expense.policy_violations)
        return super().action_submit_expenses()

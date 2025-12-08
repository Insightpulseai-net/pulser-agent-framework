# -*- coding: utf-8 -*-
import base64
import csv
import io
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CardImportWizard(models.TransientModel):
    """Wizard to import card statement transactions."""

    _name = "ipai.card.import.wizard"
    _description = "Import Card Statement Wizard"

    statement_id = fields.Many2one(
        "ipai.card.statement",
        string="Statement",
        required=True,
    )

    file = fields.Binary(string="Statement File", required=True)
    filename = fields.Char(string="Filename")

    file_format = fields.Selection(
        [
            ("csv", "CSV"),
            ("ofx", "OFX"),
            ("qif", "QIF"),
        ],
        string="File Format",
        required=True,
        default="csv",
    )

    # CSV options
    delimiter = fields.Selection(
        [
            (",", "Comma (,)"),
            (";", "Semicolon (;)"),
            ("\t", "Tab"),
        ],
        string="Delimiter",
        default=",",
    )
    skip_header = fields.Boolean(string="Skip Header Row", default=True)

    # Column mapping for CSV
    date_column = fields.Integer(string="Date Column", default=0)
    merchant_column = fields.Integer(string="Merchant Column", default=1)
    amount_column = fields.Integer(string="Amount Column", default=2)
    description_column = fields.Integer(string="Description Column", default=3)
    reference_column = fields.Integer(string="Reference Column", default=4)

    date_format = fields.Selection(
        [
            ("%Y-%m-%d", "YYYY-MM-DD"),
            ("%d/%m/%Y", "DD/MM/YYYY"),
            ("%m/%d/%Y", "MM/DD/YYYY"),
            ("%d-%m-%Y", "DD-MM-YYYY"),
        ],
        string="Date Format",
        default="%Y-%m-%d",
    )

    preview_lines = fields.Text(
        string="Preview",
        compute="_compute_preview",
        readonly=True,
    )

    @api.depends("file", "delimiter", "skip_header")
    def _compute_preview(self):
        for wizard in self:
            if not wizard.file:
                wizard.preview_lines = ""
                continue

            try:
                content = base64.b64decode(wizard.file).decode("utf-8")
                lines = content.split("\n")[:6]  # First 6 lines
                wizard.preview_lines = "\n".join(lines)
            except Exception as e:
                wizard.preview_lines = f"Error reading file: {e}"

    def action_import(self):
        """Import transactions from file."""
        self.ensure_one()

        if self.file_format == "csv":
            return self._import_csv()
        elif self.file_format == "ofx":
            return self._import_ofx()
        elif self.file_format == "qif":
            return self._import_qif()

    def _import_csv(self):
        """Import from CSV file."""
        from datetime import datetime

        content = base64.b64decode(self.file).decode("utf-8")
        reader = csv.reader(io.StringIO(content), delimiter=self.delimiter)

        Transaction = self.env["ipai.card.transaction"]
        created_count = 0
        errors = []

        for i, row in enumerate(reader):
            if self.skip_header and i == 0:
                continue

            if len(row) < max(
                self.date_column,
                self.merchant_column,
                self.amount_column
            ) + 1:
                errors.append(f"Row {i+1}: Not enough columns")
                continue

            try:
                # Parse date
                date_str = row[self.date_column].strip()
                transaction_date = datetime.strptime(date_str, self.date_format).date()

                # Parse amount
                amount_str = row[self.amount_column].strip()
                amount_str = amount_str.replace(",", "").replace("$", "").replace("PHP", "")
                amount = float(amount_str)

                # Get other fields
                merchant = row[self.merchant_column].strip()
                description = ""
                if len(row) > self.description_column:
                    description = row[self.description_column].strip()
                reference = ""
                if len(row) > self.reference_column:
                    reference = row[self.reference_column].strip()

                # Create transaction
                Transaction.create({
                    "statement_id": self.statement_id.id,
                    "transaction_date": transaction_date,
                    "merchant_name": merchant,
                    "amount": abs(amount),
                    "description": description,
                    "reference": reference,
                })
                created_count += 1

            except Exception as e:
                errors.append(f"Row {i+1}: {str(e)}")

        # Update statement
        self.statement_id.write({
            "state": "imported",
            "import_date": fields.Datetime.now(),
        })

        # Return result
        message = _("%d transactions imported.") % created_count
        if errors:
            message += _("\n\n%d errors:\n") % len(errors)
            message += "\n".join(errors[:10])
            if len(errors) > 10:
                message += _("\n... and %d more errors") % (len(errors) - 10)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Import Complete"),
                "message": message,
                "type": "success" if not errors else "warning",
            },
        }

    def _import_ofx(self):
        """Import from OFX file."""
        raise UserError(_("OFX import not yet implemented."))

    def _import_qif(self):
        """Import from QIF file."""
        raise UserError(_("QIF import not yet implemented."))

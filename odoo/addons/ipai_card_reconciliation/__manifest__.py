# -*- coding: utf-8 -*-
{
    "name": "IPAI Card Reconciliation",
    "version": "18.0.1.0.0",
    "category": "Accounting/Finance",
    "summary": "Corporate Card Statement Import and Reconciliation",
    "description": """
InsightPulseAI Card Reconciliation Module
=========================================

Smart Delta module for corporate card management:

Features:
---------
* Corporate card statement import (CSV, OFX, QIF)
* Automatic transaction categorization
* AI-powered receipt matching
* Exceptions queue for unmatched transactions
* Bulk expense creation from card transactions
* Reconciliation workflow
* Fraud detection flags

Supported Card Types:
- Visa Corporate
- Mastercard Business
- AMEX Business
- BPI Corporate Cards (PH-specific)
- BDO Corporate Cards (PH-specific)

This module provides SAP Concur-style corporate card
reconciliation for expense management.
    """,
    "author": "InsightPulseAI",
    "website": "https://insightpulseai.net",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "hr",
        "hr_expense",
        "account",
        "ipai_expense_core",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/card_data.xml",
        "views/card_statement_views.xml",
        "views/card_transaction_views.xml",
        "views/card_menu.xml",
        "wizard/import_statement_wizard.xml",
    ],
    "demo": [
        "demo/card_demo.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}

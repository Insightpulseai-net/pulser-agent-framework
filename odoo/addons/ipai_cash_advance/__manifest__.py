# -*- coding: utf-8 -*-
{
    "name": "IPAI Cash Advance",
    "version": "18.0.1.0.0",
    "category": "Human Resources/Expenses",
    "summary": "Cash Advance Request and Liquidation Management",
    "description": """
InsightPulseAI Cash Advance Module
==================================

Smart Delta module for cash advance and liquidation:

Features:
---------
* Cash advance request workflow
* Multi-level approval based on amount
* Partial and full liquidation
* Outstanding balance tracking
* Automatic reminder for overdue advances
* Integration with expense reports
* Finance posting automation

This module provides SAP Concur-style cash advance management
for handling petty cash and travel advances.
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
        "data/cash_advance_data.xml",
        "views/cash_advance_views.xml",
        "views/cash_advance_menu.xml",
    ],
    "demo": [
        "demo/cash_advance_demo.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}

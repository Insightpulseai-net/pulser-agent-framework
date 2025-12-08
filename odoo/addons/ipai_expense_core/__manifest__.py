# -*- coding: utf-8 -*-
{
    "name": "IPAI Expense Core",
    "version": "18.0.1.0.0",
    "category": "Human Resources/Expenses",
    "summary": "SAP Concur-style Expense Management for Philippines",
    "description": """
InsightPulseAI Expense Core Module
==================================

Smart Delta module providing SAP Concur-style expense management:

Features:
---------
* Multi-level expense approval workflow
* Policy-based expense validation
* Receipt OCR integration
* Per-diem automation
* VAT/withholding tax handling (PH-specific)
* Corporate card integration hooks
* Expense analytics and reporting

PH-Specific Features:
- BIR-compliant receipt requirements
- Withholding tax calculation
- VAT recovery tracking
- SSS/PhilHealth/Pag-IBIG deduction integration

Dependencies:
- hr_expense, account, documents
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
        "documents",
        "approvals",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/expense_security.xml",
        "data/expense_policy_data.xml",
        "views/expense_policy_views.xml",
        "views/expense_views.xml",
        "views/expense_menu.xml",
    ],
    "demo": [
        "demo/expense_demo.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}

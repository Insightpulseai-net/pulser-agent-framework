# -*- coding: utf-8 -*-
{
    "name": "IPAI Finance PPM",
    "version": "18.0.1.0.0",
    "category": "Project/Finance",
    "summary": "Portfolio & Project Management with Finance Integration",
    "description": """
InsightPulseAI Finance PPM Module
=================================

Smart Delta module providing Planview Clarity / SAP PPM-style capabilities:

Features:
---------
* Portfolio management with financial tracking
* Project budgeting and cost control
* Resource capacity planning
* Benefits realization tracking
* Integration with Odoo Accounting and Projects
* Multi-currency support for PHP operations

This module extends Odoo's project management with:
- Portfolio hierarchy (Portfolio > Program > Project)
- Budget vs. Actual tracking
- Burn rate analytics
- Roadmap and timeline views
- Financial KPI dashboards

Dependencies:
- base, project, account, hr, analytic
    """,
    "author": "InsightPulseAI",
    "website": "https://insightpulseai.net",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "project",
        "account",
        "hr",
        "analytic",
    ],
    "data": [
        # Security
        "security/ir.model.access.csv",
        "security/ppm_security.xml",
        # Views
        "views/ppm_portfolio_views.xml",
        "views/ppm_program_views.xml",
        "views/ppm_project_views.xml",
        "views/ppm_menu.xml",
        # Data
        "data/ppm_data.xml",
    ],
    "demo": [
        "demo/ppm_demo.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "ipai_finance_ppm/static/src/css/ppm.css",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}

# -*- coding: utf-8 -*-
{
    "name": "IPAI Travel Advance",
    "version": "18.0.1.0.0",
    "category": "Human Resources/Expenses",
    "summary": "Travel Request and Advance Management",
    "description": """
InsightPulseAI Travel Advance Module
====================================

Smart Delta module for travel request and advance management:

Features:
---------
* Travel request workflow with approvals
* Travel advance (cash/card) management
* Per-diem calculation by destination
* Itinerary and booking tracking
* Integration with expense reports
* Travel policy enforcement

This module provides SAP Concur Travel-style functionality for
managing business travel requests and advances.
    """,
    "author": "InsightPulseAI",
    "website": "https://insightpulseai.net",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "hr",
        "hr_expense",
        "approvals",
        "ipai_expense_core",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/travel_data.xml",
        "views/travel_request_views.xml",
        "views/travel_menu.xml",
    ],
    "demo": [
        "demo/travel_demo.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}

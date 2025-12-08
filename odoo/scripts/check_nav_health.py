#!/usr/bin/env python3
"""
Navigation Health Check for Concur-Style T&E Suite
===================================================

This script validates that all navigation tabs and menus are functional:
- Logs in as test user(s)
- Walks main T&E menus (Expenses, Cash Advances, Trips, Approvals, Analytics)
- Verifies no 404, 500, or empty views when demo data is expected
- Exits non-zero if any check fails (for CI/Makefile integration)

Usage:
    python check_nav_health.py             # Run all health checks
    python check_nav_health.py --verbose   # Detailed output
    python check_nav_health.py --user demo # Check as specific user

Environment Variables:
    ODOO_URL        - Odoo server URL (default: http://localhost:8069)
    ODOO_DB         - Database name (default: odoo)
    ODOO_USER       - Admin username (default: admin)
    ODOO_PASSWORD   - Admin password (required)
"""

import os
import sys
import argparse
import logging
import json
import re
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    import requests
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

# Load environment
load_dotenv()

# Configuration
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "odoo")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "")

# Console for rich output
console = Console()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("check_nav_health.log"),
    ]
)
logger = logging.getLogger(__name__)


class CheckStatus(Enum):
    """Status of a health check."""
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


@dataclass
class NavCheckResult:
    """Result of a navigation check."""
    menu_name: str
    url: str
    status: CheckStatus
    status_code: int
    message: str
    has_data: bool = False
    response_time_ms: float = 0


# Menu items to check for Concur-style T&E suite
MENU_CHECKS = [
    {
        "name": "Dashboard",
        "path": "/web",
        "action": None,
        "required": True,
        "expect_data": False,
    },
    {
        "name": "Expenses - My Expenses",
        "path": "/web#action=hr_expense.hr_expense_action_my_expenses",
        "model": "hr.expense",
        "view_type": "list",
        "required": True,
        "expect_data": True,
    },
    {
        "name": "Expenses - All Expenses",
        "path": "/web#action=hr_expense.hr_expense_action",
        "model": "hr.expense",
        "view_type": "list",
        "required": True,
        "expect_data": True,
    },
    {
        "name": "Expenses - Reports",
        "path": "/web#action=hr_expense.hr_expense_sheet_action_all",
        "model": "hr.expense.sheet",
        "view_type": "list",
        "required": True,
        "expect_data": False,
    },
    {
        "name": "Expenses - To Approve",
        "path": "/web#action=hr_expense.hr_expense_sheet_action_approve",
        "model": "hr.expense.sheet",
        "view_type": "list",
        "required": True,
        "expect_data": False,
    },
    {
        "name": "Employees",
        "path": "/web#action=hr.open_view_employee_list_my",
        "model": "hr.employee",
        "view_type": "kanban",
        "required": True,
        "expect_data": True,
    },
    {
        "name": "Projects",
        "path": "/web#action=project.open_view_project_all_config",
        "model": "project.project",
        "view_type": "kanban",
        "required": False,
        "expect_data": True,
    },
    {
        "name": "Approvals",
        "path": "/web#action=approvals.approval_request_action",
        "model": "approval.request",
        "view_type": "kanban",
        "required": False,
        "expect_data": False,
    },
    {
        "name": "Accounting Dashboard",
        "path": "/web#action=account.action_account_moves_all",
        "model": "account.move",
        "view_type": "list",
        "required": False,
        "expect_data": False,
    },
    {
        "name": "Finance PPM (Smart Delta)",
        "path": "/web#action=ipai_finance_ppm.action_ppm_dashboard",
        "model": "ipai.ppm.project",
        "view_type": "kanban",
        "required": False,
        "expect_data": False,
    },
    {
        "name": "Travel Advance (Smart Delta)",
        "path": "/web#action=ipai_travel_advance.action_travel_request",
        "model": "ipai.travel.request",
        "view_type": "list",
        "required": False,
        "expect_data": False,
    },
    {
        "name": "Cash Advance (Smart Delta)",
        "path": "/web#action=ipai_cash_advance.action_cash_advance",
        "model": "ipai.cash.advance",
        "view_type": "list",
        "required": False,
        "expect_data": False,
    },
    {
        "name": "Card Reconciliation (Smart Delta)",
        "path": "/web#action=ipai_card_reconciliation.action_card_statement",
        "model": "ipai.card.statement",
        "view_type": "list",
        "required": False,
        "expect_data": False,
    },
]


class OdooNavChecker:
    """Checks Odoo navigation health."""

    def __init__(self, base_url: str, db: str, user: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.db = db
        self.user = user
        self.password = password
        self.session: Optional[requests.Session] = None
        self.csrf_token: Optional[str] = None
        self.session_id: Optional[str] = None

    def login(self) -> bool:
        """Login to Odoo and establish session."""
        self.session = requests.Session()

        try:
            # Get CSRF token from login page
            login_page_url = f"{self.base_url}/web/login"
            response = self.session.get(login_page_url, timeout=30)

            if response.status_code != 200:
                console.print(f"[red]Failed to load login page: {response.status_code}[/red]")
                return False

            # Extract CSRF token
            csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', response.text)
            if csrf_match:
                self.csrf_token = csrf_match.group(1)

            # Perform login
            login_url = f"{self.base_url}/web/login"
            login_data = {
                "login": self.user,
                "password": self.password,
                "db": self.db,
                "redirect": "/web",
            }

            if self.csrf_token:
                login_data["csrf_token"] = self.csrf_token

            response = self.session.post(
                login_url,
                data=login_data,
                allow_redirects=True,
                timeout=30,
            )

            # Check if login was successful
            if "session_id" in self.session.cookies:
                self.session_id = self.session.cookies.get("session_id")
                console.print(f"[green]Logged in as {self.user}[/green]")
                logger.info(f"Login successful for user: {self.user}")
                return True

            # Check for login error in response
            if "/web/login" in response.url or "Invalid" in response.text:
                console.print("[red]Login failed - invalid credentials[/red]")
                return False

            # Assume success if we got redirected to /web
            if "/web" in response.url and "/login" not in response.url:
                console.print(f"[green]Logged in as {self.user}[/green]")
                return True

            console.print(f"[yellow]Login status unclear, continuing...[/yellow]")
            return True

        except requests.exceptions.RequestException as e:
            console.print(f"[red]Connection error: {e}[/red]")
            logger.error(f"Login connection error: {e}")
            return False

    def check_menu(self, menu: Dict) -> NavCheckResult:
        """Check if a menu/navigation item is accessible and functional."""
        import time

        menu_name = menu["name"]
        path = menu["path"]
        full_url = f"{self.base_url}{path}"

        start_time = time.time()

        try:
            response = self.session.get(full_url, timeout=30)
            response_time = (time.time() - start_time) * 1000

            # Check status code
            if response.status_code >= 500:
                return NavCheckResult(
                    menu_name=menu_name,
                    url=full_url,
                    status=CheckStatus.ERROR,
                    status_code=response.status_code,
                    message=f"Server error: {response.status_code}",
                    response_time_ms=response_time,
                )

            if response.status_code == 404:
                # For optional Smart Delta modules, 404 is acceptable
                if not menu.get("required", True):
                    return NavCheckResult(
                        menu_name=menu_name,
                        url=full_url,
                        status=CheckStatus.SKIPPED,
                        status_code=response.status_code,
                        message="Module not installed (optional)",
                        response_time_ms=response_time,
                    )
                return NavCheckResult(
                    menu_name=menu_name,
                    url=full_url,
                    status=CheckStatus.ERROR,
                    status_code=response.status_code,
                    message="Page not found",
                    response_time_ms=response_time,
                )

            if response.status_code != 200:
                return NavCheckResult(
                    menu_name=menu_name,
                    url=full_url,
                    status=CheckStatus.WARNING,
                    status_code=response.status_code,
                    message=f"Unexpected status: {response.status_code}",
                    response_time_ms=response_time,
                )

            # Check for login redirect (session expired)
            if "/web/login" in response.url:
                return NavCheckResult(
                    menu_name=menu_name,
                    url=full_url,
                    status=CheckStatus.ERROR,
                    status_code=response.status_code,
                    message="Session expired - redirected to login",
                    response_time_ms=response_time,
                )

            # Check for empty data warnings
            has_data = True
            if menu.get("expect_data", False):
                # For list/kanban views, check if there's actual content
                # This is a simplified check - in production you might use RPC
                if "o_nocontent" in response.text or "No record found" in response.text:
                    has_data = False
                    if menu.get("required", True):
                        return NavCheckResult(
                            menu_name=menu_name,
                            url=full_url,
                            status=CheckStatus.WARNING,
                            status_code=response.status_code,
                            message="View loaded but no data found",
                            has_data=False,
                            response_time_ms=response_time,
                        )

            # Check for error messages in page content
            error_patterns = [
                r"Traceback",
                r"Internal Server Error",
                r"AccessError",
                r"ValidationError",
            ]

            for pattern in error_patterns:
                if re.search(pattern, response.text, re.IGNORECASE):
                    return NavCheckResult(
                        menu_name=menu_name,
                        url=full_url,
                        status=CheckStatus.ERROR,
                        status_code=response.status_code,
                        message=f"Error pattern found: {pattern}",
                        response_time_ms=response_time,
                    )

            return NavCheckResult(
                menu_name=menu_name,
                url=full_url,
                status=CheckStatus.OK,
                status_code=response.status_code,
                message="OK",
                has_data=has_data,
                response_time_ms=response_time,
            )

        except requests.exceptions.Timeout:
            return NavCheckResult(
                menu_name=menu_name,
                url=full_url,
                status=CheckStatus.ERROR,
                status_code=0,
                message="Request timed out",
            )
        except requests.exceptions.RequestException as e:
            return NavCheckResult(
                menu_name=menu_name,
                url=full_url,
                status=CheckStatus.ERROR,
                status_code=0,
                message=f"Request failed: {str(e)[:50]}",
            )

    def check_all_menus(self, verbose: bool = False) -> List[NavCheckResult]:
        """Check all configured menu items."""
        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            task = progress.add_task("Checking navigation...", total=len(MENU_CHECKS))

            for menu in MENU_CHECKS:
                progress.update(task, description=f"Checking {menu['name']}...")
                result = self.check_menu(menu)
                results.append(result)

                if verbose:
                    status_color = {
                        CheckStatus.OK: "green",
                        CheckStatus.WARNING: "yellow",
                        CheckStatus.ERROR: "red",
                        CheckStatus.SKIPPED: "dim",
                    }.get(result.status, "white")

                    console.print(
                        f"  [{status_color}]{result.status.value}[/{status_color}] "
                        f"{result.menu_name} ({result.response_time_ms:.0f}ms)"
                    )

                progress.advance(task)

        return results


def print_results_table(results: List[NavCheckResult]):
    """Print results in a formatted table."""
    table = Table(title="Navigation Health Check Results")
    table.add_column("Menu", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Code", justify="right")
    table.add_column("Time (ms)", justify="right")
    table.add_column("Message")

    for r in results:
        status_style = {
            CheckStatus.OK: "green",
            CheckStatus.WARNING: "yellow",
            CheckStatus.ERROR: "red",
            CheckStatus.SKIPPED: "dim",
        }.get(r.status, "white")

        table.add_row(
            r.menu_name,
            f"[{status_style}]{r.status.value}[/{status_style}]",
            str(r.status_code) if r.status_code else "-",
            f"{r.response_time_ms:.0f}" if r.response_time_ms else "-",
            r.message[:40] + "..." if len(r.message) > 40 else r.message,
        )

    console.print(table)


def summarize_results(results: List[NavCheckResult]) -> Tuple[int, int, int, int]:
    """Summarize results and return counts."""
    ok = sum(1 for r in results if r.status == CheckStatus.OK)
    warn = sum(1 for r in results if r.status == CheckStatus.WARNING)
    error = sum(1 for r in results if r.status == CheckStatus.ERROR)
    skipped = sum(1 for r in results if r.status == CheckStatus.SKIPPED)
    return ok, warn, error, skipped


def main():
    parser = argparse.ArgumentParser(description="Check Odoo navigation health")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--url", default=ODOO_URL, help=f"Odoo URL (default: {ODOO_URL})")
    parser.add_argument("--db", default=ODOO_DB, help=f"Database (default: {ODOO_DB})")
    parser.add_argument("--user", "-u", default=ODOO_USER, help=f"User (default: {ODOO_USER})")
    parser.add_argument("--password", "-p", default=ODOO_PASSWORD, help="Password")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    if not args.password:
        console.print("[red]ERROR: ODOO_PASSWORD environment variable or --password required[/red]")
        sys.exit(1)

    console.print(f"\n[bold]Navigation Health Check[/bold]")
    console.print(f"URL: {args.url}")
    console.print(f"Database: {args.db}")
    console.print("")

    checker = OdooNavChecker(args.url, args.db, args.user, args.password)

    # Login
    if not checker.login():
        console.print("[red]Failed to login - aborting health check[/red]")
        sys.exit(1)

    # Run checks
    results = checker.check_all_menus(verbose=args.verbose)

    # Output
    if args.json:
        output = [
            {
                "menu": r.menu_name,
                "status": r.status.value,
                "status_code": r.status_code,
                "message": r.message,
                "has_data": r.has_data,
                "response_time_ms": r.response_time_ms,
            }
            for r in results
        ]
        print(json.dumps(output, indent=2))
    else:
        print_results_table(results)

    # Summary
    ok, warn, error, skipped = summarize_results(results)

    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  [green]OK: {ok}[/green]")
    console.print(f"  [yellow]Warnings: {warn}[/yellow]")
    console.print(f"  [red]Errors: {error}[/red]")
    console.print(f"  [dim]Skipped: {skipped}[/dim]")

    # Exit code
    if error > 0:
        console.print("\n[red]Health check FAILED - errors detected[/red]")
        sys.exit(1)
    elif warn > 0:
        console.print("\n[yellow]Health check completed with warnings[/yellow]")
        sys.exit(0)
    else:
        console.print("\n[green]Health check PASSED[/green]")
        sys.exit(0)


if __name__ == "__main__":
    main()

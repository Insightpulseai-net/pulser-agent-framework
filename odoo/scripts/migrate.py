#!/usr/bin/env python3
"""
Odoo Migration Script for Concur-Style T&E Suite
=================================================

This script handles:
- Upgrading base Odoo modules
- Installing/upgrading OCA modules for finance/expense
- Installing/upgrading Smart Delta (ipai_*) modules

Usage:
    python migrate.py                    # Migrate all modules
    python migrate.py --module ipai_expense_core  # Migrate specific module
    python migrate.py --list             # List installed modules
    python migrate.py --dry-run          # Show what would be migrated

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
from typing import Optional
from pathlib import Path

try:
    import odoorpc
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

# Module lists for Concur-style T&E suite
BASE_MODULES = [
    "base",
    "mail",
    "contacts",
    "hr",
    "hr_expense",
    "account",
    "account_accountant",
    "project",
    "documents",
    "approvals",
]

OCA_MODULES = [
    # Accounting
    "account_financial_report",
    "account_move_line_purchase_info",
    "account_invoice_view_payment",
    # HR & Expense
    "hr_expense_cancel",
    "hr_expense_advance_clearing",
    "hr_expense_payment",
    # Project & Timesheet
    "project_task_default_stage",
    "project_timeline",
    # Documents
    "document_page",
    "document_page_approval",
]

SMART_DELTA_MODULES = [
    "ipai_finance_ppm",
    "ipai_expense_core",
    "ipai_travel_advance",
    "ipai_cash_advance",
    "ipai_card_reconciliation",
]

ALL_MODULES = BASE_MODULES + OCA_MODULES + SMART_DELTA_MODULES

# Console for rich output
console = Console()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("migrate.log"),
    ]
)
logger = logging.getLogger(__name__)


class OdooMigrator:
    """Handles Odoo module migrations."""

    def __init__(self, url: str, db: str, user: str, password: str):
        self.url = url
        self.db = db
        self.user = user
        self.password = password
        self.odoo: Optional[odoorpc.ODOO] = None

    def connect(self) -> bool:
        """Establish connection to Odoo."""
        try:
            # Parse URL
            if self.url.startswith("https://"):
                host = self.url.replace("https://", "")
                port = 443
                protocol = "jsonrpc+ssl"
            elif self.url.startswith("http://"):
                host = self.url.replace("http://", "")
                port = 8069
                protocol = "jsonrpc"
            else:
                host = self.url
                port = 8069
                protocol = "jsonrpc"

            # Remove port from host if present
            if ":" in host:
                host, port_str = host.split(":")
                port = int(port_str)

            console.print(f"[cyan]Connecting to {host}:{port}...[/cyan]")

            self.odoo = odoorpc.ODOO(host, port=port, protocol=protocol)
            self.odoo.login(self.db, self.user, self.password)

            console.print(f"[green]Connected to Odoo {self.odoo.version}[/green]")
            logger.info(f"Connected to Odoo at {self.url}, version {self.odoo.version}")
            return True

        except Exception as e:
            console.print(f"[red]Failed to connect: {e}[/red]")
            logger.error(f"Connection failed: {e}")
            return False

    def list_modules(self, filter_installed: bool = True) -> list:
        """List installed or available modules."""
        if not self.odoo:
            return []

        Module = self.odoo.env["ir.module.module"]

        if filter_installed:
            domain = [("state", "=", "installed")]
        else:
            domain = []

        module_ids = Module.search(domain)
        modules = Module.browse(module_ids)

        return [
            {
                "name": m.name,
                "shortdesc": m.shortdesc or "",
                "state": m.state,
                "installed_version": m.installed_version or "",
            }
            for m in modules
        ]

    def is_module_installed(self, module_name: str) -> bool:
        """Check if a module is installed."""
        if not self.odoo:
            return False

        Module = self.odoo.env["ir.module.module"]
        module_ids = Module.search([
            ("name", "=", module_name),
            ("state", "=", "installed"),
        ])
        return len(module_ids) > 0

    def is_module_available(self, module_name: str) -> bool:
        """Check if a module is available (in addons path)."""
        if not self.odoo:
            return False

        Module = self.odoo.env["ir.module.module"]
        module_ids = Module.search([("name", "=", module_name)])
        return len(module_ids) > 0

    def install_module(self, module_name: str) -> bool:
        """Install a module."""
        if not self.odoo:
            return False

        try:
            Module = self.odoo.env["ir.module.module"]
            module_ids = Module.search([("name", "=", module_name)])

            if not module_ids:
                console.print(f"[yellow]Module {module_name} not found in addons path[/yellow]")
                logger.warning(f"Module {module_name} not found")
                return False

            module = Module.browse(module_ids[0])

            if module.state == "installed":
                console.print(f"[green]Module {module_name} already installed[/green]")
                return True

            console.print(f"[cyan]Installing {module_name}...[/cyan]")
            module.button_immediate_install()
            logger.info(f"Installed module: {module_name}")

            return True

        except Exception as e:
            console.print(f"[red]Failed to install {module_name}: {e}[/red]")
            logger.error(f"Failed to install {module_name}: {e}")
            return False

    def upgrade_module(self, module_name: str) -> bool:
        """Upgrade a module."""
        if not self.odoo:
            return False

        try:
            Module = self.odoo.env["ir.module.module"]
            module_ids = Module.search([
                ("name", "=", module_name),
                ("state", "=", "installed"),
            ])

            if not module_ids:
                console.print(f"[yellow]Module {module_name} not installed, attempting install...[/yellow]")
                return self.install_module(module_name)

            module = Module.browse(module_ids[0])
            console.print(f"[cyan]Upgrading {module_name}...[/cyan]")
            module.button_immediate_upgrade()
            logger.info(f"Upgraded module: {module_name}")

            return True

        except Exception as e:
            console.print(f"[red]Failed to upgrade {module_name}: {e}[/red]")
            logger.error(f"Failed to upgrade {module_name}: {e}")
            return False

    def migrate_all(self, dry_run: bool = False) -> dict:
        """Migrate all modules in the Concur suite."""
        results = {
            "base": [],
            "oca": [],
            "smart_delta": [],
            "failed": [],
            "skipped": [],
        }

        # Update module list first
        console.print("[cyan]Updating module list...[/cyan]")
        if not dry_run:
            try:
                self.odoo.env["ir.module.module"].update_list()
            except Exception as e:
                console.print(f"[yellow]Warning: Could not update module list: {e}[/yellow]")

        all_module_groups = [
            ("base", BASE_MODULES),
            ("oca", OCA_MODULES),
            ("smart_delta", SMART_DELTA_MODULES),
        ]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            for group_name, modules in all_module_groups:
                task = progress.add_task(f"Processing {group_name} modules...", total=len(modules))

                for module_name in modules:
                    progress.update(task, description=f"Processing {module_name}...")

                    if dry_run:
                        if self.is_module_available(module_name):
                            if self.is_module_installed(module_name):
                                console.print(f"[blue]Would upgrade: {module_name}[/blue]")
                            else:
                                console.print(f"[blue]Would install: {module_name}[/blue]")
                            results[group_name].append(module_name)
                        else:
                            console.print(f"[yellow]Would skip (not available): {module_name}[/yellow]")
                            results["skipped"].append(module_name)
                    else:
                        if not self.is_module_available(module_name):
                            results["skipped"].append(module_name)
                        elif self.upgrade_module(module_name):
                            results[group_name].append(module_name)
                        else:
                            results["failed"].append(module_name)

                    progress.advance(task)

        return results


def print_module_list(modules: list):
    """Print modules in a nice table."""
    table = Table(title="Installed Modules")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Version", style="green")
    table.add_column("State", style="yellow")

    for m in sorted(modules, key=lambda x: x["name"]):
        table.add_row(
            m["name"],
            m["shortdesc"][:50] + "..." if len(m["shortdesc"]) > 50 else m["shortdesc"],
            m["installed_version"],
            m["state"],
        )

    console.print(table)


def print_migration_results(results: dict):
    """Print migration results summary."""
    console.print("\n[bold]Migration Results[/bold]\n")

    for group in ["base", "oca", "smart_delta"]:
        if results[group]:
            console.print(f"[green]{group.upper()} modules migrated:[/green]")
            for m in results[group]:
                console.print(f"  - {m}")

    if results["skipped"]:
        console.print(f"\n[yellow]Skipped (not available):[/yellow]")
        for m in results["skipped"]:
            console.print(f"  - {m}")

    if results["failed"]:
        console.print(f"\n[red]Failed:[/red]")
        for m in results["failed"]:
            console.print(f"  - {m}")


def main():
    parser = argparse.ArgumentParser(description="Odoo Migration Script for Concur Suite")
    parser.add_argument("--module", "-m", help="Specific module to migrate")
    parser.add_argument("--list", "-l", action="store_true", help="List installed modules")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would be migrated")
    parser.add_argument("--url", default=ODOO_URL, help=f"Odoo URL (default: {ODOO_URL})")
    parser.add_argument("--db", default=ODOO_DB, help=f"Database name (default: {ODOO_DB})")
    parser.add_argument("--user", "-u", default=ODOO_USER, help=f"Username (default: {ODOO_USER})")
    parser.add_argument("--password", "-p", default=ODOO_PASSWORD, help="Password")

    args = parser.parse_args()

    # Validate password
    if not args.password:
        console.print("[red]ERROR: ODOO_PASSWORD environment variable or --password required[/red]")
        sys.exit(1)

    # Create migrator
    migrator = OdooMigrator(args.url, args.db, args.user, args.password)

    # Connect
    if not migrator.connect():
        sys.exit(1)

    # Handle commands
    if args.list:
        modules = migrator.list_modules()
        print_module_list(modules)
    elif args.module:
        if args.dry_run:
            console.print(f"[blue]Would migrate: {args.module}[/blue]")
        else:
            success = migrator.upgrade_module(args.module)
            if not success:
                sys.exit(1)
    else:
        results = migrator.migrate_all(dry_run=args.dry_run)
        print_migration_results(results)

        if results["failed"]:
            console.print("\n[red]Some modules failed to migrate![/red]")
            sys.exit(1)
        else:
            console.print("\n[green]Migration completed successfully![/green]")


if __name__ == "__main__":
    main()

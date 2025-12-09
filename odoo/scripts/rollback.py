#!/usr/bin/env python3
"""
Rollback Script for Concur Suite
================================

Restores the database and container images to a previous known-good state.

Usage:
    python rollback.py --latest           # Restore most recent snapshot
    python rollback.py --snapshot <id>    # Restore specific snapshot
    python rollback.py --list             # List available snapshots
    python rollback.py --dry-run          # Show what would be restored

Environment Variables:
    DATABASE_URL    - PostgreSQL connection string
    BACKUP_DIR      - Directory containing backups (default: /var/backups/odoo)
    DO_SPACES_*     - DigitalOcean Spaces credentials (optional)
"""

import os
import sys
import argparse
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.table import Table
except ImportError:
    load_dotenv = lambda: None
    Console = None

load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "")
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "/var/backups/odoo"))
COMPOSE_FILE = os.getenv("COMPOSE_FILE", "infra/docker-compose.odoo.yml")

# Console
console = Console() if Console else None


@dataclass
class Snapshot:
    """A backup snapshot."""
    id: str
    timestamp: datetime
    db_backup_path: Optional[Path]
    image_manifest: Optional[Dict]
    size_bytes: int
    notes: str


def log(message: str, style: str = ""):
    """Print a message with optional styling."""
    if console:
        console.print(f"[{style}]{message}[/{style}]" if style else message)
    else:
        print(message)


def run_command(cmd: List[str], dry_run: bool = False, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a shell command."""
    log(f"  $ {' '.join(cmd)}", "dim")

    if dry_run:
        return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")

    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        check=False,
    )


def list_snapshots() -> List[Snapshot]:
    """List available backup snapshots."""
    snapshots = []

    if not BACKUP_DIR.exists():
        log(f"Backup directory not found: {BACKUP_DIR}", "yellow")
        return snapshots

    # Look for backup files
    for backup_file in sorted(BACKUP_DIR.glob("*.sql.gz"), reverse=True):
        # Parse timestamp from filename (format: odoo_YYYYMMDD_HHMMSS.sql.gz)
        name = backup_file.stem.replace(".sql", "")
        parts = name.split("_")

        if len(parts) >= 3:
            try:
                date_str = parts[1]
                time_str = parts[2] if len(parts) > 2 else "000000"
                timestamp = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
            except ValueError:
                timestamp = datetime.fromtimestamp(backup_file.stat().st_mtime)
        else:
            timestamp = datetime.fromtimestamp(backup_file.stat().st_mtime)

        # Look for associated manifest
        manifest_path = backup_file.with_suffix(".manifest.json")
        manifest = None
        if manifest_path.exists():
            try:
                with open(manifest_path) as f:
                    manifest = json.load(f)
            except Exception:
                pass

        snapshots.append(Snapshot(
            id=backup_file.stem.replace(".sql", ""),
            timestamp=timestamp,
            db_backup_path=backup_file,
            image_manifest=manifest,
            size_bytes=backup_file.stat().st_size,
            notes=manifest.get("notes", "") if manifest else "",
        ))

    return snapshots


def print_snapshots(snapshots: List[Snapshot]):
    """Print snapshot list in a table."""
    if not snapshots:
        log("No snapshots found.", "yellow")
        return

    if console:
        table = Table(title="Available Snapshots")
        table.add_column("ID", style="cyan")
        table.add_column("Timestamp", style="green")
        table.add_column("Size", justify="right")
        table.add_column("Notes")

        for s in snapshots[:20]:  # Show last 20
            size_mb = s.size_bytes / (1024 * 1024)
            table.add_row(
                s.id,
                s.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                f"{size_mb:.1f} MB",
                s.notes[:40] + "..." if len(s.notes) > 40 else s.notes,
            )

        console.print(table)
    else:
        print("\nAvailable Snapshots:")
        for s in snapshots[:20]:
            size_mb = s.size_bytes / (1024 * 1024)
            print(f"  {s.id} | {s.timestamp} | {size_mb:.1f} MB | {s.notes}")


def restore_database(snapshot: Snapshot, dry_run: bool = False) -> bool:
    """Restore database from snapshot."""
    if not snapshot.db_backup_path or not snapshot.db_backup_path.exists():
        log("Database backup file not found!", "red")
        return False

    log(f"\nRestoring database from: {snapshot.db_backup_path}", "cyan")

    # Parse database connection
    # Expected format: postgresql://user:pass@host:port/dbname
    if DATABASE_URL:
        # Extract components using simple parsing
        # This is simplified; in production use urllib.parse
        db_name = DATABASE_URL.split("/")[-1].split("?")[0]
        db_host = DATABASE_URL.split("@")[1].split(":")[0] if "@" in DATABASE_URL else "localhost"
    else:
        db_name = os.getenv("ODOO_DB", "odoo")
        db_host = os.getenv("POSTGRES_HOST", "localhost")

    log(f"  Target database: {db_name} on {db_host}")

    if dry_run:
        log("  [DRY RUN] Would restore database", "yellow")
        return True

    # Step 1: Stop Odoo to prevent writes
    log("\n1. Stopping Odoo service...", "cyan")
    run_command(["docker", "compose", "-f", COMPOSE_FILE, "stop", "odoo"], dry_run)

    # Step 2: Drop and recreate database
    log("\n2. Recreating database...", "cyan")

    # Use docker compose exec for postgres commands
    drop_cmd = [
        "docker", "compose", "-f", COMPOSE_FILE, "exec", "-T", "postgres",
        "psql", "-U", "postgres", "-c", f"DROP DATABASE IF EXISTS {db_name};"
    ]
    run_command(drop_cmd, dry_run)

    create_cmd = [
        "docker", "compose", "-f", COMPOSE_FILE, "exec", "-T", "postgres",
        "psql", "-U", "postgres", "-c", f"CREATE DATABASE {db_name};"
    ]
    run_command(create_cmd, dry_run)

    # Step 3: Restore from backup
    log("\n3. Restoring from backup...", "cyan")

    # Decompress and restore
    backup_path = str(snapshot.db_backup_path)

    if backup_path.endswith(".gz"):
        restore_cmd = f"gunzip -c {backup_path} | docker compose -f {COMPOSE_FILE} exec -T postgres psql -U postgres -d {db_name}"
    else:
        restore_cmd = f"cat {backup_path} | docker compose -f {COMPOSE_FILE} exec -T postgres psql -U postgres -d {db_name}"

    result = subprocess.run(restore_cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        log(f"  Restore failed: {result.stderr}", "red")
        return False

    log("  Database restored successfully", "green")

    # Step 4: Start Odoo
    log("\n4. Starting Odoo service...", "cyan")
    run_command(["docker", "compose", "-f", COMPOSE_FILE, "start", "odoo"], dry_run)

    return True


def restore_images(snapshot: Snapshot, dry_run: bool = False) -> bool:
    """Restore container images from manifest."""
    if not snapshot.image_manifest:
        log("No image manifest found, skipping image restore", "yellow")
        return True

    log("\nRestoring container images...", "cyan")

    images = snapshot.image_manifest.get("images", {})

    for service, image_tag in images.items():
        log(f"  Pulling {service}: {image_tag}")

        if not dry_run:
            result = run_command(["docker", "pull", image_tag], dry_run, capture=True)
            if result.returncode != 0:
                log(f"  Failed to pull {image_tag}", "red")

    return True


def create_pre_rollback_snapshot(dry_run: bool = False) -> Optional[Snapshot]:
    """Create a snapshot before rollback for safety."""
    log("\nCreating pre-rollback snapshot...", "cyan")

    if dry_run:
        log("  [DRY RUN] Would create pre-rollback snapshot", "yellow")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"pre_rollback_{timestamp}.sql.gz"

    # Ensure backup directory exists
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Create backup using pg_dump
    db_name = os.getenv("ODOO_DB", "odoo")

    dump_cmd = f"docker compose -f {COMPOSE_FILE} exec -T postgres pg_dump -U postgres {db_name} | gzip > {backup_path}"
    result = subprocess.run(dump_cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        log(f"  Warning: Pre-rollback snapshot failed: {result.stderr}", "yellow")
        return None

    log(f"  Created: {backup_path}", "green")

    return Snapshot(
        id=f"pre_rollback_{timestamp}",
        timestamp=datetime.now(),
        db_backup_path=backup_path,
        image_manifest=None,
        size_bytes=backup_path.stat().st_size if backup_path.exists() else 0,
        notes="Pre-rollback safety snapshot",
    )


def perform_rollback(snapshot: Snapshot, dry_run: bool = False) -> bool:
    """Perform full rollback to snapshot."""
    log(f"\n{'[DRY RUN] ' if dry_run else ''}Rolling back to: {snapshot.id}", "bold cyan")
    log(f"  Timestamp: {snapshot.timestamp}")
    log(f"  Database: {snapshot.db_backup_path}")

    if not dry_run:
        # Create safety snapshot first
        create_pre_rollback_snapshot(dry_run)

    # Restore database
    if not restore_database(snapshot, dry_run):
        log("\nRollback FAILED at database restore step", "red")
        return False

    # Restore images if available
    if not restore_images(snapshot, dry_run):
        log("\nWarning: Image restore had issues", "yellow")

    log("\n" + "=" * 50, "green")
    log("Rollback completed successfully!", "bold green")
    log("=" * 50, "green")

    return True


def main():
    parser = argparse.ArgumentParser(description="Rollback Concur Suite to previous state")
    parser.add_argument("--latest", action="store_true", help="Restore most recent snapshot")
    parser.add_argument("--snapshot", "-s", help="Specific snapshot ID to restore")
    parser.add_argument("--list", "-l", action="store_true", help="List available snapshots")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would be done")

    args = parser.parse_args()

    # List snapshots
    if args.list:
        snapshots = list_snapshots()
        print_snapshots(snapshots)
        return

    # Find snapshot to restore
    snapshot = None

    if args.latest:
        snapshots = list_snapshots()
        if not snapshots:
            log("No snapshots available", "red")
            sys.exit(1)
        snapshot = snapshots[0]

    elif args.snapshot:
        snapshots = list_snapshots()
        for s in snapshots:
            if s.id == args.snapshot or args.snapshot in s.id:
                snapshot = s
                break

        if not snapshot:
            log(f"Snapshot not found: {args.snapshot}", "red")
            log("Use --list to see available snapshots")
            sys.exit(1)

    else:
        parser.print_help()
        return

    # Confirm
    if not args.dry_run:
        log(f"\nAbout to rollback to: {snapshot.id}", "yellow")
        log(f"  Timestamp: {snapshot.timestamp}")
        log(f"  This will REPLACE the current database!", "red")

        try:
            confirm = input("\nType 'ROLLBACK' to confirm: ")
            if confirm != "ROLLBACK":
                log("Rollback cancelled", "yellow")
                sys.exit(0)
        except KeyboardInterrupt:
            log("\nRollback cancelled", "yellow")
            sys.exit(0)

    # Perform rollback
    success = perform_rollback(snapshot, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Checklist Validator for Go-Live Procedures
===========================================

Parses markdown checklist files and ensures all required checkboxes are checked.
Used by `make go-live` to block deployment if critical items are missing.

Usage:
    python validate_checklists.py /path/to/checklists
    python validate_checklists.py --file CONCUR_SUITE_GO_LIVE.md
    python validate_checklists.py --strict  # Fail on any unchecked items

Exit codes:
    0 - All required items checked
    1 - Missing required items
    2 - File not found or parse error
"""

import os
import sys
import argparse
import re
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    Console = None


class Priority(Enum):
    CRITICAL = "CRITICAL"
    REQUIRED = "REQUIRED"
    RECOMMENDED = "RECOMMENDED"
    OPTIONAL = "OPTIONAL"


@dataclass
class ChecklistItem:
    """A single checklist item."""
    text: str
    checked: bool
    priority: Priority
    section: str
    line_number: int


@dataclass
class ChecklistFile:
    """Parsed checklist file."""
    path: Path
    title: str
    items: List[ChecklistItem]
    parse_errors: List[str]


# Keywords that indicate priority level in item text
PRIORITY_KEYWORDS = {
    Priority.CRITICAL: ["CRITICAL", "BLOCKER", "MUST"],
    Priority.REQUIRED: ["REQUIRED", "MANDATORY"],
    Priority.RECOMMENDED: ["RECOMMENDED", "SHOULD"],
    Priority.OPTIONAL: ["OPTIONAL", "NICE-TO-HAVE"],
}


def detect_priority(text: str) -> Priority:
    """Detect priority from item text."""
    upper_text = text.upper()

    for priority, keywords in PRIORITY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in upper_text:
                return priority

    # Default priority based on common patterns
    if "security" in text.lower() or "backup" in text.lower():
        return Priority.CRITICAL
    if "test" in text.lower() or "verify" in text.lower():
        return Priority.REQUIRED

    return Priority.REQUIRED


def parse_checklist_file(file_path: Path) -> ChecklistFile:
    """Parse a markdown checklist file."""
    items = []
    errors = []
    current_section = "General"
    title = file_path.stem

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        return ChecklistFile(
            path=file_path,
            title=title,
            items=[],
            parse_errors=[f"Failed to read file: {e}"],
        )

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        # Extract title from first H1
        if line.startswith("# ") and title == file_path.stem:
            title = line[2:].strip()
            continue

        # Track section headers
        if line.startswith("## "):
            current_section = line[3:].strip()
            continue

        # Parse checkbox items: - [ ] or - [x]
        checkbox_match = re.match(r"^[-*]\s*\[([ xX])\]\s*(.+)$", line)
        if checkbox_match:
            checked = checkbox_match.group(1).lower() == "x"
            text = checkbox_match.group(2).strip()
            priority = detect_priority(text)

            items.append(ChecklistItem(
                text=text,
                checked=checked,
                priority=priority,
                section=current_section,
                line_number=line_num,
            ))

    return ChecklistFile(
        path=file_path,
        title=title,
        items=items,
        parse_errors=errors,
    )


def validate_checklist(checklist: ChecklistFile, strict: bool = False) -> Tuple[bool, List[ChecklistItem]]:
    """
    Validate a checklist.

    Returns:
        (passed, missing_items)
    """
    missing = []

    for item in checklist.items:
        if not item.checked:
            # In strict mode, all items must be checked
            if strict:
                missing.append(item)
            # Otherwise, only CRITICAL and REQUIRED must be checked
            elif item.priority in [Priority.CRITICAL, Priority.REQUIRED]:
                missing.append(item)

    passed = len(missing) == 0
    return passed, missing


def print_results(checklists: List[ChecklistFile], missing_by_file: Dict[Path, List[ChecklistItem]], use_rich: bool = True):
    """Print validation results."""
    if use_rich and Console:
        console = Console()

        for checklist in checklists:
            missing = missing_by_file.get(checklist.path, [])

            if missing:
                console.print(f"\n[red]FAILED:[/red] {checklist.title}")
                console.print(f"  File: {checklist.path}")

                table = Table(show_header=True)
                table.add_column("Line", justify="right", width=6)
                table.add_column("Priority", width=12)
                table.add_column("Section", width=20)
                table.add_column("Item")

                for item in missing:
                    priority_color = {
                        Priority.CRITICAL: "red",
                        Priority.REQUIRED: "yellow",
                        Priority.RECOMMENDED: "cyan",
                        Priority.OPTIONAL: "dim",
                    }.get(item.priority, "white")

                    table.add_row(
                        str(item.line_number),
                        f"[{priority_color}]{item.priority.value}[/{priority_color}]",
                        item.section[:18] + ".." if len(item.section) > 20 else item.section,
                        item.text[:50] + "..." if len(item.text) > 50 else item.text,
                    )

                console.print(table)
            else:
                console.print(f"\n[green]PASSED:[/green] {checklist.title}")

            # Summary
            total = len(checklist.items)
            checked = sum(1 for i in checklist.items if i.checked)
            console.print(f"  Progress: {checked}/{total} items checked")

    else:
        # Plain text output
        for checklist in checklists:
            missing = missing_by_file.get(checklist.path, [])

            if missing:
                print(f"\nFAILED: {checklist.title}")
                print(f"  File: {checklist.path}")
                print(f"  Missing items:")
                for item in missing:
                    print(f"    Line {item.line_number}: [{item.priority.value}] {item.text}")
            else:
                print(f"\nPASSED: {checklist.title}")

            total = len(checklist.items)
            checked = sum(1 for i in checklist.items if i.checked)
            print(f"  Progress: {checked}/{total} items checked")


def main():
    parser = argparse.ArgumentParser(description="Validate go-live checklists")
    parser.add_argument("path", nargs="?", default=".", help="Checklist directory or file")
    parser.add_argument("--file", "-f", help="Specific checklist file to validate")
    parser.add_argument("--strict", "-s", action="store_true", help="All items must be checked")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only output errors")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")

    args = parser.parse_args()

    use_rich = Console is not None and not args.no_color

    # Find checklist files
    files_to_check = []

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {args.file}")
            sys.exit(2)
        files_to_check.append(file_path)
    else:
        base_path = Path(args.path)
        if base_path.is_file():
            files_to_check.append(base_path)
        elif base_path.is_dir():
            # Look for markdown files with checklist patterns
            for pattern in ["*.md", "**/*.md"]:
                for md_file in base_path.glob(pattern):
                    # Only include files that look like checklists
                    if any(x in md_file.name.upper() for x in ["CHECKLIST", "GO_LIVE", "UAT", "IMPLEMENTATION"]):
                        files_to_check.append(md_file)
        else:
            print(f"Error: Path not found: {args.path}")
            sys.exit(2)

    if not files_to_check:
        print("No checklist files found.")
        sys.exit(0)

    # Parse and validate each file
    checklists = []
    missing_by_file = {}
    all_passed = True

    for file_path in files_to_check:
        checklist = parse_checklist_file(file_path)
        checklists.append(checklist)

        if checklist.parse_errors:
            print(f"Warning: Parse errors in {file_path}:")
            for err in checklist.parse_errors:
                print(f"  {err}")

        passed, missing = validate_checklist(checklist, strict=args.strict)

        if not passed:
            all_passed = False
            missing_by_file[file_path] = missing

    # Print results
    if not args.quiet or not all_passed:
        print_results(checklists, missing_by_file, use_rich=use_rich)

    # Summary
    total_files = len(checklists)
    passed_files = total_files - len(missing_by_file)

    if use_rich and Console:
        console = Console()
        console.print(f"\n[bold]Summary:[/bold] {passed_files}/{total_files} checklists passed")
    else:
        print(f"\nSummary: {passed_files}/{total_files} checklists passed")

    # Exit code
    if all_passed:
        if use_rich and Console:
            Console().print("[green]All required checklist items are complete![/green]")
        else:
            print("All required checklist items are complete!")
        sys.exit(0)
    else:
        if use_rich and Console:
            Console().print("[red]Some required checklist items are incomplete![/red]")
        else:
            print("Some required checklist items are incomplete!")
        sys.exit(1)


if __name__ == "__main__":
    main()

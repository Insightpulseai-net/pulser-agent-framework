#!/usr/bin/env python3
"""
Parity Checklist Generator
===========================
Generates parity checklists, matrices, and spec-kit documents from YAML definitions.

Usage:
    python paritygen.py parity.yml [profile.yml] [--min-score=0.85]

Outputs:
    - out/PARITY_CHECKLIST.md  (human-readable checklist)
    - out/parity_matrix.csv     (importable to Sheets/Supabase)
    - out/summary.json          (CI/CD integration)
    - out/spec-kit/*.md         (spec-driven docs)
"""

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    print("Missing dependency: pyyaml. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

try:
    from jinja2 import Environment, FileSystemLoader
    HAS_JINJA = True
except ImportError:
    HAS_JINJA = False
    print("Optional: Install jinja2 for template support: pip install jinja2", file=sys.stderr)

ROOT = Path(__file__).parent.resolve()


def load_yaml(path: str) -> Dict[str, Any]:
    """Load and parse YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dir(p: Path) -> None:
    """Create directory if it doesn't exist."""
    p.mkdir(parents=True, exist_ok=True)


def score_item(item: Dict[str, Any], scoring: Dict[str, Any]) -> float:
    """Calculate score for a single item."""
    weight = scoring["weights"].get(item["priority"], 1)
    points = scoring["status_points"].get(item["status"], 0)
    return weight * points


def weighted_max(item: Dict[str, Any], scoring: Dict[str, Any]) -> float:
    """Calculate maximum possible score for an item."""
    return scoring["weights"].get(item["priority"], 1) * 1.0


def status_emoji(status: str) -> str:
    """Return emoji for status."""
    return {
        "done": "✅",
        "partial": "🟡",
        "planned": "🧭",
        "no": "❌",
    }.get(status, "⬜")


def md_escape(s: str) -> str:
    """Escape markdown special characters."""
    return str(s).replace("|", "\\|").replace("\n", " ")


def generate_markdown(
    items: List[Dict[str, Any]],
    groups: Dict[str, str],
    target_name: str,
    ratio: float,
    total: float,
    total_max: float,
) -> str:
    """Generate markdown checklist."""
    lines = [
        f"# Parity Checklist — {target_name}",
        "",
        f"**Parity Score:** {ratio*100:.1f}% ({total:.2f}/{total_max:.2f})",
        "",
        "Legend: ✅ done · 🟡 partial · 🧭 planned · ❌ no",
        "",
    ]

    # Group items
    by_group: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        group = item["group"]
        if group not in by_group:
            by_group[group] = []
        by_group[group].append(item)

    for group_id, group_items in by_group.items():
        group_title = groups.get(group_id, group_id)
        lines.append(f"## {group_title}")
        lines.append("")

        for it in sorted(group_items, key=lambda x: (x["priority"], x["id"])):
            emoji = status_emoji(it["status"])
            lines.append(f"### {emoji} `{it['id']}` — {it['name']}")
            lines.append("")
            lines.append(f"- **Status:** `{it['status']}`")
            lines.append(f"- **Priority:** `{it['priority']}`")
            lines.append(f"- **Owner:** `{it.get('owner', '-')}`")

            if it.get("framework_labels"):
                lines.append(f"- **Frameworks:** {', '.join(it['framework_labels'])}")

            if it.get("acceptance"):
                lines.append("- **Acceptance Criteria:**")
                for acc in it["acceptance"]:
                    lines.append(f"  - {acc}")

            if it.get("notes"):
                lines.append(f"- **Notes:** {it['notes']}")

            if it.get("evidence"):
                lines.append("- **Evidence:**")
                for ev in it["evidence"]:
                    lines.append(f"  - {ev}")

            lines.append("")

    return "\n".join(lines)


def generate_csv(items: List[Dict[str, Any]], output_path: Path) -> None:
    """Generate CSV matrix."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "group", "group_title", "name", "priority", "status",
            "owner", "score", "score_max", "frameworks", "notes", "evidence"
        ])
        for x in items:
            writer.writerow([
                x["id"],
                x["group"],
                x.get("group_title", x["group"]),
                x["name"],
                x["priority"],
                x["status"],
                x.get("owner", ""),
                f"{x['score']:.2f}",
                f"{x['score_max']:.2f}",
                " | ".join(x.get("framework_labels", [])),
                x.get("notes", ""),
                " | ".join(x.get("evidence", [])),
            ])


def generate_speckit_tasks(
    items: List[Dict[str, Any]],
    target_name: str,
    ratio: float,
    output_path: Path,
) -> None:
    """Generate spec-kit tasks.md."""
    lines = [
        "# tasks.md — Parity Closure Plan",
        "",
        f"Target: **{target_name}**",
        f"Current parity score: **{ratio*100:.1f}%**",
        "",
        "## Tasks by Priority",
        "",
    ]

    # Sort by priority (core first) then status
    priority_order = {"core": 0, "important": 1, "nice": 2}
    status_order = {"planned": 0, "partial": 1, "done": 2, "no": 3}

    sorted_items = sorted(
        items,
        key=lambda x: (priority_order.get(x["priority"], 9), status_order.get(x["status"], 9))
    )

    for it in sorted_items:
        checkbox = "[x]" if it["status"] == "done" else "[ ]"
        lines.append(f"- {checkbox} **{it['id']}** — {it['name']}")
        lines.append(f"  - Priority: `{it['priority']}` | Status: `{it['status']}` | Owner: `{it.get('owner', '-')}`")

        if it.get("acceptance"):
            lines.append("  - Acceptance:")
            for acc in it["acceptance"][:3]:  # Limit to first 3
                lines.append(f"    - {acc}")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def generate_speckit_constitution(target_name: str, output_path: Path) -> None:
    """Generate spec-kit constitution.md."""
    content = f"""# Constitution — {target_name}

## Purpose
This document defines the guiding principles and constraints for the AFC Close Manager implementation.

## Core Principles

1. **Audit-First Design**
   - Every transaction must be traceable
   - Immutable audit trails are non-negotiable
   - Evidence must be linked to actions

2. **Separation of Duties**
   - Four-eyes principle enforced at all levels
   - Conflicts detected and remediated
   - Emergency access is time-boxed and logged

3. **Compliance by Default**
   - Philippine BIR compliance built-in
   - SOX 404 controls embedded
   - COSO framework alignment

4. **Process Intelligence**
   - Measure what matters (cycle time, FPY)
   - Detect bottlenecks automatically
   - Recommend improvements continuously

## Constraints

- No retroactive changes to locked periods without audit trail
- No single-person approval for high-risk transactions
- No deployment without passing parity threshold (85%)
- No production access without quarterly review

## Success Criteria

- Parity score ≥ 85%
- Close cycle time reduction ≥ 20%
- First pass yield ≥ 90%
- Zero critical SoD violations
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate parity checklist artifacts")
    parser.add_argument("parity_file", help="Path to parity.yml")
    parser.add_argument("profile_file", nargs="?", help="Path to profile.yml (optional)")
    parser.add_argument("--min-score", type=float, help="Minimum parity score (CI gate)")
    parser.add_argument("--out-dir", default=str(ROOT / "out"), help="Output directory")
    args = parser.parse_args()

    # Load configuration
    parity = load_yaml(args.parity_file)
    scoring = parity.get("scoring", {
        "weights": {"core": 3, "important": 2, "nice": 1},
        "status_points": {"done": 1.0, "partial": 0.5, "planned": 0.2, "no": 0.0}
    })

    items = parity.get("items", [])
    groups = {g["id"]: g["title"] for g in parity.get("capability_groups", [])}
    frameworks = parity.get("frameworks", {})

    # Load profile overrides
    if args.profile_file:
        profile = load_yaml(args.profile_file)
    else:
        profile = {"target": {"name": "Default Target"}, "overrides": {}}

    overrides = profile.get("overrides", {})
    target_name = profile.get("target", {}).get("name", "Unknown")
    default_status = profile.get("target", {}).get("defaults", {}).get("status", "planned")
    default_owner = profile.get("target", {}).get("defaults", {}).get("owner", "platform")

    # Normalize items with profile overrides
    normalized: List[Dict[str, Any]] = []
    for it in items:
        it = dict(it)  # Copy
        ov = overrides.get(it["id"], {})

        it["status"] = ov.get("status", default_status)
        it["notes"] = ov.get("notes", "")
        it["evidence"] = ov.get("evidence", [])
        it["owner"] = ov.get("owner", it.get("owner", default_owner))
        it["group_title"] = groups.get(it["group"], it["group"])
        it["framework_labels"] = [
            frameworks[f]["label"]
            for f in it.get("frameworks", [])
            if f in frameworks
        ]
        it["score"] = score_item(it, scoring)
        it["score_max"] = weighted_max(it, scoring)

        normalized.append(it)

    # Calculate totals
    total = sum(x["score"] for x in normalized)
    total_max = sum(x["score_max"] for x in normalized)
    ratio = (total / total_max) if total_max else 0.0

    # Create output directory
    out_dir = Path(args.out_dir)
    ensure_dir(out_dir)

    # Generate markdown checklist
    md_content = generate_markdown(
        normalized, groups, target_name, ratio, total, total_max
    )
    (out_dir / "PARITY_CHECKLIST.md").write_text(md_content, encoding="utf-8")

    # Generate CSV matrix
    generate_csv(normalized, out_dir / "parity_matrix.csv")

    # Generate spec-kit documents
    speckit_dir = out_dir / "spec-kit"
    ensure_dir(speckit_dir)
    generate_speckit_tasks(normalized, target_name, ratio, speckit_dir / "tasks.md")
    generate_speckit_constitution(target_name, speckit_dir / "constitution.md")

    # Generate summary JSON
    summary = {
        "target": target_name,
        "parity_score": round(ratio, 4),
        "points": round(total, 2),
        "points_max": round(total_max, 2),
        "counts": {
            "done": sum(1 for x in normalized if x["status"] == "done"),
            "partial": sum(1 for x in normalized if x["status"] == "partial"),
            "planned": sum(1 for x in normalized if x["status"] == "planned"),
            "no": sum(1 for x in normalized if x["status"] == "no"),
        },
        "by_priority": {
            "core": sum(1 for x in normalized if x["priority"] == "core"),
            "important": sum(1 for x in normalized if x["priority"] == "important"),
            "nice": sum(1 for x in normalized if x["priority"] == "nice"),
        }
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    # Print summary
    print(f"[paritygen] target={target_name}")
    print(f"[paritygen] score={ratio:.1%} ({total:.2f}/{total_max:.2f})")
    print(f"[paritygen] items: {summary['counts']}")
    print(f"[paritygen] output: {out_dir}")

    # CI gate
    if args.min_score is not None and ratio < args.min_score:
        print(
            f"[paritygen] FAIL: score {ratio:.3f} < min {args.min_score:.3f}",
            file=sys.stderr
        )
        sys.exit(1)

    print("[paritygen] SUCCESS")


if __name__ == "__main__":
    main()

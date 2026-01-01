#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON Schema to Odoo Module Generator

Generates complete ipai_* Odoo 18 CE modules from JSON Schema specifications.
Deterministic, idempotent, and CI-ready.

Usage:
    python3 generators/schema_to_odoo.py --schema specs/ipai_example.schema.json --out addons

Convention:
    Schema file: specs/ipai_<name>.schema.json
    Output: addons/ipai_<name>/
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

AGPL_HEADER = """# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.en.html).
"""


def _stable_generated_timestamp() -> str:
    """
    Deterministic timestamp for reproducible builds.
    Uses SOURCE_DATE_EPOCH if set, otherwise epoch 0.
    """
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", "0") or "0")
    return dt.datetime.fromtimestamp(epoch, tz=dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _slugify(s: str) -> str:
    """Convert string to valid Python identifier."""
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "module"


def _titleize(module_name: str) -> str:
    """Convert module name to title: ipai_bir_2307 -> IPAI Bir 2307"""
    parts = module_name.split("_")
    return " ".join([p.upper() if i == 0 else p.capitalize() for i, p in enumerate(parts)])


def _odoo_model_name(module_name: str) -> str:
    """Convert module name to Odoo model: ipai_bir_2307 -> ipai.bir_2307"""
    suffix = module_name.removeprefix("ipai_")
    return f"ipai.{suffix}"


def _python_class_name(module_name: str) -> str:
    """Convert module name to Python class: ipai_bir_2307 -> IpaiBir2307"""
    parts = module_name.split("_")
    return "".join(p.capitalize() for p in parts)


def _safe_write(path: Path, content: str) -> None:
    """Write content to file, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _json_load(path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class FieldSpec:
    """Specification for an Odoo field."""
    name: str
    odoo_field: str
    required: bool
    string: str


def _map_jsonschema_property(name: str, prop: Dict[str, Any], required: bool) -> FieldSpec:
    """Map JSON Schema property to Odoo field specification."""
    t = prop.get("type")
    fmt = prop.get("format")

    string = prop.get("title") or name.replace("_", " ").title()

    # JSON Schema type to Odoo field mapping
    if t == "string" and fmt == "date":
        odoo_field = "fields.Date"
    elif t == "string" and fmt in ("date-time", "datetime"):
        odoo_field = "fields.Datetime"
    elif t == "string":
        odoo_field = "fields.Char"
    elif t == "number":
        odoo_field = "fields.Float"
    elif t == "integer":
        odoo_field = "fields.Integer"
    elif t == "boolean":
        odoo_field = "fields.Boolean"
    elif t == "array":
        odoo_field = "fields.Text"  # Serialize arrays as JSON
    else:
        odoo_field = "fields.Text"  # Default to Text for unknown types

    return FieldSpec(name=name, odoo_field=odoo_field, required=required, string=string)


def _extract_fields(schema: Dict[str, Any]) -> List[FieldSpec]:
    """Extract field specifications from JSON Schema."""
    if schema.get("type") != "object":
        raise ValueError("Schema must have top-level type=object")

    props = schema.get("properties")
    if not isinstance(props, dict) or not props:
        raise ValueError("Schema must define non-empty 'properties' object")

    required_set = set(schema.get("required") or [])
    fields: List[FieldSpec] = []

    for k in sorted(props.keys()):  # Deterministic ordering
        v = props[k]
        if not isinstance(v, dict):
            raise ValueError(f"Property '{k}' must be an object")
        fields.append(_map_jsonschema_property(k, v, required=(k in required_set)))

    return fields


def _manifest_py(module_name: str, title: str, summary: str, description: str,
                 depends: List[str], data_files: List[str]) -> str:
    """Generate __manifest__.py content."""
    gen_ts = _stable_generated_timestamp()
    return f'''# GENERATED FILE - DO NOT EDIT MANUALLY
# Source: JSON Schema -> Odoo module generator
# Generated: {gen_ts}
# Regenerate: python3 generators/schema_to_odoo.py --schema specs/{module_name}.schema.json --out addons

{{
    'name': '{title}',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': '{summary}',
    'description': """
{description}
    """,
    'author': 'InsightPulse AI',
    'website': 'https://insightpulseai.net',
    'license': 'AGPL-3',
    'depends': {depends!r},
    'data': {data_files!r},
    'installable': True,
    'application': False,
    'auto_install': False,
}}
'''


def _models_py(module_name: str, model: str, class_name: str, fields: List[FieldSpec]) -> str:
    """Generate model Python file."""
    gen_ts = _stable_generated_timestamp()

    lines = []
    for f in fields:
        req = ", required=True" if f.required else ""
        lines.append(f"    {f.name} = {f.odoo_field}(string={f.string!r}{req})")

    fields_block = "\n".join(lines) if lines else "    pass"

    field_names = [f.name for f in fields]
    required_fields = [f.name for f in fields if f.required]
    other_fields = [f.name for f in fields if not f.required]
    ordered_fields = required_fields + other_fields

    return f'''{AGPL_HEADER}# GENERATED FILE - DO NOT EDIT MANUALLY
# Source: JSON Schema -> Odoo model
# Generated: {gen_ts}
# Regenerate: python3 generators/schema_to_odoo.py --schema specs/{module_name}.schema.json --out addons

from odoo import api, fields, models


class {class_name}(models.Model):
    _name = "{model}"
    _description = "{class_name}"

{fields_block}

    name = fields.Char(string="Name", compute="_compute_name", store=True)

    @api.depends({", ".join([repr(f) for f in field_names])})
    def _compute_name(self):
        for rec in self:
            parts = []
            ordered = {ordered_fields!r}
            for field_name in ordered:
                val = rec[field_name]
                if val not in (False, None, ""):
                    parts.append(str(val))
            rec.name = " / ".join(parts)[:256] if parts else "{model}"
'''


def _views_xml(module_name: str, model: str, class_name: str, fields: List[FieldSpec]) -> str:
    """Generate views XML file."""
    gen_ts = _stable_generated_timestamp()
    model_id = model.replace(".", "_")
    action_id = f"action_{model_id}"
    menu_id = f"menu_{model_id}"
    root_menu_id = "menu_ipai_root"

    tree_fields = "\n".join([f'          <field name="{f.name}"/>' for f in fields[:8]])
    form_fields = "\n".join([f'              <field name="{f.name}"/>' for f in fields])

    return f'''<?xml version="1.0" encoding="utf-8"?>
<!-- GENERATED FILE - DO NOT EDIT MANUALLY
     Source: JSON Schema -> Odoo views
     Generated: {gen_ts}
     Regenerate: python3 generators/schema_to_odoo.py --schema specs/{module_name}.schema.json --out addons
-->
<odoo>
  <data>

    <menuitem id="{root_menu_id}" name="IPAI" sequence="10"/>

    <record id="view_{model_id}_tree" model="ir.ui.view">
      <field name="name">{model}.tree</field>
      <field name="model">{model}</field>
      <field name="arch" type="xml">
        <tree string="{class_name}">
          <field name="name"/>
{tree_fields}
        </tree>
      </field>
    </record>

    <record id="view_{model_id}_form" model="ir.ui.view">
      <field name="name">{model}.form</field>
      <field name="model">{model}</field>
      <field name="arch" type="xml">
        <form string="{class_name}">
          <sheet>
            <group>
              <field name="name" readonly="1"/>
{form_fields}
            </group>
          </sheet>
        </form>
      </field>
    </record>

    <record id="{action_id}" model="ir.actions.act_window">
      <field name="name">{class_name}</field>
      <field name="res_model">{model}</field>
      <field name="view_mode">tree,form</field>
    </record>

    <menuitem id="{menu_id}" name="{class_name}" parent="{root_menu_id}" action="{action_id}" sequence="20"/>

  </data>
</odoo>
'''


def _access_csv(module_name: str, model: str) -> str:
    """Generate security access CSV."""
    gen_ts = _stable_generated_timestamp()
    model_id = model.replace(".", "_")
    return f'''# GENERATED FILE - DO NOT EDIT MANUALLY
# Source: JSON Schema -> access CSV
# Generated: {gen_ts}
# Regenerate: python3 generators/schema_to_odoo.py --schema specs/{module_name}.schema.json --out addons

id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_{model_id}_user,access_{model_id}_user,model_{model_id},base.group_user,1,1,1,0
'''


def _readme_md(module_name: str, schema_path: str) -> str:
    """Generate README.md."""
    gen_ts = _stable_generated_timestamp()
    return f'''# {module_name}

Generated from JSON Schema.

- **Source**: `{schema_path}`
- **Generated**: `{gen_ts}`
- **Regenerate**:
  ```bash
  python3 generators/schema_to_odoo.py --schema {schema_path} --out addons
  ```

## Smart Delta Rule

This module is a delta-layer extension following the Smart Delta Framework:
- **Configure** native Odoo first
- Use **OCA modules** where available
- Only then add **ipai_*** custom code

Do not fork core/OCA modules; extend via `_inherit` as needed.
'''


def _tests_py(module_name: str, model: str, fields: List[FieldSpec]) -> str:
    """Generate test file."""
    gen_ts = _stable_generated_timestamp()

    # Build minimal create payload using required fields
    payload_lines = []
    for f in fields:
        if not f.required:
            continue
        if f.odoo_field.endswith("Date"):
            payload_lines.append(f'            "{f.name}": "2025-01-01",')
        elif f.odoo_field.endswith("Datetime"):
            payload_lines.append(f'            "{f.name}": "2025-01-01 00:00:00",')
        elif f.odoo_field.endswith("Float"):
            payload_lines.append(f'            "{f.name}": 1.0,')
        elif f.odoo_field.endswith("Integer"):
            payload_lines.append(f'            "{f.name}": 1,')
        elif f.odoo_field.endswith("Boolean"):
            payload_lines.append(f'            "{f.name}": True,')
        else:
            payload_lines.append(f'            "{f.name}": "test_value",')

    payload = "\n".join(payload_lines) if payload_lines else '            # No required fields'

    return f'''{AGPL_HEADER}# GENERATED FILE - DO NOT EDIT MANUALLY
# Source: JSON Schema -> Odoo tests
# Generated: {gen_ts}
# Regenerate: python3 generators/schema_to_odoo.py --schema specs/{module_name}.schema.json --out addons

from odoo.tests.common import TransactionCase


class TestGeneratedModel(TransactionCase):
    """Tests for generated model."""

    def test_create_record(self):
        """Test creating a record with required fields."""
        Model = self.env["{model}"]
        rec = Model.create({{
{payload}
        }})
        self.assertTrue(rec.id)
        self.assertTrue(rec.name)

    def test_name_computation(self):
        """Test that name field is computed correctly."""
        Model = self.env["{model}"]
        rec = Model.create({{
{payload}
        }})
        self.assertIsInstance(rec.name, str)
        self.assertTrue(len(rec.name) > 0)
'''


def generate(schema_path: Path, out_root: Path) -> Path:
    """Generate complete Odoo module from JSON Schema."""
    schema = _json_load(schema_path)

    base = schema_path.name
    # Convention: specs/ipai_<name>.schema.json -> module_name = ipai_<name>
    m = re.match(r"^(ipai_[a-zA-Z0-9_]+)\.schema\.json$", base)
    if not m:
        raise ValueError("Schema filename must match: ipai_<name>.schema.json (e.g., ipai_bir_2307.schema.json)")

    module_name = _slugify(m.group(1))
    if not module_name.startswith("ipai_"):
        raise ValueError("Module name must start with ipai_")

    title = schema.get("title") or _titleize(module_name)
    description = schema.get("description") or (schema.get("$comment") or "").strip() or f"Generated module for {module_name}."
    summary = (schema.get("title") or title)[:120]

    depends = schema.get("x_ipai_depends")
    if depends is None:
        depends = ["base"]
    if not isinstance(depends, list) or not all(isinstance(x, str) for x in depends):
        raise ValueError("Optional x_ipai_depends must be a list[str]")

    fields = _extract_fields(schema)
    model = _odoo_model_name(module_name)
    class_name = _python_class_name(module_name)

    module_dir = out_root / module_name

    # Overwrite for determinism
    if module_dir.exists():
        shutil.rmtree(module_dir)

    (module_dir / "models").mkdir(parents=True, exist_ok=True)
    (module_dir / "views").mkdir(parents=True, exist_ok=True)
    (module_dir / "security").mkdir(parents=True, exist_ok=True)
    (module_dir / "tests").mkdir(parents=True, exist_ok=True)
    (module_dir / "static" / "description").mkdir(parents=True, exist_ok=True)

    # Generate files
    _safe_write(module_dir / "__init__.py",
        "# GENERATED FILE - DO NOT EDIT MANUALLY\n# Source: JSON Schema -> module init\nfrom . import models\n")
    _safe_write(module_dir / "__manifest__.py",
        _manifest_py(module_name, title, summary, description, depends,
                     ["security/ir.model.access.csv", f"views/{module_name}_views.xml"]))
    _safe_write(module_dir / "README.md",
        _readme_md(module_name, str(schema_path)))
    _safe_write(module_dir / "models" / "__init__.py",
        "# GENERATED FILE - DO NOT EDIT MANUALLY\n# Source: JSON Schema -> models init\nfrom . import generated_model\n")
    _safe_write(module_dir / "models" / "generated_model.py",
        _models_py(module_name, model, class_name, fields))
    _safe_write(module_dir / "views" / f"{module_name}_views.xml",
        _views_xml(module_name, model, class_name, fields))
    _safe_write(module_dir / "security" / "ir.model.access.csv",
        _access_csv(module_name, model))
    _safe_write(module_dir / "tests" / "__init__.py",
        "# GENERATED FILE - DO NOT EDIT MANUALLY\n")
    _safe_write(module_dir / "tests" / "test_generated_model.py",
        _tests_py(module_name, model, fields))

    return module_dir


def main() -> None:
    """CLI entry point."""
    p = argparse.ArgumentParser(description="Generate Odoo module from JSON Schema")
    p.add_argument("--schema", required=True, help="Path to specs/ipai_<name>.schema.json")
    p.add_argument("--out", required=True, help="Output root directory (e.g., addons)")
    args = p.parse_args()

    schema_path = Path(args.schema).resolve()
    out_root = Path(args.out).resolve()

    if not schema_path.exists():
        raise SystemExit(f"Schema not found: {schema_path}")

    out_root.mkdir(parents=True, exist_ok=True)
    module_dir = generate(schema_path, out_root)
    print(f"Generated: {module_dir}")


if __name__ == "__main__":
    main()

# Phase 22: Custom Figma Plugin Specification
## pulser-figma-to-odoo - Design to Business Logic Code Generator

**Version:** 1.0.0
**Last Updated:** 2025-12-31
**Status:** Specification Complete, Ready for Implementation

---

## Executive Summary

This document specifies a custom Figma plugin that bridges design systems to Odoo 18 CE business logic code generation. Unlike generic design-to-code tools that only produce UI templates, this plugin generates complete Odoo modules including models, views, workflows, and compliance patterns.

### Differentiation from Existing Plugins

| Feature | Generic Plugins | pulser-figma-to-odoo |
|---------|-----------------|---------------------|
| Output | HTML/React/CSS only | Odoo Python + XML + tests |
| Business Logic | ❌ None | ✅ Models, constraints, workflows |
| Form Validation | ❌ Basic | ✅ BIR-compliant patterns |
| Database Schema | ❌ None | ✅ Supabase + Odoo ORM |
| Compliance | ❌ None | ✅ Audit trails, SoD, BIR |
| Full-Stack | ❌ Frontend only | ✅ UI + backend + database |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FIGMA DESIGN                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                │
│  │ Invoice │  │ Customer│  │ Tax Form│  │ Workflow│                │
│  │  Form   │  │  Card   │  │  1700   │  │  Wizard │                │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘                │
└───────┼────────────┼────────────┼────────────┼──────────────────────┘
        │            │            │            │
        ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────────┐
│               PULSER-FIGMA-TO-ODOO PLUGIN                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  TIER 1: Form Intelligence                                   │   │
│  │  - Field type detection (text, date, dropdown, etc.)         │   │
│  │  - Label extraction                                          │   │
│  │  - Required field detection (asterisk, color)                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  TIER 2: Validation & Constraints                            │   │
│  │  - Min/max length, email patterns                            │   │
│  │  - Conditional visibility                                    │   │
│  │  - Cross-field validation                                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  TIER 3: Workflow Detection                                  │   │
│  │  - Multi-step wizards                                        │   │
│  │  - State machines (draft→pending→approved)                   │   │
│  │  - Approval chains                                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  TIER 4: Compliance & Audit                                  │   │
│  │  - BIR form patterns (1700, 1601-C, 2550-Q)                  │   │
│  │  - Audit trail fields                                        │   │
│  │  - SoD enforcement                                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  TIER 5: Integration                                         │   │
│  │  - Model relationships (Many2one, One2many)                  │   │
│  │  - API endpoints                                             │   │
│  │  - Supabase schema sync                                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         GENERATED OUTPUT                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ models.py   │  │ views.xml   │  │ tests/      │                 │
│  │ (Odoo ORM)  │  │ (Odoo XML)  │  │ test_*.py   │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ manifest.py │  │ schema.sql  │  │ README.md   │                 │
│  │ (Odoo)      │  │ (Supabase)  │  │             │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Technical Specification

### Plugin Manifest

```json
{
  "name": "Pulser Figma to Odoo",
  "id": "pulser-figma-to-odoo",
  "version": "1.0.0",
  "api": "1.0.0",
  "main": "dist/code.js",
  "ui": "dist/ui.html",
  "capabilities": ["currentPage"],
  "permissions": [
    "currentPage:read",
    "fileKey:read"
  ],
  "networkAccess": {
    "allowedDomains": [
      "*.odoo.com",
      "api.docs2code.dev",
      "api.github.com"
    ],
    "devAllowedDomains": ["*"]
  },
  "editorType": ["figma", "figjam"],
  "documentAccess": "dynamic-page"
}
```

### File Structure

```
pulser-figma-to-odoo/
├── manifest.json
├── package.json
├── tsconfig.json
├── webpack.config.js
├── src/
│   ├── code.ts                 # Main plugin logic (runs in Figma)
│   ├── ui.tsx                  # React UI (modal)
│   ├── types/
│   │   ├── figma.d.ts          # Figma API types
│   │   ├── odoo.d.ts           # Odoo output types
│   │   └── plugin.d.ts         # Plugin state types
│   ├── extractors/
│   │   ├── form.ts             # Form field extraction
│   │   ├── validation.ts       # Validation pattern detection
│   │   ├── workflow.ts         # Workflow/wizard detection
│   │   ├── compliance.ts       # BIR pattern detection
│   │   └── relationships.ts    # Model relationship inference
│   ├── generators/
│   │   ├── odoo-model.ts       # models.py generator
│   │   ├── odoo-view.ts        # views.xml generator
│   │   ├── odoo-manifest.ts    # __manifest__.py generator
│   │   ├── odoo-tests.ts       # test_*.py generator
│   │   └── supabase-schema.ts  # schema.sql generator
│   ├── templates/
│   │   ├── model.py.ejs        # Odoo model template
│   │   ├── view.xml.ejs        # Odoo view template
│   │   ├── test.py.ejs         # Test template
│   │   └── schema.sql.ejs      # Supabase schema template
│   └── utils/
│       ├── naming.ts           # Name conventions
│       ├── heuristics.ts       # Field type detection
│       └── api.ts              # External API calls
├── dist/                       # Compiled output
├── tests/
│   ├── fixtures/               # Test Figma files
│   └── *.test.ts
└── README.md
```

---

## Field Type Detection Algorithm

### Heuristic-Based Detection

```typescript
interface FieldDetection {
  name: string;
  odooType: OdooFieldType;
  supabaseType: string;
  confidence: number;
  validations: Validation[];
}

type OdooFieldType =
  | 'Char'
  | 'Text'
  | 'Integer'
  | 'Float'
  | 'Monetary'
  | 'Date'
  | 'Datetime'
  | 'Boolean'
  | 'Selection'
  | 'Many2one'
  | 'One2many'
  | 'Many2many'
  | 'Binary';

function detectFieldType(node: SceneNode): FieldDetection {
  const label = extractLabel(node);
  const inputType = inferInputType(node);
  const constraints = detectConstraints(node);

  // Priority 1: Explicit input type (from component name or variant)
  if (inputType === 'date' || label.match(/date|fecha|petsa/i)) {
    return { odooType: 'Date', supabaseType: 'DATE', confidence: 0.95 };
  }

  // Priority 2: Label pattern matching
  if (label.match(/email|e-mail|correo/i)) {
    return {
      odooType: 'Char',
      supabaseType: 'TEXT',
      confidence: 0.90,
      validations: [{ type: 'email' }]
    };
  }

  if (label.match(/phone|tel|mobile|celular/i)) {
    return {
      odooType: 'Char',
      supabaseType: 'TEXT',
      confidence: 0.85,
      validations: [{ type: 'phone' }]
    };
  }

  if (label.match(/amount|price|total|subtotal|tax|importe|presyo/i)) {
    return { odooType: 'Monetary', supabaseType: 'DECIMAL(18,2)', confidence: 0.90 };
  }

  if (label.match(/quantity|qty|cantidad|bilang/i)) {
    return { odooType: 'Integer', supabaseType: 'INTEGER', confidence: 0.85 };
  }

  // Priority 3: Component structure
  if (isDropdownComponent(node)) {
    return { odooType: 'Selection', supabaseType: 'TEXT', confidence: 0.95 };
  }

  if (isCheckboxComponent(node)) {
    return { odooType: 'Boolean', supabaseType: 'BOOLEAN', confidence: 0.95 };
  }

  if (isTextareaComponent(node)) {
    return { odooType: 'Text', supabaseType: 'TEXT', confidence: 0.90 };
  }

  // Default: Char field
  return { odooType: 'Char', supabaseType: 'TEXT', confidence: 0.60 };
}
```

### BIR Pattern Detection

```typescript
interface BIRFormPattern {
  formNumber: string;
  formTitle: string;
  fields: BIRField[];
  computationRules: ComputationRule[];
}

const BIR_PATTERNS = {
  '1700': {
    markers: ['taxable income', 'tax due', 'withholding tax', 'annual'],
    requiredFields: ['gross_income', 'deductions', 'tax_credits', 'tax_due'],
    computations: [
      'taxable_income = gross_income - deductions',
      'tax_due = apply_brackets(taxable_income)',
      'net_tax = tax_due - tax_credits - withholding_paid'
    ]
  },
  '1601-C': {
    markers: ['withholding', 'monthly', 'compensation'],
    requiredFields: ['gross_compensation', 'withholding_tax', 'period'],
    computations: [
      'withholding = apply_withholding_table(gross_compensation)'
    ]
  },
  '2550-Q': {
    markers: ['VAT', 'quarterly', 'output tax', 'input tax'],
    requiredFields: ['output_vat', 'input_vat', 'vat_payable'],
    computations: [
      'vat_payable = output_vat - input_vat'
    ]
  }
};

function detectBIRPattern(nodes: SceneNode[]): BIRFormPattern | null {
  const labels = nodes.map(n => extractLabel(n).toLowerCase());
  const fullText = labels.join(' ');

  for (const [formNumber, pattern] of Object.entries(BIR_PATTERNS)) {
    const matches = pattern.markers.filter(m => fullText.includes(m.toLowerCase()));
    if (matches.length >= 2) {
      return {
        formNumber,
        formTitle: `BIR Form ${formNumber}`,
        fields: extractBIRFields(nodes, pattern.requiredFields),
        computationRules: pattern.computations.map(c => parseComputation(c))
      };
    }
  }

  return null;
}
```

---

## Code Generation Templates

### Odoo Model Generator

```python
# templates/model.py.ejs
# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class <%= className %>(models.Model):
    _name = '<%= modelName %>'
    _description = '<%= description %>'
<% if (inherit) { %>
    _inherit = '<%= inherit %>'
<% } %>

    # === FIELDS ===
<% for (const field of fields) { %>
    <%= field.name %> = fields.<%= field.type %>(
        string='<%= field.label %>',
<% if (field.required) { %>
        required=True,
<% } %>
<% if (field.selection) { %>
        selection=[<%= field.selection.map(s => `('${s.value}', '${s.label}')`).join(', ') %>],
<% } %>
<% if (field.relation) { %>
        comodel_name='<%= field.relation %>',
<% } %>
<% if (field.default) { %>
        default=<%= field.default %>,
<% } %>
<% if (field.help) { %>
        help='<%= field.help %>',
<% } %>
    )
<% } %>

<% if (computedFields.length > 0) { %>
    # === COMPUTED FIELDS ===
<% for (const cf of computedFields) { %>
    @api.depends(<%= cf.depends.map(d => `'${d}'`).join(', ') %>)
    def _compute_<%= cf.name %>(self):
        for record in self:
            <%= cf.computation %>
<% } %>
<% } %>

<% if (constraints.length > 0) { %>
    # === CONSTRAINTS ===
<% for (const c of constraints) { %>
    @api.constrains(<%= c.fields.map(f => `'${f}'`).join(', ') %>)
    def _check_<%= c.name %>(self):
        for record in self:
            if <%= c.condition %>:
                raise ValidationError('<%= c.message %>')
<% } %>
<% } %>

<% if (workflow) { %>
    # === WORKFLOW ===
    state = fields.Selection([
<% for (const state of workflow.states) { %>
        ('<%= state.value %>', '<%= state.label %>'),
<% } %>
    ], default='<%= workflow.defaultState %>', tracking=True)

<% for (const transition of workflow.transitions) { %>
    def action_<%= transition.action %>(self):
        self.ensure_one()
        if self.state != '<%= transition.fromState %>':
            raise ValidationError('Invalid state transition')
        self.state = '<%= transition.toState %>'
<% } %>
<% } %>
```

### Odoo View Generator

```xml
<!-- templates/view.xml.ejs -->
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Form View -->
    <record id="<%= viewId %>_form" model="ir.ui.view">
        <field name="name"><%= modelName %>.form</field>
        <field name="model"><%= modelName %></field>
        <field name="arch" type="xml">
            <form string="<%= formTitle %>">
<% if (workflow) { %>
                <header>
                    <field name="state" widget="statusbar" statusbar_visible="<%= workflow.states.map(s => s.value).join(',') %>"/>
<% for (const btn of workflow.buttons) { %>
                    <button name="action_<%= btn.action %>" string="<%= btn.label %>" type="object" class="<%= btn.class %>" attrs="{'invisible': [('state', '!=', '<%= btn.visibleInState %>')]}"/>
<% } %>
                </header>
<% } %>
                <sheet>
<% if (groups.length > 0) { %>
<% for (const group of groups) { %>
                    <group string="<%= group.title %>">
<% for (const field of group.fields) { %>
                        <field name="<%= field.name %>"<% if (field.widget) { %> widget="<%= field.widget %>"<% } %><% if (field.readonly) { %> readonly="1"<% } %>/>
<% } %>
                    </group>
<% } %>
<% } else { %>
                    <group>
<% for (const field of fields) { %>
                        <field name="<%= field.name %>"/>
<% } %>
                    </group>
<% } %>
                </sheet>
<% if (chatter) { %>
                <div class="oe_chatter">
                    <field name="message_follower_ids"/>
                    <field name="message_ids"/>
                </div>
<% } %>
            </form>
        </field>
    </record>

    <!-- Tree View -->
    <record id="<%= viewId %>_tree" model="ir.ui.view">
        <field name="name"><%= modelName %>.tree</field>
        <field name="model"><%= modelName %></field>
        <field name="arch" type="xml">
            <tree string="<%= treeTitle %>">
<% for (const field of listFields) { %>
                <field name="<%= field.name %>"/>
<% } %>
            </tree>
        </field>
    </record>

    <!-- Action -->
    <record id="<%= actionId %>" model="ir.actions.act_window">
        <field name="name"><%= actionTitle %></field>
        <field name="res_model"><%= modelName %></field>
        <field name="view_mode">tree,form</field>
    </record>

    <!-- Menu -->
    <menuitem id="<%= menuId %>" name="<%= menuTitle %>" action="<%= actionId %>" parent="<%= parentMenu %>" sequence="<%= sequence %>"/>
</odoo>
```

---

## Plugin UI Design

### Main Panel

```
┌─────────────────────────────────────────────────────────────────┐
│  🔌 Pulser Figma to Odoo                              [×]       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Selected: Invoice Form (Frame)                                  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📋 DETECTED FIELDS (12)                                │   │
│  │                                                          │   │
│  │  ✓ customer_id      Many2one      (res.partner)         │   │
│  │  ✓ invoice_date     Date          Required              │   │
│  │  ✓ due_date         Date          Required              │   │
│  │  ✓ invoice_lines    One2many      (account.move.line)   │   │
│  │  ✓ amount_untaxed   Monetary      Computed              │   │
│  │  ✓ amount_tax       Monetary      Computed              │   │
│  │  ✓ amount_total     Monetary      Computed              │   │
│  │  ⚠ notes            Text          (low confidence)      │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  🔄 DETECTED WORKFLOW                                    │   │
│  │                                                          │   │
│  │  States: draft → sent → paid → cancelled                │   │
│  │  Buttons: ✓ Send, ✓ Register Payment, ✓ Cancel          │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  🏛️ BIR COMPLIANCE                                       │   │
│  │                                                          │   │
│  │  ⚠ No BIR pattern detected                              │   │
│  │  (Add withholding_tax field for 1601-C support)         │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ⚙️ GENERATION OPTIONS                                   │   │
│  │                                                          │   │
│  │  Module Name: [ipai_custom_invoice          ]            │   │
│  │  Inherit:     [account.move                 ] ☑          │   │
│  │  Generate:    ☑ models.py  ☑ views.xml  ☑ tests          │   │
│  │               ☑ Supabase schema  ☐ README                │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  [  📋 Copy to Clipboard  ]  [  ⬇️ Download ZIP  ]       │   │
│  │  [  🐙 Push to GitHub     ]  [  📤 Export to Docs2Code ] │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Test Cases

### Test Form 1: Simple Contact Form

```
Input: Contact form with name, email, phone, address fields
Expected Output:
- models.py with Char fields, email validation constraint
- views.xml with grouped form layout
- test_contact.py with validation tests
```

### Test Form 2: Invoice with Line Items

```
Input: Invoice form with header + line items table
Expected Output:
- models.py with One2many relationship to line items
- Computed fields for totals (amount_untaxed, amount_tax, amount_total)
- views.xml with notebook tabs and inline tree for lines
```

### Test Form 3: Multi-Step Wizard

```
Input: 3-step onboarding wizard with progress indicator
Expected Output:
- models.py with TransientModel base
- State field with step tracking
- action_next/action_prev methods
- views.xml with page-based layout
```

### Test Form 4: BIR Form 1700

```
Input: Annual income tax return form
Expected Output:
- models.py with all 1700 fields + tax computation
- Compliance constraints (gross_income >= 0, etc.)
- _compute_tax_due method with bracket logic
- Audit trail fields (create_uid, write_date)
```

### Test Form 5: Approval Workflow

```
Input: Purchase request with approval chain
Expected Output:
- models.py with state field (draft, pending, approved, rejected)
- SoD constraint (approver != requester)
- action_submit, action_approve, action_reject methods
- views.xml with statusbar and conditional buttons
```

---

## Implementation Roadmap

### Phase 22 (Weeks 1-4): MVP

**Week 1: Setup**
- [ ] Initialize npm project with TypeScript
- [ ] Configure Webpack for Figma plugin build
- [ ] Set up ESLint + Prettier
- [ ] Create manifest.json

**Week 2: Field Detection**
- [ ] Implement form field extraction (Tier 1)
- [ ] Build label pattern matching
- [ ] Create field type heuristics
- [ ] Test with simple forms

**Week 3: Code Generation**
- [ ] Create EJS templates for Odoo model/view
- [ ] Implement models.py generator
- [ ] Implement views.xml generator
- [ ] Add basic test generation

**Week 4: UI + Export**
- [ ] Build React modal UI
- [ ] Add clipboard export
- [ ] Add ZIP download
- [ ] End-to-end testing with 5 test forms

### Phase 23 (Weeks 5-8): Extended Features

- [ ] Tier 2: Validation detection
- [ ] Tier 3: Workflow/wizard detection
- [ ] Tier 4: BIR pattern detection
- [ ] Supabase schema generation
- [ ] GitHub API integration

### Phase 24 (Weeks 9-12): Production

- [ ] Tier 5: Relationship inference
- [ ] Docs2Code API integration
- [ ] ML-based field detection (fine-tuned model)
- [ ] Team collaboration features
- [ ] Figma Community publishing

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Field Detection Accuracy | ≥ 85% | Test against 50 forms |
| Code Compilation | 100% | All generated Python/XML compiles |
| Test Generation | 100% | Every model gets test file |
| BIR Pattern Detection | ≥ 90% | Test against 10 BIR forms |
| Export Success | 100% | Clipboard/ZIP/GitHub all work |
| User Satisfaction | ≥ 4/5 | Post-pilot survey |

---

## Dependencies

### External APIs

| API | Purpose | Auth |
|-----|---------|------|
| Figma Plugin API | Read design nodes | Built-in |
| GitHub API | Push generated code | OAuth/PAT |
| Docs2Code API | Advanced generation | API key |

### NPM Packages

```json
{
  "dependencies": {
    "@figma/plugin-typings": "^1.95.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "ejs": "^3.1.9"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "webpack": "^5.90.0",
    "webpack-cli": "^5.1.0",
    "@types/react": "^18.2.0",
    "ts-loader": "^9.5.0",
    "css-loader": "^6.10.0",
    "style-loader": "^3.3.0"
  }
}
```

---

## Appendix: Figma Node Type Mapping

| Figma Node Type | Inferred Odoo Type | Confidence |
|-----------------|-------------------|------------|
| TEXT | Char (if short) / Text (if long) | 0.70 |
| RECTANGLE (outlined) | Char input | 0.60 |
| COMPONENT (name: "Input") | Char | 0.85 |
| COMPONENT (name: "Dropdown") | Selection | 0.95 |
| COMPONENT (name: "Checkbox") | Boolean | 0.95 |
| COMPONENT (name: "DatePicker") | Date | 0.95 |
| COMPONENT (name: "TextArea") | Text | 0.90 |
| COMPONENT (name: "FileUpload") | Binary | 0.90 |
| FRAME (contains multiple fields) | Group | 0.80 |
| FRAME (name: "Step 1", "Step 2") | Wizard page | 0.85 |

---

*This specification is ready for implementation. Begin with Phase 22 Week 1 tasks.*

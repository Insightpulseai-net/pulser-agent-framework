# Docs2Code Pipeline Using Google Workspace Add-ons

> **Leveraging existing installed tools instead of custom development**

## Overview

This pipeline uses your already-installed Google Workspace add-ons to create a complete Docs2Code automation system without requiring custom development.

---

## Installed Tools Inventory

| Tool | Status | Pipeline Role |
|------|--------|---------------|
| Docs to Markdown Pro | ✅ Installed | Core: Convert Docs → Markdown → Git |
| GitHub Integration (Gemini) | ✅ Connected | GitHub actions from Gemini Apps |
| Smart Links for Developers | ✅ Installed | Pull GitHub/GitLab/Azure info into Docs |
| Colaboratory | ✅ Installed | Python code generation engine |
| PostgreSQL Connector | ✅ Installed | Schema extraction to Sheets |
| MeisterTask | ✅ Installed | Task management (replaces Planner) |
| DocHub | ✅ Installed | PDF processing for documentation |
| Document Translator | ✅ Installed | Multi-language documentation |

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DOCS2CODE GOOGLE WORKSPACE PIPELINE               │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────────┐    ┌─────────────────────────┐
│ Google Docs  │───▶│ Docs to Markdown │───▶│ GitHub Repository       │
│ (Source)     │    │ Pro              │    │ (Auto-export)           │
└──────────────┘    └──────────────────┘    └─────────────────────────┘
       │                    │                          │
       │                    ▼                          ▼
       │           ┌──────────────────┐    ┌─────────────────────────┐
       │           │ Git Export       │    │ GitHub Actions          │
       │           │ (Built-in)       │    │ (CI/CD triggers)        │
       │           └──────────────────┘    └─────────────────────────┘
       │                                              │
       ▼                                              ▼
┌──────────────┐                          ┌─────────────────────────┐
│ Smart Links  │◀─────────────────────────│ Code Generation         │
│ (Pull info)  │                          │ (Colab notebooks)       │
└──────────────┘                          └─────────────────────────┘
       │                                              │
       ▼                                              ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────────────────┐
│ PostgreSQL   │───▶│ Google Sheets    │───▶│ Schema Documentation    │
│ Connector    │    │ (Data layer)     │    │ (Auto-generated)        │
└──────────────┘    └──────────────────┘    └─────────────────────────┘
       │                                              │
       ▼                                              ▼
┌──────────────┐                          ┌─────────────────────────┐
│ MeisterTask  │◀─────────────────────────│ Task Tracking           │
│ (Project)    │                          │ (Auto-created)          │
└──────────────┘                          └─────────────────────────┘
```

---

## Stage 1: Documentation Source (Google Docs)

### Your Existing Documents (12 Deliverables)

1. Fluent UI Docs - Scout Deployment Guide
2. Azure Foundry Landing Zone - Enterprise Docs Deployment
3. Microsoft Planner Integration
4. BIR Tax Filing & Month-End Close Planner App
5. Docs-to-Code Automation Pipeline
6. Docs2Code: Paper2Code Adapted
7. Month-End Close as Planner UI
8. Enterprise Docs2Code Pipeline
9. Comprehensive Docs2Code Methodology
10. Docs2Code Enterprise Platform PRD
11. Design System Figma-to-Code Integration
12. Docs2Code Figma Plugin Specification

### Document Structure Best Practices

For optimal Markdown conversion, structure documents with:

```
# Title (H1)

## Section (H2)

### Subsection (H3)

**Bold for emphasis**

`code` for inline code

```python
# Code blocks with language hint
def example():
    pass
```

| Column 1 | Column 2 |
|----------|----------|
| Data     | Data     |
```

---

## Stage 2: Docs to Markdown Pro Workflow

### Setup (One-time)

1. Open any Google Doc
2. **Extensions** → **Docs to Markdown Pro** → **Open**
3. Configure Git settings:
   - **Repository**: `Insightpulseai-net/pulser-agent-framework`
   - **Branch**: `claude/system-design-analysis-pVVIl` (or main)
   - **Path**: `docs/` (target directory)
   - **Commit message template**: `docs: sync {filename} from Google Docs`

### Conversion Options

| Option | Recommended Setting |
|--------|---------------------|
| Heading style | ATX (`#` symbols) |
| Code block style | Fenced (```) |
| Table style | GFM (GitHub Flavored Markdown) |
| Image handling | Upload to repository |
| Link handling | Preserve relative links |

### Export Workflow

```
1. Open Google Doc
2. Extensions → Docs to Markdown Pro → Convert
3. Review Markdown preview
4. Click "Export to Git"
5. Select repository and branch
6. Confirm commit
```

### Bulk Conversion

Docs to Markdown Pro supports bulk conversion:

```
1. Extensions → Docs to Markdown Pro → Bulk Convert
2. Select folder with documents
3. Configure output directory
4. Click "Convert All"
5. Export all to Git in single commit
```

---

## Stage 3: Smart Links Integration

### Pull GitHub Info INTO Docs

Smart Links for Developers brings real-time data from:

- **GitHub**: Issues, PRs, commits, releases
- **GitLab**: Same features
- **Azure DevOps**: Work items, repos

### Usage in Documents

Type `@` in Google Docs and select:

```
@github:issue:123          → Embeds issue #123 details
@github:pr:456             → Embeds PR #456 status
@github:commit:abc123      → Embeds commit info
@github:release:v1.0.0     → Embeds release notes
```

### Bi-directional Flow

```
Google Docs                          GitHub
    │                                  │
    │  ┌──────────────────────┐        │
    ├──│ Docs to Markdown Pro │───────▶│ (Docs → Code)
    │  └──────────────────────┘        │
    │                                  │
    │  ┌──────────────────────┐        │
    ◀──│ Smart Links          │────────┤ (Code → Docs)
    │  └──────────────────────┘        │
    │                                  │
```

---

## Stage 4: Colaboratory Code Generation

### Colab Notebook for Docs2Code

Create a Colab notebook that:

1. **Fetches documentation** from Google Docs API
2. **Parses structure** using Python
3. **Generates code** based on templates
4. **Pushes to GitHub** via API

### Example Notebook Structure

```python
# Cell 1: Setup
!pip install google-api-python-client PyGithub

# Cell 2: Authenticate
from google.colab import auth
auth.authenticate_user()

# Cell 3: Fetch Google Doc
from googleapiclient.discovery import build

def fetch_doc(doc_id):
    service = build('docs', 'v1')
    doc = service.documents().get(documentId=doc_id).execute()
    return doc

# Cell 4: Parse Document Structure
def parse_doc_structure(doc):
    """Extract headings, code blocks, tables from doc"""
    content = doc.get('body', {}).get('content', [])
    structure = {
        'title': doc.get('title'),
        'headings': [],
        'code_blocks': [],
        'tables': []
    }
    # Parse content...
    return structure

# Cell 5: Generate Odoo Module
def generate_odoo_module(structure):
    """Generate Odoo module from parsed structure"""
    module_name = structure['title'].lower().replace(' ', '_')

    manifest = f'''{{
    'name': '{structure["title"]}',
    'version': '18.0.1.0.0',
    'category': 'Uncategorized',
    'summary': 'Auto-generated from Google Docs',
    'depends': ['base'],
    'data': [],
    'installable': True,
    'application': False,
}}'''

    return {
        '__manifest__.py': manifest,
        '__init__.py': '# Auto-generated',
        'models/__init__.py': '',
        'views/.gitkeep': '',
    }

# Cell 6: Push to GitHub
from github import Github

def push_to_github(files, repo_name, branch, path_prefix):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(repo_name)

    for filename, content in files.items():
        file_path = f"{path_prefix}/{filename}"
        try:
            # Update existing file
            contents = repo.get_contents(file_path, ref=branch)
            repo.update_file(file_path, f"docs: update {filename}",
                           content, contents.sha, branch=branch)
        except:
            # Create new file
            repo.create_file(file_path, f"docs: add {filename}",
                           content, branch=branch)
```

### Colab → GitHub Integration

```
┌─────────────────┐    ┌──────────────────┐    ┌───────────────┐
│ Google Docs     │───▶│ Colab Notebook   │───▶│ GitHub Repo   │
│ (Documentation) │    │ (Code Generator) │    │ (Source Code) │
└─────────────────┘    └──────────────────┘    └───────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Generated Files  │
                    ├──────────────────┤
                    │ __manifest__.py  │
                    │ models/*.py      │
                    │ views/*.xml      │
                    │ tests/*.py       │
                    │ README.md        │
                    └──────────────────┘
```

---

## Stage 5: PostgreSQL Schema Extraction

### Database Connector Setup

1. Open Google Sheets
2. **Extensions** → **SyncWith** → **Connect**
3. Add PostgreSQL connection:
   - **Host**: Your Supabase/DigitalOcean PostgreSQL
   - **Port**: 5432
   - **Database**: odoo_prod
   - **User**: readonly_user
   - **Password**: (from secrets)

### Schema Extraction Query

```sql
-- Extract table schemas
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;
```

### Auto-Sync to Sheets

```
PostgreSQL → Google Sheets → Google Docs → Markdown → GitHub

Schedule: Every hour (or on-demand)
```

### Schema Documentation Flow

```
┌─────────────┐    ┌───────────────┐    ┌──────────────┐
│ PostgreSQL  │───▶│ Google Sheets │───▶│ Google Docs  │
│ (Live DB)   │    │ (Schema data) │    │ (Schema doc) │
└─────────────┘    └───────────────┘    └──────────────┘
                          │                     │
                          ▼                     ▼
               ┌───────────────────┐   ┌──────────────┐
               │ Charts & Analysis │   │ Markdown     │
               │ (Auto-generated)  │   │ (Git export) │
               └───────────────────┘   └──────────────┘
```

---

## Stage 6: MeisterTask Integration

### Replace Microsoft Planner

MeisterTask provides:
- Kanban boards
- Task dependencies
- Time tracking
- Integrations (Gmail, Slack/Mattermost)

### Project Structure for Docs2Code

```
MeisterTask Project: "Docs2Code Pipeline"
├── Section: Backlog
│   ├── Task: Add new documentation source
│   └── Task: Schema update request
├── Section: In Progress
│   ├── Task: Converting BIR Tax Filing doc
│   └── Task: Generating Odoo module
├── Section: Review
│   ├── Task: PR #123 awaiting review
│   └── Task: Code validation pending
├── Section: Done
│   ├── Task: Fluent UI docs synced
│   └── Task: Azure Landing Zone deployed
└── Section: Blocked
    └── Task: Waiting for compliance approval
```

### Gmail → MeisterTask Flow

With **MeisterTask for Gmail**:

```
1. Receive email about documentation update
2. Click MeisterTask icon in Gmail
3. Create task automatically:
   - Title: Email subject
   - Description: Email body
   - Attachments: Email attachments
   - Due date: Extracted from email
4. Task appears in Docs2Code project
```

---

## Complete Pipeline Workflow

### Step-by-Step Execution

```
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: Create/Update Documentation in Google Docs                  │
│ - Use structured headings (H1, H2, H3)                              │
│ - Include code blocks with language hints                           │
│ - Add tables for data models                                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: Export to GitHub via Docs to Markdown Pro                   │
│ - Extensions → Docs to Markdown Pro → Convert                       │
│ - Review Markdown preview                                           │
│ - Export to Git (select repo/branch/path)                           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: GitHub Actions Trigger                                      │
│ - Workflow detects new/updated Markdown                             │
│ - Runs validation (lint, links, format)                             │
│ - Triggers code generation if template detected                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: Colab Code Generation (if applicable)                       │
│ - Parse documentation structure                                     │
│ - Generate Odoo/FastAPI/React code                                  │
│ - Create tests and CI configuration                                 │
│ - Push generated code to repository                                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 5: Pull Request & Review                                       │
│ - Auto-create PR with generated code                                │
│ - Smart Links shows PR status in source Doc                         │
│ - MeisterTask tracks review progress                                │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 6: Merge & Deploy                                              │
│ - Approve and merge PR                                              │
│ - GitHub Actions deploys to staging/production                      │
│ - MeisterTask marks task complete                                   │
│ - Smart Links updates Doc with deployment status                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Configuration Files

### GitHub Actions: docs-to-code.yml

```yaml
name: Docs to Code Pipeline

on:
  push:
    paths:
      - 'docs/**/*.md'
  workflow_dispatch:

jobs:
  detect-templates:
    runs-on: ubuntu-latest
    outputs:
      has_templates: ${{ steps.check.outputs.has_templates }}
    steps:
      - uses: actions/checkout@v4

      - name: Check for code templates
        id: check
        run: |
          if grep -rq "```python" docs/ || grep -rq "```javascript" docs/; then
            echo "has_templates=true" >> $GITHUB_OUTPUT
          else
            echo "has_templates=false" >> $GITHUB_OUTPUT
          fi

  generate-code:
    needs: detect-templates
    if: needs.detect-templates.outputs.has_templates == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install PyGithub markdown

      - name: Generate code from docs
        run: python scripts/docs2code/generate.py

      - name: Create PR with generated code
        uses: peter-evans/create-pull-request@v6
        with:
          commit-message: 'feat: auto-generate code from documentation'
          title: '[Docs2Code] Generated code from documentation update'
          body: |
            This PR contains auto-generated code from documentation changes.

            ## Changes
            - Generated from documentation templates
            - Includes model definitions, views, and tests

            ## Review Checklist
            - [ ] Code follows Odoo 18 CE conventions
            - [ ] Tests pass locally
            - [ ] No hardcoded credentials
          branch: docs2code/auto-${{ github.run_number }}
```

---

## Benefits of This Approach

### Why Existing Tools > Custom Development

| Aspect | Custom Development | Existing Tools |
|--------|-------------------|----------------|
| Time to deploy | 4-8 weeks | 1-2 days |
| Maintenance | You maintain | Vendor maintains |
| Cost | Development + hosting | Already paid/free |
| Reliability | Needs testing | Battle-tested |
| Updates | You build | Auto-updated |
| Support | DIY | Vendor support |

### Cost Comparison

| Approach | Cost/Month |
|----------|------------|
| Custom n8n + APIs | ~$50-100 |
| Google Workspace add-ons | $0 (already installed) |
| Savings | 100% |

---

## Next Steps

1. **Configure Docs to Markdown Pro** for Git export
2. **Create Colab notebook** for code generation
3. **Set up PostgreSQL Connector** for schema sync
4. **Configure MeisterTask** project structure
5. **Test end-to-end pipeline** with one document

---

## References

- [Docs to Markdown Pro](https://workspace.google.com/marketplace/app/docs_to_markdown_pro/483386994804)
- [Smart Links for Developers](https://workspace.google.com/marketplace/app/smart_links_for_developers/158828424828)
- [Google Colab](https://colab.research.google.com/)
- [SyncWith PostgreSQL Connector](https://workspace.google.com/marketplace/app/syncwith/449644239211)
- [MeisterTask](https://www.meistertask.com/)

---

*Generated from InsightPulseAI Docs2Code Pipeline*
*Last Updated: 2025-12-30*

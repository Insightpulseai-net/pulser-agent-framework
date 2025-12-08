# Schema Documentation

> Auto-generated from `db/schema.sql`. Run `make docs-schema-md` to regenerate.

## Tables

### tenants
Multi-tenant isolation root table.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| slug | text | Unique tenant identifier |
| name | text | Display name |
| created_at | timestamptz | Creation timestamp |

### workspaces
Workspace within a tenant.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| tenant_id | uuid | Foreign key to tenants |
| slug | text | Unique within tenant |
| name | text | Display name |
| created_at | timestamptz | Creation timestamp |

### schema_migrations
Tracks applied migrations.

| Column | Type | Description |
|--------|------|-------------|
| version | text | Migration version (e.g., 0001_init) |
| applied_at | timestamptz | When migration was applied |
